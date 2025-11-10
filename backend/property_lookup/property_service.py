"""
Property Address Lookup Service

Handles property address validation, geocoding, and data retrieval.
Integrates with:
- Tax scraper database (property taxes, fees)
- External APIs (property value estimates, comparable sales)
- County/jurisdiction mapping

Created by: Neumann Rashid AI Development
Date: November 8, 2025
"""

import requests
from decimal import Decimal
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class PropertyAddress:
    """Structured property address"""
    street_address: str
    city: str
    state: str
    zip_code: str
    county: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    formatted_address: Optional[str] = None


@dataclass
class PropertyData:
    """Complete property information"""
    address: PropertyAddress
    estimated_value: Optional[Decimal] = None
    tax_assessment_value: Optional[Decimal] = None
    annual_property_tax: Optional[Decimal] = None
    monthly_property_tax: Optional[Decimal] = None
    property_type: Optional[str] = None  # Single Family, Condo, Townhouse
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    year_built: Optional[int] = None
    lot_size: Optional[float] = None

    # Tax and fee data from database
    tax_rate: Optional[Decimal] = None
    transfer_tax_rate: Optional[Decimal] = None
    recordation_tax_rate: Optional[Decimal] = None
    recording_fees: Optional[Dict] = None
    insurance_estimate: Optional[Decimal] = None

    # Metadata
    data_source: Optional[str] = None
    confidence_score: Optional[int] = None
    last_updated: Optional[str] = None


