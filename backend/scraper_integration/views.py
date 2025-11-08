"""
Scraper Integration Views
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from api.models import State, County
from .tasks import scrape_county_data, bulk_scrape_states, check_stale_tax_data


@api_view(['POST'])
@permission_classes([IsAdminUser])
def trigger_scrape(request, state_code, county_name):
    """
    Manually trigger scraping for a jurisdiction

    POST /api/scraper/trigger/{state_code}/{county_name}/
    """
    try:
        # Validate state and county
        state = State.objects.get(code=state_code.upper(), active=True)
        county = County.objects.get(state=state, name=county_name, active=True)

        # Trigger async task
        task = scrape_county_data.delay(state.code, county.name)

        return Response({
            'message': f'Scraping triggered for {county.name}, {state.code}',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)

    except (State.DoesNotExist, County.DoesNotExist):
        return Response({
            'error': 'State or county not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_scrape_state(request, state_code):
    """
    Trigger scraping for all counties in a state

    POST /api/scraper/bulk/state/{state_code}/
    """
    try:
        state = State.objects.get(code=state_code.upper(), active=True)
        counties_count = state.counties.filter(active=True).count()

        # Trigger bulk task
        task = bulk_scrape_states.delay([state.code])

        return Response({
            'message': f'Bulk scraping triggered for {state.name}',
            'counties_count': counties_count,
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)

    except State.DoesNotExist:
        return Response({
            'error': 'State not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def check_stale(request):
    """
    Check for stale data and trigger re-scraping

    POST /api/scraper/check-stale/
    """
    task = check_stale_tax_data.delay()

    return Response({
        'message': 'Stale data check triggered',
        'task_id': task.id
    }, status=status.HTTP_202_ACCEPTED)
