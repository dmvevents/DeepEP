#!/usr/bin/env python3
"""
Multi-State County Scraper
Scrapes VA, DC, and PA counties
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any
import sys


class MultiStateTester:
    def __init__(self, base_url: str = "http://localhost:8000", scraper_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.scraper_url = scraper_url
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "states_scraped": [],
            "total_jurisdictions": 0,
            "total_successful": 0,
            "total_failed": 0,
            "failed_jurisdictions": [],
            "by_state": {}
        }

    def get_counties_by_state(self, state_code: str) -> List[Dict]:
        """Fetch all counties for a given state"""
        try:
            response = requests.get(f"{self.base_url}/api/states/")
            states = response.json()

            state = None
            for s in states.get('results', []):
                if s['code'] == state_code:
                    state = s
                    break

            if not state:
                print(f"❌ State {state_code} not found!")
                return []

            response = requests.get(f"{self.base_url}/api/states/{state['id']}/counties/")
            counties = response.json()

            print(f"✅ Found {len(counties)} counties in {state_code}")
            return counties

        except Exception as e:
            print(f"❌ Error fetching counties for {state_code}: {e}")
            return []

    def scrape_jurisdiction(self, state_code: str, jurisdiction_name: str, jurisdiction_info: Dict) -> Dict[str, Any]:
        """Scrape a single jurisdiction"""
        start_time = time.time()

        try:
            payload = {
                "state": state_code,
                "county": jurisdiction_name,
                "force_refresh": True
            }

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

                    result = {
                        "jurisdiction_id": jurisdiction_info.get('id'),
                        "jurisdiction_name": jurisdiction_name,
                        "state": state_code,
                        "scrape_timestamp": datetime.now().isoformat(),
                        "scrape_duration_seconds": round(duration, 2),
                        "success": True,
                        "data_completeness": tax_data.get('data_completeness'),
                        "scraper_confidence": tax_data.get('scraper_confidence'),
                        "property_tax": {
                            "total_rate": tax_data.get('property_tax', {}).get('total_rate'),
                            "components": tax_data.get('property_tax', {}).get('components', {})
                        },
                        "transfer_tax": {
                            "state_rate": tax_data.get('transfer_tax', {}).get('state_rate'),
                            "county_rate": tax_data.get('transfer_tax', {}).get('county_rate')
                        },
                        "recording_fees": tax_data.get('recording_fees', {}),
                        "sources_used": tax_data.get('sources_used', [])
                    }

                    return result
                else:
                    return {
                        "jurisdiction_name": jurisdiction_name,
                        "state": state_code,
                        "success": False,
                        "error": data.get('error', 'Unknown error'),
                        "scrape_duration_seconds": round(duration, 2)
                    }
            else:
                return {
                    "jurisdiction_name": jurisdiction_name,
                    "state": state_code,
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "scrape_duration_seconds": round(duration, 2)
                }

        except Exception as e:
            duration = time.time() - start_time
            return {
                "jurisdiction_name": jurisdiction_name,
                "state": state_code,
                "success": False,
                "error": str(e),
                "scrape_duration_seconds": round(duration, 2)
            }

    def scrape_state(self, state_code: str, state_name: str):
        """Scrape all jurisdictions in a state"""
        print(f"\n{'='*70}")
        print(f"SCRAPING: {state_name} ({state_code})")
        print(f"{'='*70}\n")

        counties = self.get_counties_by_state(state_code)
        if not counties:
            return

        state_results = {
            "state_code": state_code,
            "state_name": state_name,
            "total": len(counties),
            "successful": 0,
            "failed": 0,
            "jurisdictions": []
        }

        for i, county_info in enumerate(counties, 1):
            jurisdiction_name = county_info['name']
            print(f"[{i}/{len(counties)}] {jurisdiction_name}, {state_code}...", end=' ')

            result = self.scrape_jurisdiction(state_code, jurisdiction_name, county_info)
            state_results['jurisdictions'].append(result)

            if result.get('success'):
                state_results['successful'] += 1
                self.results['total_successful'] += 1
                print(f"✅ {result.get('data_completeness', 'N/A')}% complete ({result.get('scrape_duration_seconds', 0):.1f}s)")
            else:
                state_results['failed'] += 1
                self.results['total_failed'] += 1
                self.results['failed_jurisdictions'].append(f"{jurisdiction_name}, {state_code}")
                print(f"❌ {result.get('error', 'Unknown')} ({result.get('scrape_duration_seconds', 0):.1f}s)")

            time.sleep(1)  # Rate limiting

        self.results['by_state'][state_code] = state_results
        self.results['states_scraped'].append(state_code)
        self.results['total_jurisdictions'] += len(counties)

    def scrape_all_states(self):
        """Scrape VA, DC, and PA"""
        total_start = time.time()

        self.scrape_state('VA', 'Virginia')
        self.scrape_state('DC', 'District of Columbia')
        self.scrape_state('PA', 'Pennsylvania')

        total_duration = time.time() - total_start
        self.results['total_duration_seconds'] = round(total_duration, 2)
        self.results['total_duration_minutes'] = round(total_duration / 60, 2)

    def save_results(self, filename: str):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✅ Results saved to: {filename}")

    def print_summary(self):
        """Print summary of scraping results"""
        print(f"\n{'='*70}")
        print(f"MULTI-STATE SCRAPING SUMMARY")
        print(f"{'='*70}")
        print(f"Total Jurisdictions: {self.results['total_jurisdictions']}")
        print(f"Successfully Scraped: {self.results['total_successful']}")
        print(f"Failed: {self.results['total_failed']}")
        print(f"Success Rate: {(self.results['total_successful'] / self.results['total_jurisdictions'] * 100):.1f}%")
        print(f"Total Duration: {self.results.get('total_duration_minutes', 0):.2f} minutes")

        print(f"\nBy State:")
        for state_code in ['VA', 'DC', 'PA']:
            if state_code in self.results['by_state']:
                state = self.results['by_state'][state_code]
                success_rate = (state['successful'] / state['total'] * 100) if state['total'] > 0 else 0
                print(f"  {state_code}: {state['successful']}/{state['total']} ({success_rate:.1f}%)")

        if self.results['failed_jurisdictions']:
            print(f"\nFailed Jurisdictions:")
            for failed in self.results['failed_jurisdictions']:
                print(f"  ❌ {failed}")

        print(f"\n{'='*70}")


if __name__ == "__main__":
    output_file = sys.argv[1] if len(sys.argv) > 1 else "multi_state_results.json"

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║        MULTI-STATE SCRAPING: VA, DC, PA                     ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    tester = MultiStateTester()
    tester.scrape_all_states()
    tester.save_results(output_file)
    tester.print_summary()

    sys.exit(0 if tester.results['total_failed'] == 0 else 1)
