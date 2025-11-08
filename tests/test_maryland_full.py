#!/usr/bin/env python3
"""
Comprehensive Maryland County Scraper Test
Scrapes all Maryland counties and saves complete tax data to JSON
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any
import sys


class MarylandTester:
    def __init__(self, base_url: str = "http://localhost:8000", scraper_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.scraper_url = scraper_url
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "state": "Maryland",
            "state_code": "MD",
            "total_counties": 0,
            "scraped_successfully": 0,
            "failed_counties": [],
            "counties": []
        }

    def get_maryland_counties(self) -> List[Dict]:
        """Fetch all Maryland counties from the API"""
        print("Fetching Maryland counties from database...")
        try:
            # Get Maryland state ID (should be 20)
            response = requests.get(f"{self.base_url}/api/states/")
            states = response.json()

            maryland = None
            for state in states.get('results', []):
                if state['code'] == 'MD':
                    maryland = state
                    break

            if not maryland:
                print("❌ Maryland not found in database!")
                return []

            # Get all Maryland counties
            response = requests.get(f"{self.base_url}/api/states/{maryland['id']}/counties/")
            counties = response.json()

            print(f"✅ Found {len(counties)} Maryland counties")
            self.results['total_counties'] = len(counties)
            return counties

        except Exception as e:
            print(f"❌ Error fetching counties: {e}")
            return []

    def scrape_county(self, county_name: str, county_info: Dict) -> Dict[str, Any]:
        """Scrape a single county and return complete tax data"""
        print(f"\n{'='*60}")
        print(f"Scraping: {county_name}, MD")
        print(f"{'='*60}")

        start_time = time.time()

        try:
            payload = {
                "state": "MD",
                "county": county_name,
                "force_refresh": True
            }

            print(f"  ⏳ Requesting scrape...")
            response = requests.post(
                f"{self.scraper_url}/scrape",
                json=payload,
                timeout=120
            )

            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                if data.get('success'):
                    tax_data = data.get('data', {})

                    # Extract all the key fields
                    result = {
                        "county_id": county_info.get('id'),
                        "county_name": county_name,
                        "state": "MD",
                        "scrape_timestamp": datetime.now().isoformat(),
                        "scrape_duration_seconds": round(duration, 2),
                        "success": True,

                        # Data quality metrics
                        "data_completeness": tax_data.get('data_completeness'),
                        "scraper_confidence": tax_data.get('scraper_confidence'),
                        "processing_time": tax_data.get('processing_time'),
                        "last_verified": tax_data.get('last_verified'),

                        # Property Tax
                        "property_tax": {
                            "total_rate": tax_data.get('property_tax', {}).get('total_rate'),
                            "total_rate_source": tax_data.get('property_tax', {}).get('total_rate_source'),
                            "total_rate_confidence": tax_data.get('property_tax', {}).get('total_rate_confidence'),
                            "assessment_ratio": tax_data.get('property_tax', {}).get('assessment_ratio'),
                            "assessment_ratio_source": tax_data.get('property_tax', {}).get('assessment_ratio_source'),
                            "components": tax_data.get('property_tax', {}).get('components', {}),
                            "homestead_cap": tax_data.get('property_tax', {}).get('homestead_cap'),
                            "reassessment_cycle": tax_data.get('property_tax', {}).get('reassessment_cycle'),
                            "billing_schedule": tax_data.get('property_tax', {}).get('billing_schedule', {})
                        },

                        # Transfer Tax
                        "transfer_tax": {
                            "state_rate": tax_data.get('transfer_tax', {}).get('state_rate'),
                            "state_rate_source": tax_data.get('transfer_tax', {}).get('state_rate_source'),
                            "county_rate": tax_data.get('transfer_tax', {}).get('county_rate'),
                            "county_rate_source": tax_data.get('transfer_tax', {}).get('county_rate_source'),
                            "first_time_buyer_threshold": tax_data.get('transfer_tax', {}).get('first_time_buyer_threshold'),
                            "first_time_buyer_exemption": tax_data.get('transfer_tax', {}).get('first_time_buyer_exemption'),
                            "buyer_seller_split": tax_data.get('transfer_tax', {}).get('buyer_seller_split')
                        },

                        # Recordation Tax
                        "recordation_tax": {
                            "tiers": tax_data.get('recordation_tax', {}).get('tiers', []),
                            "tiers_source": tax_data.get('recordation_tax', {}).get('tiers_source'),
                            "notes": tax_data.get('recordation_tax', {}).get('notes')
                        },

                        # Recording Fees
                        "recording_fees": {
                            "deed": tax_data.get('recording_fees', {}).get('deed', {}),
                            "mortgage": tax_data.get('recording_fees', {}).get('mortgage', {}),
                            "surcharge": tax_data.get('recording_fees', {}).get('surcharge'),
                            "surcharge_description": tax_data.get('recording_fees', {}).get('surcharge_description'),
                            "recording_fees_source": tax_data.get('recording_fees', {}).get('recording_fees_source')
                        },

                        # Insurance Estimate
                        "insurance_estimate": {
                            "base_premium_per_100k": tax_data.get('insurance_estimate', {}).get('base_premium_per_100k'),
                            "insurance_source": tax_data.get('insurance_estimate', {}).get('insurance_source'),
                            "insurance_confidence": tax_data.get('insurance_estimate', {}).get('insurance_confidence')
                        },

                        # Sources and metadata
                        "sources_used": tax_data.get('sources_used', []),
                        "notes": tax_data.get('notes', ''),
                        "field_confidence_breakdown": tax_data.get('field_confidence_breakdown', {})
                    }

                    print(f"  ✅ Success!")
                    print(f"     Completeness: {result['data_completeness']}%")
                    print(f"     Confidence: {result['scraper_confidence']}%")
                    print(f"     Property Tax Rate: {result['property_tax']['total_rate']}")
                    print(f"     Transfer Tax (County): {result['transfer_tax']['county_rate']}")
                    print(f"     Duration: {duration:.2f}s")

                    self.results['scraped_successfully'] += 1
                    return result
                else:
                    error_msg = data.get('error', 'Unknown error')
                    print(f"  ❌ Scrape failed: {error_msg}")

                    self.results['failed_counties'].append({
                        "county": county_name,
                        "error": error_msg,
                        "duration": duration
                    })

                    return {
                        "county_name": county_name,
                        "state": "MD",
                        "success": False,
                        "error": error_msg,
                        "scrape_duration_seconds": round(duration, 2)
                    }
            else:
                error_msg = f"HTTP {response.status_code}"
                print(f"  ❌ HTTP Error: {response.status_code}")

                self.results['failed_counties'].append({
                    "county": county_name,
                    "error": error_msg,
                    "duration": duration
                })

                return {
                    "county_name": county_name,
                    "state": "MD",
                    "success": False,
                    "error": error_msg,
                    "scrape_duration_seconds": round(duration, 2)
                }

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            print(f"  ❌ Exception: {error_msg}")

            self.results['failed_counties'].append({
                "county": county_name,
                "error": error_msg,
                "duration": duration
            })

            return {
                "county_name": county_name,
                "state": "MD",
                "success": False,
                "error": error_msg,
                "scrape_duration_seconds": round(duration, 2)
            }

    def scrape_all_counties(self):
        """Scrape all Maryland counties"""
        counties = self.get_maryland_counties()

        if not counties:
            print("No counties found!")
            return

        print(f"\n{'='*60}")
        print(f"Starting to scrape {len(counties)} Maryland counties")
        print(f"{'='*60}\n")

        total_start = time.time()

        for i, county_info in enumerate(counties, 1):
            county_name = county_info['name']
            print(f"\n[{i}/{len(counties)}] Processing {county_name}...")

            result = self.scrape_county(county_name, county_info)
            self.results['counties'].append(result)

            # Small delay to avoid overwhelming the server
            if i < len(counties):
                time.sleep(1)

        total_duration = time.time() - total_start
        self.results['total_duration_seconds'] = round(total_duration, 2)
        self.results['total_duration_minutes'] = round(total_duration / 60, 2)

    def save_results(self, filename: str):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n{'='*60}")
        print(f"Results saved to: {filename}")
        print(f"{'='*60}")

    def print_summary(self):
        """Print summary of scraping results"""
        print(f"\n{'='*60}")
        print(f"MARYLAND SCRAPING SUMMARY")
        print(f"{'='*60}")
        print(f"Total Counties: {self.results['total_counties']}")
        print(f"Successfully Scraped: {self.results['scraped_successfully']}")
        print(f"Failed: {len(self.results['failed_counties'])}")
        print(f"Success Rate: {(self.results['scraped_successfully'] / self.results['total_counties'] * 100):.1f}%")
        print(f"Total Duration: {self.results.get('total_duration_minutes', 0):.2f} minutes")

        if self.results['failed_counties']:
            print(f"\nFailed Counties:")
            for failed in self.results['failed_counties']:
                print(f"  ❌ {failed['county']}: {failed['error']}")

        print(f"\n{'='*60}")


if __name__ == "__main__":
    output_file = sys.argv[1] if len(sys.argv) > 1 else "maryland_counties_complete.json"

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║        MARYLAND COMPLETE COUNTY SCRAPING TEST               ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    tester = MarylandTester()

    # Scrape all counties
    tester.scrape_all_counties()

    # Save results
    tester.save_results(output_file)

    # Print summary
    tester.print_summary()

    # Exit with appropriate code
    sys.exit(0 if len(tester.results['failed_counties']) == 0 else 1)
