"""
Celery tasks for scraper integration
"""
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import requests
import logging

from api.models import State, County, TaxData, ScraperLog

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def scrape_county_data(self, state_code: str, county_name: str):
    """
    Trigger scraping for a specific county

    This calls the scraper service API
    """
    try:
        logger.info(f"Starting scrape task for {county_name}, {state_code}")

        # Get state and county objects
        state = State.objects.get(code=state_code.upper())
        county = County.objects.get(state=state, name=county_name)

        # Create scraper log
        scraper_log = ScraperLog.objects.create(
            state=state,
            county=county,
            status='in_progress',
            trigger_type='scheduled',
            llm_provider=settings.LLM_PROVIDER
        )

        # Call scraper service
        scraper_url = f"{settings.SCRAPER_SERVICE_URL}/scrape"

        response = requests.post(
            scraper_url,
            json={
                "state": state_code,
                "county": county_name,
                "force_refresh": True
            },
            timeout=settings.SCRAPER_TIMEOUT
        )

        response.raise_for_status()
        result = response.json()

        if result.get('success'):
            # Update scraper log with success
            scraper_log.status = 'success'
            scraper_log.completed_at = timezone.now()
            scraper_log.data_completeness = result.get('data', {}).get('data_completeness', 0)
            scraper_log.confidence_score = result.get('data', {}).get('scraper_confidence', 0)
            scraper_log.sources_found = len(result.get('data', {}).get('sources', []))
            scraper_log.save()

            logger.info(f"Scrape successful for {county_name}, {state_code}")
        else:
            # Update scraper log with failure
            scraper_log.status = 'failed'
            scraper_log.completed_at = timezone.now()
            scraper_log.error_message = result.get('error', 'Unknown error')
            scraper_log.save()

            logger.error(f"Scrape failed for {county_name}, {state_code}: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"Scrape task failed: {str(e)}", exc_info=True)

        # Update scraper log if it exists
        try:
            scraper_log.status = 'failed'
            scraper_log.completed_at = timezone.now()
            scraper_log.error_message = str(e)
            scraper_log.retry_count = self.request.retries
            scraper_log.save()
        except:
            pass

        # Retry task
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        raise


@shared_task
def check_stale_tax_data():
    """
    Periodic task to check for stale tax data and trigger re-scraping

    Runs daily via Celery Beat
    """
    logger.info("Checking for stale tax data")

    expiry_date = timezone.now() - timedelta(days=settings.SCRAPER_CACHE_EXPIRY_DAYS)

    # Find all current tax data that is stale
    stale_data = TaxData.objects.filter(
        is_current=True,
        last_verified__lt=expiry_date
    ).select_related('state', 'county')

    logger.info(f"Found {stale_data.count()} stale tax data records")

    # Trigger re-scraping for stale data
    for tax_data in stale_data:
        logger.info(f"Triggering re-scrape for {tax_data.county.name}, {tax_data.state.code}")
        scrape_county_data.delay(
            tax_data.state.code,
            tax_data.county.name
        )

    return {
        'checked_at': timezone.now().isoformat(),
        'stale_count': stale_data.count()
    }


@shared_task
def bulk_scrape_states(state_codes: list):
    """
    Bulk scrape all counties in specified states

    Args:
        state_codes: List of 2-letter state codes
    """
    logger.info(f"Starting bulk scrape for states: {state_codes}")

    total_counties = 0

    for state_code in state_codes:
        try:
            state = State.objects.get(code=state_code.upper())
            counties = state.counties.filter(active=True)

            logger.info(f"Scraping {counties.count()} counties in {state.name}")

            for county in counties:
                # Queue scraping task
                scrape_county_data.delay(state.code, county.name)
                total_counties += 1

        except State.DoesNotExist:
            logger.error(f"State {state_code} not found")
            continue

    return {
        'started_at': timezone.now().isoformat(),
        'states': state_codes,
        'total_counties_queued': total_counties
    }


@shared_task
def scrape_all_jurisdictions():
    """
    Scrape all active counties in all states

    Use with caution - this will trigger thousands of scraping tasks
    """
    logger.info("Starting full jurisdiction scrape")

    states = State.objects.filter(active=True)
    state_codes = [s.code for s in states]

    return bulk_scrape_states.delay(state_codes)
