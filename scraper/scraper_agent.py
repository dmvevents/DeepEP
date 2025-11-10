"""
LLM-Powered Web Scraper Agent

Uses LLMs with web search to intelligently find and extract mortgage tax data
from official government sources.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio

from llm_client import LLMClient
from web_search import WebSearchClient
from database import DatabaseClient
from config import settings

logger = logging.getLogger(__name__)


class ScraperAgent:
    """
    Main scraper agent that orchestrates the scraping process
    """

    def __init__(self):
        self.llm_client = LLMClient()
        self.search_client = WebSearchClient()
        self.db_client = DatabaseClient()

    async def scrape(self, state: str, county: str) -> Dict[str, Any]:
        """
        Main scraping method

        Args:
            state: Two-letter state code
            county: County name

        Returns:
            Dict containing all scraped tax data
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting scrape for {county}, {state}")

        try:
            # Step 1: Search for official sources
            sources = await self._find_official_sources(state, county)

            if not sources:
                raise ValueError(f"No official sources found for {county}, {state}")

            # Step 2: Extract tax data using LLM
            tax_data = await self._extract_tax_data(state, county, sources)

            # Step 3: Validate and enrich data
            tax_data = await self._validate_and_enrich(tax_data, state, county)

            # Step 4: Calculate metadata
            tax_data['last_verified'] = datetime.utcnow().isoformat()
            tax_data['processing_time'] = (datetime.utcnow() - start_time).total_seconds()

            # Step 5: Save to database
            await self.db_client.save_tax_data(state, county, tax_data)

            logger.info(f"Scrape completed for {county}, {state} in {tax_data['processing_time']:.2f}s")

            return tax_data

        except Exception as e:
            logger.error(f"Scrape failed for {county}, {state}: {str(e)}", exc_info=True)
            raise

    async def _find_official_sources(self, state: str, county: str) -> List[Dict[str, str]]:
        """
        Find official government sources for tax data

        Uses web search with LLM-guided query construction
        """
        logger.info(f"Finding sources for {county}, {state}")

        # Construct search queries
        queries = [
            f"{county} County {state} property tax rate 2025",
            f"{county} {state} transfer tax rate",
            f"{county} {state} recording fees",
            f"{state} recordation tax",
            f"{county} County treasurer {state}"
        ]

        all_sources = []

        for query in queries:
            try:
                results = await self.search_client.search(query)

                # Filter for official sources
                official_results = [
                    r for r in results
                    if self._is_official_source(r['url'])
                ]

                all_sources.extend(official_results)

            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {str(e)}")

        # Deduplicate and prioritize
        unique_sources = self._deduplicate_sources(all_sources)

        logger.info(f"Found {len(unique_sources)} official sources")

        return unique_sources

    def _is_official_source(self, url: str) -> bool:
        """Check if URL is from an official government source"""
        url_lower = url.lower()

        # Check against official patterns
        for pattern in settings.OFFICIAL_SOURCE_PATTERNS:
            if pattern in url_lower:
                # Check against blacklist
                for blacklist in settings.BLACKLIST_PATTERNS:
                    if blacklist in url_lower:
                        return False
                return True

        return False

    def _deduplicate_sources(self, sources: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Deduplicate and prioritize sources"""
        seen_urls = set()
        unique = []

        # Prioritize .gov domains
        sources_sorted = sorted(
            sources,
            key=lambda x: (
                0 if '.gov' in x['url'] else 1 if '.us' in x['url'] else 2
            )
        )

        for source in sources_sorted:
            if source['url'] not in seen_urls:
                seen_urls.add(source['url'])
                unique.append(source)

        return unique[:10]  # Limit to top 10 sources

    async def _extract_tax_data(
        self,
        state: str,
        county: str,
        sources: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Extract structured tax data using LLM

        The LLM analyzes search results and extracts relevant data
        """
        logger.info(f"Extracting tax data for {county}, {state}")

        # Build extraction prompt
        prompt = self._build_extraction_prompt(state, county, sources)

        # Call LLM with reasoning loop
        max_loops = settings.MAX_REASONING_LOOPS
        for attempt in range(max_loops):
            try:
                logger.debug(f"Extraction attempt {attempt + 1}/{max_loops}")

                response = await self.llm_client.extract_structured_data(prompt)

                # Parse JSON response
                tax_data = json.loads(response)

                # Validate completeness
                completeness = self._calculate_completeness(tax_data)

                if completeness >= settings.MIN_COMPLETENESS_SCORE:
                    logger.info(f"Extraction successful with {completeness}% completeness")
                    tax_data['data_completeness'] = completeness
                    return tax_data

                logger.warning(f"Completeness too low ({completeness}%), retrying...")

                # Ask LLM to fill in missing data
                prompt = self._build_refinement_prompt(tax_data, sources)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response: {str(e)}")
                if attempt == max_loops - 1:
                    raise ValueError("LLM failed to return valid JSON after multiple attempts")

        # If we get here, return what we have
        logger.warning(f"Returning incomplete data after {max_loops} attempts")
        tax_data['data_completeness'] = self._calculate_completeness(tax_data)
        return tax_data

    def _build_extraction_prompt(
        self,
        state: str,
        county: str,
        sources: List[Dict[str, str]]
    ) -> str:
        """Build the LLM extraction prompt with best practices"""

        sources_text = "\n\n".join([
            f"Source {i+1}: {s['title']}\nURL: {s['url']}\nSnippet: {s.get('snippet', 'N/A')}"
            for i, s in enumerate(sources)
        ])

        prompt = f"""You are an expert web scraper and data extraction specialist for US mortgage and real estate tax regulations. Your role is to analyze official government sources and extract accurate, structured data for mortgage calculations.

# TASK OVERVIEW
Extract comprehensive tax and fee data for mortgage calculations in:
- STATE: {state}
- COUNTY: {county}

# SOURCE MATERIALS
{sources_text}

# EXTRACTION METHODOLOGY

Follow this step-by-step reasoning process:

## Step 1: Source Assessment
First, evaluate each source for relevance and authority:
- Identify which sources are official (.gov, .us domains)
- Note the publication/last updated dates
- Determine which sources cover which topics (property tax, transfer tax, fees)
- Flag any sources that may be outdated or unofficial

## Step 2: Property Tax Extraction
For property taxes, systematically extract:

a) **Total Tax Rate**: Look for phrases like:
   - "Total tax rate is X mills" (convert mills to decimal: mills/1000)
   - "Combined tax rate of X%"
   - "Effective tax rate"

b) **Rate Components**: Break down by jurisdiction:
   - County portion
   - State portion (if applicable)
   - Municipality/city portion
   - School district portion
   - Special districts (fire, water, etc.)

c) **Assessment Practices**:
   - Assessment ratio (e.g., "assessed at 100% of market value" or "60% assessment ratio")
   - Reassessment cycle (annual, triennial, etc.)
   - Appeal procedures

d) **Exemptions & Caps**:
   - Homestead exemption amount and eligibility
   - Senior/veteran/disability exemptions
   - Assessment increase caps (e.g., "increases limited to 3% annually")

e) **Billing Schedule**:
   - When tax bills are issued (e.g., "July 1st and January 1st")
   - Payment due dates
   - Installment options

## Step 3: Transfer Tax Extraction
Extract transaction taxes at closing:

a) **State Transfer Tax**:
   - Base rate (e.g., "$5 per $1,000 of sale price" = 0.005)
   - Any tiered rates by property value
   - Exemptions (first-time buyers, affordable housing, etc.)

b) **County Transfer Tax**:
   - County-specific rate
   - Local municipality add-ons
   - Who typically pays (buyer/seller/split)

c) **Special Provisions**:
   - First-time homebuyer programs
   - Agricultural/conservation exemptions
   - Threshold amounts

## Step 4: Recordation Tax & Fees
Extract recording costs:

a) **Recordation Tax** (if applicable in state):
   - Base rate structure
   - Tiered rates (e.g., "0.35% on first $500k, 0.5% thereafter")
   - Surcharges or add-ons

b) **Recording Fees**:
   - Deed recording: flat fee + per-page charges
   - Mortgage recording: flat fee + per-page charges
   - Additional surcharges (technology fund, land records, etc.)
   - Number of pages typically required

## Step 5: Insurance Estimates
Extract typical insurance costs:
- Average homeowners insurance premium by property value
- Regional factors (coastal, urban, rural adjustments)
- Typical coverage amounts

## Step 6: Confidence Assessment
For each data point extracted, assess confidence:
- 90-100%: Found explicit data in official source with recent date
- 70-89%: Found data in official source but may be 1-2 years old
- 50-69%: Inferred from related information or regional averages
- Below 50%: Estimated based on state/national averages

# FEW-SHOT EXAMPLES

## Example 1: Montgomery County, Maryland
```json
{{
  "state": "MD",
  "county": "Montgomery",
  "effective_date": "2024-07-01",
  "data_completeness": 95,
  "property_tax": {{
    "total_rate": 0.011234,
    "total_rate_source": "Source 2 - Montgomery County Tax Office 2024 rates",
    "total_rate_confidence": 95,
    "assessment_ratio": 100,
    "assessment_ratio_source": "Source 2",
    "assessment_ratio_confidence": 100,
    "components": {{
      "county": 0.00643,
      "state": 0.00112,
      "municipality": 0.0,
      "school": 0.00368
    }},
    "components_source": "Source 2 - Itemized tax rate breakdown table",
    "components_confidence": 95,
    "homestead_cap": "Annual assessment increase capped at 10% for owner-occupied primary residences",
    "homestead_cap_source": "Source 3",
    "reassessment_cycle": "Triennial - properties reassessed every 3 years",
    "billing_schedule": {{
      "first_half_due": "September 30",
      "second_half_due": "December 31"
    }}
  }},
  "transfer_tax": {{
    "state_rate": 0.005,
    "state_rate_source": "Source 1 - MD State Department of Assessments",
    "state_rate_confidence": 100,
    "county_rate": 0.01,
    "county_rate_source": "Source 2",
    "county_rate_confidence": 95,
    "first_time_buyer_threshold": 450000,
    "first_time_buyer_exemption": "First-time buyers purchasing under $450k exempt from state transfer tax",
    "buyer_seller_split": "Buyer pays county transfer tax, seller pays state transfer tax by local custom"
  }},
  "recordation_tax": {{
    "tiers": [
      {{"max_value": 500000, "rate": 0.0035}},
      {{"min_value": 500000, "rate": 0.005}}
    ],
    "tiers_source": "Source 3 - MD Comptroller office",
    "tiers_confidence": 100
  }},
  "recording_fees": {{
    "deed": {{"flat": 50, "per_page": 5, "typical_pages": 3}},
    "mortgage": {{"flat": 80, "per_page": 5, "typical_pages": 8}},
    "surcharge": 20,
    "surcharge_description": "Technology surcharge for electronic filing system",
    "recording_fees_source": "Source 4 - County Clerk fee schedule",
    "recording_fees_confidence": 90
  }},
  "insurance_estimate": {{
    "base_premium_per_100k": 650,
    "insurance_source": "Regional average from Source 5",
    "insurance_confidence": 70
  }},
  "sources_used": [
    "https://msa.maryland.gov/...",
    "https://www.montgomerycountymd.gov/...",
    "..."
  ],
  "notes": "Transfer tax split is customary but can be negotiated. Recordation tax applies to both deed and mortgage. First-time buyer exemption requires state certification.",
  "scraper_confidence": 92,
  "field_confidence_breakdown": {{
    "property_tax_rate": 95,
    "transfer_tax": 98,
    "recordation_tax": 100,
    "recording_fees": 90,
    "insurance": 70
  }}
}}
```

# OUTPUT SCHEMA

Return ONLY valid JSON matching this exact schema:
{{
  "state": "{state}",
  "county": "{county}",
  "effective_date": "YYYY-MM-DD",
  "data_completeness": 0-100,

  "property_tax": {{
    "total_rate": 0.0,
    "total_rate_source": "Which source and where",
    "total_rate_confidence": 0-100,
    "assessment_ratio": 100,
    "assessment_ratio_source": "Which source",
    "assessment_ratio_confidence": 0-100,
    "components": {{
      "county": 0.0,
      "state": 0.0,
      "municipality": 0.0,
      "school": 0.0
    }},
    "components_source": "Which source",
    "components_confidence": 0-100,
    "homestead_cap": "description",
    "homestead_cap_source": "Which source or 'Not found'",
    "reassessment_cycle": "description",
    "billing_schedule": {{
      "first_half_due": "date or N/A",
      "second_half_due": "date or N/A"
    }}
  }},

  "transfer_tax": {{
    "state_rate": 0.0,
    "state_rate_source": "Which source",
    "state_rate_confidence": 0-100,
    "county_rate": 0.0,
    "county_rate_source": "Which source",
    "county_rate_confidence": 0-100,
    "first_time_buyer_threshold": 0,
    "first_time_buyer_exemption": "description or 'None found'",
    "buyer_seller_split": "description"
  }},

  "recordation_tax": {{
    "tiers": [
      {{"max_value": 500000, "rate": 0.0035}},
      {{"min_value": 500000, "rate": 0.005}}
    ],
    "tiers_source": "Which source or 'Not applicable'",
    "tiers_confidence": 0-100,
    "notes": "State-specific details"
  }},

  "recording_fees": {{
    "deed": {{"flat": 50, "per_page": 5, "typical_pages": 3}},
    "mortgage": {{"flat": 80, "per_page": 5, "typical_pages": 8}},
    "surcharge": 20,
    "surcharge_description": "description",
    "recording_fees_source": "Which source",
    "recording_fees_confidence": 0-100
  }},

  "insurance_estimate": {{
    "base_premium_per_100k": 650,
    "insurance_source": "Which source or 'Estimated'",
    "insurance_confidence": 0-100
  }},

  "sources_used": ["URL1", "URL2", "..."],
  "notes": "Important caveats, effective dates, special conditions, or gaps in data",
  "scraper_confidence": 0-100,
  "field_confidence_breakdown": {{
    "property_tax_rate": 0-100,
    "transfer_tax": 0-100,
    "recordation_tax": 0-100,
    "recording_fees": 0-100,
    "insurance": 0-100
  }}
}}

# CRITICAL INSTRUCTIONS

1. **Rate Formats**: ALWAYS convert to decimal format:
   - "1.5%" → 0.015
   - "15 mills" → 0.015
   - "$5 per $1,000" → 0.005

2. **Source Attribution**: For EVERY major data point, cite:
   - Which source number it came from
   - Specific section/table if available
   - Confidence level (0-100)

3. **Missing Data Handling**:
   - If data not found: use null or "Not found"
   - If estimated: clearly label as "Estimated from [basis]"
   - If outdated: note year and mark confidence <70
   - NEVER make up official-sounding data

4. **Date Sensitivity**:
   - Prioritize 2024-2025 data
   - If using 2023 data, note it and reduce confidence
   - Mark effective dates clearly

5. **Validation Checks**:
   - Property tax rates typically 0.005-0.035 (0.5%-3.5%)
   - Transfer tax rates typically 0.001-0.02 (0.1%-2%)
   - Recording fees typically $20-$200 per document

6. **Completeness**:
   - Set data_completeness based on fields found vs required
   - Set scraper_confidence based on source quality and data recency
   - Provide field-level confidence for granular assessment

Now, carefully analyze the provided sources step-by-step and extract all available data following the methodology above. Return ONLY the JSON output, no other text."""

        return prompt

    def _build_refinement_prompt(
        self,
        incomplete_data: Dict[str, Any],
        sources: List[Dict[str, str]]
    ) -> str:
        """Build prompt to refine incomplete data with targeted guidance"""

        missing_fields = self._identify_missing_fields(incomplete_data)
        completeness = self._calculate_completeness(incomplete_data)

        sources_text = "\n".join([
            f"- Source {i+1}: {s['title']} - {s['url']}"
            for i, s in enumerate(sources)
        ])

        return f"""# DATA REFINEMENT TASK

Your previous extraction achieved {completeness}% completeness but is missing critical fields. Please perform a MORE THOROUGH analysis of the sources to fill in the gaps.

## AVAILABLE SOURCES
{sources_text}

## CURRENT DATA (Incomplete - {completeness}% complete)
```json
{json.dumps(incomplete_data, indent=2)}
```

## MISSING OR INCOMPLETE FIELDS
{missing_fields}

## REFINEMENT STRATEGY

For each missing field, follow this approach:

### 1. Property Tax Data (if missing)
- Re-examine county treasurer/assessor websites in the sources
- Look for "tax rates", "mill levies", "assessment schedules"
- Check for PDF rate sheets or tax rate tables
- If not in snippets, infer from related information (e.g., if you see total revenue and property values, calculate rate)
- As last resort, use state/regional averages and mark confidence < 50

### 2. Transfer Tax Rates (if missing)
- Check state revenue department sites
- Look for "real estate transfer tax", "documentary stamps", "deed stamps"
- County clerk or recorder of deeds may have local rates
- Some states have no transfer tax - verify and explicitly state this
- Mark confidence based on source recency

### 3. Recording Fees (if missing)
- County clerk or recorder of deeds fee schedules
- Look for "recording fees", "document filing fees"
- Often found in PDF fee schedules
- Fees change infrequently, so 2023 data is acceptable (mark confidence 80)

### 4. Insurance Estimates (if missing)
- Use regional averages if no local data
- Coastal areas: higher rates ($800-1200 per $100k)
- Inland areas: moderate rates ($500-800 per $100k)
- Mark as "Estimated from regional averages" with confidence 60

## CONFIDENCE SCORING FOR ESTIMATES

When you must estimate (data truly not available):
- State the estimation basis clearly
- Use conservative ranges
- Mark confidence appropriately:
  - 80-90: Based on adjacent county data
  - 60-79: Based on state average
  - 40-59: Based on regional/national average
  - <40: Pure estimate (avoid if possible)

## OUTPUT REQUIREMENTS

1. Return the COMPLETE JSON with ALL fields filled
2. For every filled field, add or update the "_source" and "_confidence" annotations
3. Update the "notes" field with:
   - Which fields were estimated
   - Basis for estimates
   - Any data quality concerns
4. Update "data_completeness" to reflect actual completeness
5. Update "scraper_confidence" to reflect overall data quality

## EXAMPLE OF GOOD ESTIMATION

If transfer tax data is not found:
```json
"transfer_tax": {{
  "state_rate": 0.005,
  "state_rate_source": "Estimated from neighboring county averages in [state]",
  "state_rate_confidence": 65,
  "county_rate": 0.0,
  "county_rate_source": "No county transfer tax found in sources; verified against county clerk site",
  "county_rate_confidence": 85,
  ...
}}
```

Now, return the COMPLETE, REFINED JSON with all fields filled following the guidance above. Be thorough but honest about data quality."""

    def _calculate_completeness(self, data: Dict[str, Any]) -> int:
        """Calculate data completeness score (0-100)"""

        required_fields = [
            ('property_tax', 'total_rate'),
            ('property_tax', 'assessment_ratio'),
            ('transfer_tax', 'state_rate'),
            ('transfer_tax', 'county_rate'),
            ('recordation_tax', 'tiers'),
            ('recording_fees', 'deed'),
            ('recording_fees', 'mortgage'),
            ('insurance_estimate', 'base_premium_per_100k'),
        ]

        found = 0
        for field_path in required_fields:
            if len(field_path) == 1:
                if field_path[0] in data and data[field_path[0]]:
                    found += 1
            elif len(field_path) == 2:
                if (field_path[0] in data and
                    field_path[1] in data[field_path[0]] and
                    data[field_path[0]][field_path[1]]):
                    found += 1

        completeness = int((found / len(required_fields)) * 100)
        return completeness

    def _identify_missing_fields(self, data: Dict[str, Any]) -> str:
        """Identify which fields are missing or incomplete"""

        missing = []

        if 'property_tax' not in data or not data['property_tax'].get('total_rate'):
            missing.append("- Property tax total rate")

        if 'transfer_tax' not in data or not data['transfer_tax'].get('state_rate'):
            missing.append("- State transfer tax rate")

        if 'recording_fees' not in data:
            missing.append("- Recording fees")

        if not missing:
            return "All major fields present, but may need more detail"

        return "\n".join(missing)

    async def _validate_and_enrich(
        self,
        tax_data: Dict[str, Any],
        state: str,
        county: str
    ) -> Dict[str, Any]:
        """
        Validate extracted data and enrich with additional info
        """
        logger.info(f"Validating data for {county}, {state}")

        # Ensure required fields exist
        if 'state' not in tax_data:
            tax_data['state'] = state

        if 'county' not in tax_data:
            tax_data['county'] = county

        if 'effective_date' not in tax_data:
            tax_data['effective_date'] = datetime.utcnow().strftime('%Y-%m-%d')

        # Set default confidence if not provided
        if 'scraper_confidence' not in tax_data:
            tax_data['scraper_confidence'] = 70

        # Validate numeric values
        self._validate_numeric_values(tax_data)

        return tax_data

    def _validate_numeric_values(self, data: Dict[str, Any]):
        """Ensure all numeric values are reasonable"""

        # Property tax rate should be between 0.001 and 0.05 (0.1% to 5%)
        if 'property_tax' in data and 'total_rate' in data['property_tax']:
            rate = data['property_tax']['total_rate']
            if rate < 0 or rate > 0.10:
                logger.warning(f"Property tax rate seems unusual: {rate}")

        # Transfer tax rates should be between 0 and 0.02 (0% to 2%)
        if 'transfer_tax' in data:
            for key in ['state_rate', 'county_rate']:
                if key in data['transfer_tax']:
                    rate = data['transfer_tax'][key]
                    if rate < 0 or rate > 0.05:
                        logger.warning(f"{key} seems unusual: {rate}")

    def get_cached_data(self, state: str, county: str) -> Optional[Dict[str, Any]]:
        """Get cached data if available and fresh"""

        if not settings.USE_CACHED_RESULTS:
            return None

        try:
            data = self.db_client.get_tax_data(state, county)

            if data:
                # Check if data is stale
                last_verified = datetime.fromisoformat(data['last_verified'])
                age_days = (datetime.utcnow() - last_verified).days

                if age_days <= settings.CACHE_EXPIRY_DAYS:
                    logger.info(f"Using cached data ({age_days} days old)")
                    return data

                logger.info(f"Cached data is stale ({age_days} days old)")

        except Exception as e:
            logger.error(f"Failed to get cached data: {str(e)}")

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get scraper statistics"""

        return {
            "total_jurisdictions_scraped": self.db_client.get_total_count(),
            "avg_completeness": self.db_client.get_avg_completeness(),
            "avg_confidence": self.db_client.get_avg_confidence(),
            "stale_data_count": self.db_client.get_stale_count(),
        }