class PropertyLookupService:
    """
    Service for looking up property information by address.

    Integrates multiple data sources:
    1. Tax scraper database (fees, taxes)
    2. Geocoding API (address validation)
    3. Property data APIs (values, details)
    """

    def __init__(
        self,
        tax_scraper_url: str = "http://localhost:8001",
        geocoding_api_key: Optional[str] = None,
        property_api_key: Optional[str] = None
    ):
        """
        Initialize property lookup service.

        Args:
            tax_scraper_url: URL for tax scraper service
            geocoding_api_key: API key for geocoding (Google Maps, Mapbox, etc.)
            property_api_key: API key for property data (Zillow, Redfin, etc.)
        """
        self.tax_scraper_url = tax_scraper_url
        self.geocoding_api_key = geocoding_api_key
        self.property_api_key = property_api_key

    def lookup_property(self, address_string: str) -> PropertyData:
        """
        Complete property lookup from address string.

        Args:
            address_string: Full address (e.g., "123 Main St, Rockville, MD 20850")

        Returns:
            PropertyData with all available information
        """
        # Step 1: Parse and validate address
        parsed_address = self._parse_address(address_string)

        # Step 2: Geocode to get coordinates and county
        geocoded_address = self._geocode_address(parsed_address)

        # Step 3: Get tax data from database
        tax_data = self._get_tax_data(
            state=geocoded_address.state,
            county=geocoded_address.county
        )

        # Step 4: Get property details (optional - external API)
        property_details = self._get_property_details(geocoded_address)

        # Step 5: Calculate estimates
        property_data = self._build_property_data(
            address=geocoded_address,
            tax_data=tax_data,
            property_details=property_details
        )

        return property_data

    def _parse_address(self, address_string: str) -> PropertyAddress:
        """
        Parse address string into structured format.

        Basic parsing - in production, use USPS API or similar.
        """
        # Remove extra whitespace
        address_string = ' '.join(address_string.split())

        # Try to extract zip code
        zip_match = re.search(r'\b(\d{5})(?:-\d{4})?\b', address_string)
        zip_code = zip_match.group(1) if zip_match else None

        # Split address by commas first
        parts = address_string.split(',')

        street_address = None
        city = None
        state = None

        if len(parts) >= 3:
            street_address = parts[0].strip()
            city = parts[1].strip()
            state_zip = parts[2].strip()

            # Extract state from the state/zip part (e.g., "MD 20850" or "MD")
            state_match = re.search(r'\b([A-Z]{2})\b', state_zip)
            state = state_match.group(1) if state_match else None
        elif len(parts) == 2:
            street_address = parts[0].strip()
            city = parts[1].strip()
            # Try to find state in second part
            state_match = re.search(r'\b([A-Z]{2})\b', parts[1].upper())
            state = state_match.group(1) if state_match else None
        else:
            street_address = address_string
            # Last resort - try to find state anywhere
            state_match = re.search(r'\b([A-Z]{2})\s+\d{5}', address_string.upper())
            state = state_match.group(1) if state_match else None

        return PropertyAddress(
            street_address=street_address,
            city=city,
            state=state,
            zip_code=zip_code,
            formatted_address=address_string
        )

    def _geocode_address(self, address: PropertyAddress) -> PropertyAddress:
        """
        Geocode address to get coordinates and validate.

        Uses geocoding API (Google Maps, Mapbox, etc.)
        Falls back to database lookup if API unavailable.
        """
        if self.geocoding_api_key:
            # Use external geocoding API
            return self._geocode_with_api(address)
        else:
            # Use internal lookup (zip code to county mapping)
            return self._geocode_with_database(address)

    def _geocode_with_api(self, address: PropertyAddress) -> PropertyAddress:
        """
        Geocode using external API (Google Maps, etc.)

        In production, implement actual API integration.
        """
        # TODO: Implement actual geocoding API
        # For now, return mock data based on zip code

        # Maryland zip codes to counties (sample)
        zip_to_county = {
            '20850': 'Montgomery',
            '20851': 'Montgomery',
            '20852': 'Montgomery',
            '21201': 'Baltimore City',
            '21202': 'Baltimore City',
            '20601': "Prince George's",
            '20602': "Prince George's",
        }

        county = zip_to_county.get(address.zip_code, 'Unknown')

        # Update address with geocoded data
        address.county = county
        address.latitude = 39.0458  # Mock coordinates
        address.longitude = -77.4877

        return address

    def _geocode_with_database(self, address: PropertyAddress) -> PropertyAddress:
        """
        Lookup county from database using zip code.
        """
        # Query database for county by zip code
        # In production, implement actual database lookup

        # Maryland zip codes to counties (sample)
        zip_to_county = {
            '20850': 'Montgomery',
            '20851': 'Montgomery',
            '20852': 'Montgomery',
            '21201': 'Baltimore City',
            '21202': 'Baltimore City',
        }

        county = zip_to_county.get(address.zip_code)
        address.county = county

        return address

    def _get_tax_data(self, state: str, county: str) -> Dict:
        """
        Get tax data from scraper database.

        Calls tax scraper service to get current tax rates and fees.
        The scraper will automatically use LLM to search the web if data doesn't exist.
        """
        try:
            # Call tax scraper API - it will automatically search with LLM if needed
            # Timeout set to 60s to allow for LLM web search (typically takes 18-20 seconds)
            response = requests.get(
                f"{self.tax_scraper_url}/scrape/{state}/{county}",
                timeout=60
            )

            if response.status_code == 200:
                response_data = response.json()

                # Extract the 'data' field from the scraper response
                # Scraper returns: {"success": true, "data": {...}}
                if isinstance(response_data, dict) and 'data' in response_data:
                    return response_data['data']
                else:
                    # If response is already in the correct format
                    return response_data
            else:
                # Return empty dict if not found
                return {}

        except Exception as e:
            print(f"Error fetching tax data from scraper: {e}")
            return {}

    def _get_property_details(self, address: PropertyAddress) -> Dict:
        """
        Get property details from external API (Zillow, Redfin, etc.)

        This is optional and requires API keys.
        For MVP, return estimated values based on user input.
        """
        # TODO: Implement actual property API integration
        # Options: Zillow, Redfin, Realtor.com, Attom Data

        # For now, return mock data
        return {
            'estimated_value': None,  # Will be provided by user
            'property_type': 'Single Family',
            'bedrooms': None,
            'bathrooms': None,
            'square_feet': None,
            'year_built': None,
        }

    def _build_property_data(
        self,
        address: PropertyAddress,
        tax_data: Dict,
        property_details: Dict
    ) -> PropertyData:
        """
        Build complete PropertyData object from all sources.
        """
        # Extract tax rate from scraped data
        tax_rate = None
        annual_property_tax = None
        monthly_property_tax = None

        if tax_data and 'property_tax' in tax_data:
            tax_rate_raw = tax_data['property_tax'].get('total_rate')
            if tax_rate_raw:
                tax_rate = Decimal(str(tax_rate_raw))

        # Extract transfer tax
        transfer_tax_rate = None
        if tax_data and 'transfer_tax' in tax_data:
            state_rate = tax_data['transfer_tax'].get('state_rate', 0)
            county_rate = tax_data['transfer_tax'].get('county_rate', 0)
            transfer_tax_rate = Decimal(str(state_rate + county_rate))

        # Extract recordation tax
        recordation_tax_rate = None
        if tax_data and 'recordation_tax' in tax_data:
            # Handle tiered rates - use average or first tier
            tiers = tax_data['recordation_tax'].get('tiers', [])
            if tiers:
                recordation_tax_rate = Decimal(str(tiers[0].get('rate', 0)))

        # Extract recording fees
        recording_fees = tax_data.get('recording_fees', {})

        # Extract insurance estimate
        insurance_estimate = None
        if tax_data and 'insurance_estimate' in tax_data:
            base_premium = tax_data['insurance_estimate'].get('base_premium_per_100k')
            if base_premium:
                insurance_estimate = Decimal(str(base_premium))

        # Calculate confidence score
        confidence_score = self._calculate_confidence(tax_data, property_details)

        return PropertyData(
            address=address,
            estimated_value=property_details.get('estimated_value'),
            property_type=property_details.get('property_type'),
            bedrooms=property_details.get('bedrooms'),
            bathrooms=property_details.get('bathrooms'),
            square_feet=property_details.get('square_feet'),
            year_built=property_details.get('year_built'),

            # Tax data from scraper
            tax_rate=tax_rate,
            annual_property_tax=annual_property_tax,
            monthly_property_tax=monthly_property_tax,
            transfer_tax_rate=transfer_tax_rate,
            recordation_tax_rate=recordation_tax_rate,
            recording_fees=recording_fees,
            insurance_estimate=insurance_estimate,

            # Metadata
            data_source='tax_scraper',
            confidence_score=confidence_score,
        )

    def _calculate_confidence(self, tax_data: Dict, property_details: Dict) -> int:
        """
        Calculate confidence score for property data.

        Based on completeness of data from various sources.
        """
        score = 0

        # Tax data available (50 points)
        if tax_data:
            if 'property_tax' in tax_data:
                score += 20
            if 'transfer_tax' in tax_data:
                score += 15
            if 'recording_fees' in tax_data:
                score += 15

        # Property details available (50 points)
        if property_details:
            if property_details.get('estimated_value'):
                score += 25
            if property_details.get('property_type'):
                score += 10
            if property_details.get('square_feet'):
                score += 15

        return min(score, 100)

    def calculate_monthly_property_tax(
        self,
        property_value: Decimal,
        tax_rate: Optional[Decimal] = None,
        state: Optional[str] = None,
        county: Optional[str] = None
    ) -> Decimal:
        """
        Calculate monthly property tax.

        Args:
            property_value: Property value or assessment value
            tax_rate: Annual tax rate (if known)
            state: State code (if tax_rate not provided)
            county: County name (if tax_rate not provided)

        Returns:
            Monthly property tax amount
        """
        if tax_rate is None:
            # Fetch tax rate from database
            if state and county:
                tax_data = self._get_tax_data(state, county)
                if tax_data and 'property_tax' in tax_data:
                    tax_rate = Decimal(str(
                        tax_data['property_tax'].get('total_rate', 0.012)
                    ))
                else:
                    # Default to 1.2% if not found
                    tax_rate = Decimal('0.012')
            else:
                # Default to 1.2% if no location provided
                tax_rate = Decimal('0.012')

        # Calculate annual tax
        annual_tax = property_value * tax_rate

        # Convert to monthly
        monthly_tax = annual_tax / 12

        return monthly_tax

    def estimate_insurance(
        self,
        property_value: Decimal,
        state: Optional[str] = None,
        county: Optional[str] = None
    ) -> Decimal:
        """
        Estimate monthly homeowners insurance.

        Args:
            property_value: Property value
            state: State code
            county: County name

        Returns:
            Monthly insurance premium estimate
        """
        # Try to get estimate from tax data
        if state and county:
            tax_data = self._get_tax_data(state, county)
            if tax_data and 'insurance_estimate' in tax_data:
                base_premium = tax_data['insurance_estimate'].get('base_premium_per_100k')
                if base_premium:
                    # Calculate based on property value
                    annual_premium = (property_value / 100000) * Decimal(str(base_premium))
                    return annual_premium / 12

        # Default estimate: $650 per $100k annually
        annual_premium = (property_value / 100000) * Decimal('650')
        monthly_premium = annual_premium / 12

        return monthly_premium


