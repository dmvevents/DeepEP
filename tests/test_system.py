#!/usr/bin/env python3
"""
Comprehensive system test suite that logs all operations to JSON
Tests database reads/writes, API endpoints, and scraper functionality
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any
import sys


class SystemTester:
    def __init__(self, base_url: str = "http://localhost:8000", scraper_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.scraper_url = scraper_url
        self.test_results: List[Dict[str, Any]] = []

    def log_operation(self, operation: str, endpoint: str, method: str,
                      request_data: Any = None, response_data: Any = None,
                      status_code: int = None, error: str = None, duration_ms: float = None):
        """Log an operation to the results list"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "endpoint": endpoint,
            "method": method,
            "request_data": request_data,
            "response_data": response_data,
            "status_code": status_code,
            "success": status_code in [200, 201] if status_code else False,
            "error": error,
            "duration_ms": duration_ms
        }
        self.test_results.append(entry)
        return entry

    def test_api_health(self):
        """Test API health endpoint"""
        print("Testing API health...")
        start = time.time()
        try:
            response = requests.get(f"{self.base_url}/api/health/")
            duration = (time.time() - start) * 1000
            self.log_operation(
                operation="API Health Check",
                endpoint="/api/health/",
                method="GET",
                response_data=response.json() if response.ok else None,
                status_code=response.status_code,
                duration_ms=duration
            )
            print(f"  ✓ API health: {response.status_code}")
        except Exception as e:
            self.log_operation(
                operation="API Health Check",
                endpoint="/api/health/",
                method="GET",
                error=str(e)
            )
            print(f"  ✗ API health failed: {e}")

    def test_scraper_health(self):
        """Test scraper health endpoint"""
        print("Testing scraper health...")
        start = time.time()
        try:
            response = requests.get(f"{self.scraper_url}/health")
            duration = (time.time() - start) * 1000
            self.log_operation(
                operation="Scraper Health Check",
                endpoint="/health",
                method="GET",
                response_data=response.json() if response.ok else None,
                status_code=response.status_code,
                duration_ms=duration
            )
            print(f"  ✓ Scraper health: {response.status_code}")
        except Exception as e:
            self.log_operation(
                operation="Scraper Health Check",
                endpoint="/health",
                method="GET",
                error=str(e)
            )
            print(f"  ✗ Scraper health failed: {e}")

    def test_read_states(self):
        """Test reading states from database"""
        print("Testing database read - states...")
        start = time.time()
        try:
            response = requests.get(f"{self.base_url}/api/states/")
            duration = (time.time() - start) * 1000
            data = response.json() if response.ok else None
            self.log_operation(
                operation="Read States",
                endpoint="/api/states/",
                method="GET",
                response_data={"count": data.get("count") if data else 0, "sample": data.get("results", [])[:2] if data else []},
                status_code=response.status_code,
                duration_ms=duration
            )
            print(f"  ✓ Read {data.get('count', 0) if data else 0} states")
        except Exception as e:
            self.log_operation(
                operation="Read States",
                endpoint="/api/states/",
                method="GET",
                error=str(e)
            )
            print(f"  ✗ Read states failed: {e}")

    def test_read_counties(self, state_id: int = 20):
        """Test reading counties from database"""
        print(f"Testing database read - counties for state {state_id}...")
        start = time.time()
        try:
            response = requests.get(f"{self.base_url}/api/states/{state_id}/counties/")
            duration = (time.time() - start) * 1000
            data = response.json() if response.ok else None
            self.log_operation(
                operation="Read Counties",
                endpoint=f"/api/states/{state_id}/counties/",
                method="GET",
                request_data={"state_id": state_id},
                response_data={"count": len(data) if isinstance(data, list) else 0, "sample": data[:2] if isinstance(data, list) else []},
                status_code=response.status_code,
                duration_ms=duration
            )
            print(f"  ✓ Read {len(data) if isinstance(data, list) else 0} counties")
        except Exception as e:
            self.log_operation(
                operation="Read Counties",
                endpoint=f"/api/states/{state_id}/counties/",
                method="GET",
                request_data={"state_id": state_id},
                error=str(e)
            )
            print(f"  ✗ Read counties failed: {e}")

    def test_scrape_county(self, state: str = "MD", county: str = "Montgomery"):
        """Test scraping a county"""
        print(f"Testing scraper - {county}, {state}...")
        start = time.time()
        try:
            payload = {"state": state, "county": county, "force_refresh": False}
            response = requests.post(
                f"{self.scraper_url}/scrape",
                json=payload,
                timeout=60
            )
            duration = (time.time() - start) * 1000
            data = response.json() if response.ok else None

            # Simplify response data for logging
            simplified_data = None
            if data and isinstance(data, dict):
                simplified_data = {
                    "success": data.get("success"),
                    "data_completeness": data.get("data", {}).get("data_completeness"),
                    "scraper_confidence": data.get("data", {}).get("scraper_confidence"),
                    "processing_time": data.get("data", {}).get("processing_time")
                }

            self.log_operation(
                operation="Scrape County",
                endpoint="/scrape",
                method="POST",
                request_data=payload,
                response_data=simplified_data,
                status_code=response.status_code,
                duration_ms=duration
            )
            print(f"  ✓ Scraped {county}, {state} - Completeness: {simplified_data.get('data_completeness') if simplified_data else 'N/A'}%")
        except Exception as e:
            self.log_operation(
                operation="Scrape County",
                endpoint="/scrape",
                method="POST",
                request_data={"state": state, "county": county},
                error=str(e)
            )
            print(f"  ✗ Scrape failed: {e}")

    def test_read_tax_data(self, state_code: str = "MD", county_name: str = "Montgomery"):
        """Test reading tax data from database"""
        print(f"Testing database read - tax data for {county_name}, {state_code}...")
        start = time.time()
        try:
            response = requests.get(f"{self.base_url}/api/tax-data/{state_code}/{county_name}/")
            duration = (time.time() - start) * 1000
            data = response.json() if response.ok else None

            # Simplify response
            simplified_data = None
            if data and isinstance(data, dict):
                simplified_data = {
                    "state": data.get("state"),
                    "county": data.get("county"),
                    "data_completeness": data.get("data_completeness"),
                    "property_tax_rate": data.get("property_tax", {}).get("total_rate") if "property_tax" in data else None
                }

            self.log_operation(
                operation="Read Tax Data",
                endpoint=f"/api/tax-data/{state_code}/{county_name}/",
                method="GET",
                request_data={"state": state_code, "county": county_name},
                response_data=simplified_data,
                status_code=response.status_code,
                duration_ms=duration
            )
            print(f"  ✓ Read tax data - Completeness: {simplified_data.get('data_completeness') if simplified_data else 'N/A'}%")
        except Exception as e:
            self.log_operation(
                operation="Read Tax Data",
                endpoint=f"/api/tax-data/{state_code}/{county_name}/",
                method="GET",
                request_data={"state": state_code, "county": county_name},
                error=str(e)
            )
            print(f"  ✗ Read tax data failed: {e}")

    def run_all_tests(self):
        """Run all system tests"""
        print("="*60)
        print("Starting Comprehensive System Tests")
        print("="*60)

        # Health checks
        self.test_api_health()
        self.test_scraper_health()

        # Database reads
        self.test_read_states()
        self.test_read_counties()

        # Scraper test
        self.test_scrape_county()

        # Read scraped data
        time.sleep(2)  # Wait for data to be saved
        self.test_read_tax_data()

        print("="*60)
        print("Tests completed")
        print("="*60)

    def save_results(self, filename: str = "test_results.json"):
        """Save test results to JSON file"""
        with open(filename, 'w') as f:
            json.dump({
                "test_run_timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "passed": sum(1 for r in self.test_results if r["success"]),
                "failed": sum(1 for r in self.test_results if not r["success"]),
                "results": self.test_results
            }, f, indent=2)
        print(f"\n✓ Test results saved to {filename}")


if __name__ == "__main__":
    tester = SystemTester()
    tester.run_all_tests()

    # Save results
    output_file = sys.argv[1] if len(sys.argv) > 1 else "test_results.json"
    tester.save_results(output_file)

    # Print summary
    passed = sum(1 for r in tester.test_results if r["success"])
    total = len(tester.test_results)
    print(f"\nSummary: {passed}/{total} tests passed")

    sys.exit(0 if passed == total else 1)