def example_usage():
    """Example of using PropertyLookupService"""

    service = PropertyLookupService()

    # Lookup property by address
    address = "12345 Main Street, Rockville, MD 20850"
    property_data = service.lookup_property(address)

    print("Property Lookup Results:")
    print("=" * 80)
    print(f"Address: {property_data.address.formatted_address}")
    print(f"County: {property_data.address.county}")
    print(f"State: {property_data.address.state}")
    print(f"\nTax Information:")
    print(f"Tax Rate: {property_data.tax_rate * 100 if property_data.tax_rate else 'N/A'}%")
    print(f"Transfer Tax Rate: {property_data.transfer_tax_rate * 100 if property_data.transfer_tax_rate else 'N/A'}%")
    print(f"\nConfidence Score: {property_data.confidence_score}%")

    # Calculate property tax for a specific value
    property_value = Decimal('500000')
    monthly_tax = service.calculate_monthly_property_tax(
        property_value=property_value,
        state=property_data.address.state,
        county=property_data.address.county
    )
    print(f"\nFor property value ${property_value:,.2f}:")
    print(f"Estimated monthly property tax: ${monthly_tax:,.2f}")

    # Estimate insurance
    monthly_insurance = service.estimate_insurance(
        property_value=property_value,
        state=property_data.address.state,
        county=property_data.address.county
    )
    print(f"Estimated monthly insurance: ${monthly_insurance:,.2f}")


if __name__ == '__main__':
    example_usage()
