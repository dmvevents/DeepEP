"""
Script to scrape tax data for all US states and counties

This script will:
1. Load all US counties from a data file
2. Trigger scraping for each jurisdiction
3. Track progress and generate reports
4. Handle errors and retries

Usage:
    python scripts/scrape_all_jurisdictions.py [--states MD,VA,DC] [--test-mode]
"""
import sys
import os
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from tqdm import tqdm


# All US states
ALL_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]

# Sample counties for each state (in production, load from comprehensive CSV)
# This is a representative sample for testing
SAMPLE_COUNTIES = {
    'AL': ['Jefferson', 'Mobile', 'Madison', 'Montgomery', 'Tuscaloosa'],
    'AK': ['Anchorage', 'Fairbanks North Star', 'Matanuska-Susitna', 'Juneau'],
    'AZ': ['Maricopa', 'Pima', 'Pinal', 'Yavapai', 'Mohave'],
    'AR': ['Pulaski', 'Benton', 'Washington', 'Sebastian', 'Faulkner'],
    'CA': ['Los Angeles', 'San Diego', 'Orange', 'Riverside', 'San Bernardino', 'Santa Clara', 'Alameda'],
    'CO': ['Denver', 'El Paso', 'Arapahoe', 'Jefferson', 'Adams'],
    'CT': ['Fairfield', 'Hartford', 'New Haven', 'New London', 'Middlesex'],
    'DE': ['New Castle', 'Sussex', 'Kent'],
    'FL': ['Miami-Dade', 'Broward', 'Palm Beach', 'Hillsborough', 'Orange', 'Pinellas'],
    'GA': ['Fulton', 'Gwinnett', 'Cobb', 'DeKalb', 'Clayton'],
    'HI': ['Honolulu', 'Hawaii', 'Maui', 'Kauai'],
    'ID': ['Ada', 'Canyon', 'Kootenai', 'Bonneville', 'Bannock'],
    'IL': ['Cook', 'DuPage', 'Lake', 'Will', 'Kane'],
    'IN': ['Marion', 'Lake', 'Allen', 'Hamilton', 'St. Joseph'],
    'IA': ['Polk', 'Linn', 'Scott', 'Johnson', 'Black Hawk'],
    'KS': ['Johnson', 'Sedgwick', 'Shawnee', 'Wyandotte', 'Douglas'],
    'KY': ['Jefferson', 'Fayette', 'Kenton', 'Boone', 'Warren'],
    'LA': ['Orleans', 'Jefferson', 'East Baton Rouge', 'Caddo', 'St. Tammany'],
    'ME': ['Cumberland', 'York', 'Penobscot', 'Kennebec', 'Androscoggin'],
    'MD': ['Montgomery', 'Prince George\'s', 'Baltimore', 'Anne Arundel', 'Howard', 'Baltimore City'],
    'MA': ['Middlesex', 'Worcester', 'Essex', 'Suffolk', 'Norfolk'],
    'MI': ['Wayne', 'Oakland', 'Macomb', 'Kent', 'Genesee'],
    'MN': ['Hennepin', 'Ramsey', 'Dakota', 'Anoka', 'Washington'],
    'MS': ['Hinds', 'Harrison', 'DeSoto', 'Rankin', 'Madison'],
    'MO': ['St. Louis', 'Jackson', 'St. Charles', 'Jefferson', 'Greene'],
    'MT': ['Yellowstone', 'Missoula', 'Gallatin', 'Flathead', 'Cascade'],
    'NE': ['Douglas', 'Lancaster', 'Sarpy', 'Hall', 'Buffalo'],
    'NV': ['Clark', 'Washoe', 'Carson City', 'Lyon', 'Elko'],
    'NH': ['Hillsborough', 'Rockingham', 'Merrimack', 'Strafford', 'Grafton'],
    'NJ': ['Bergen', 'Middlesex', 'Essex', 'Hudson', 'Monmouth'],
    'NM': ['Bernalillo', 'Dona Ana', 'Sandoval', 'San Juan', 'Santa Fe'],
    'NY': ['Kings', 'Queens', 'New York', 'Suffolk', 'Bronx', 'Nassau', 'Westchester'],
    'NC': ['Mecklenburg', 'Wake', 'Guilford', 'Forsyth', 'Cumberland'],
    'ND': ['Cass', 'Burleigh', 'Grand Forks', 'Ward', 'Williams'],
    'OH': ['Cuyahoga', 'Franklin', 'Hamilton', 'Summit', 'Montgomery'],
    'OK': ['Oklahoma', 'Tulsa', 'Cleveland', 'Canadian', 'Comanche'],
    'OR': ['Multnomah', 'Washington', 'Clackamas', 'Lane', 'Marion'],
    'PA': ['Philadelphia', 'Allegheny', 'Montgomery', 'Bucks', 'Delaware'],
    'RI': ['Providence', 'Kent', 'Washington', 'Newport', 'Bristol'],
    'SC': ['Greenville', 'Richland', 'Charleston', 'Horry', 'Spartanburg'],
    'SD': ['Minnehaha', 'Pennington', 'Lincoln', 'Brown', 'Brookings'],
    'TN': ['Shelby', 'Davidson', 'Knox', 'Hamilton', 'Rutherford'],
    'TX': ['Harris', 'Dallas', 'Tarrant', 'Bexar', 'Travis', 'Collin', 'El Paso'],
    'UT': ['Salt Lake', 'Utah', 'Davis', 'Weber', 'Washington'],
    'VT': ['Chittenden', 'Rutland', 'Washington', 'Windsor', 'Franklin'],
    'VA': ['Fairfax', 'Virginia Beach', 'Prince William', 'Chesterfield', 'Henrico'],
    'WA': ['King', 'Pierce', 'Snohomish', 'Spokane', 'Clark'],
    'WV': ['Kanawha', 'Berkeley', 'Cabell', 'Wood', 'Monongalia'],
    'WI': ['Milwaukee', 'Dane', 'Waukesha', 'Brown', 'Racine'],
    'WY': ['Laramie', 'Natrona', 'Campbell', 'Fremont', 'Sweetwater']
}


def scrape_jurisdiction(scraper_url, state, county):
    """Scrape a single jurisdiction"""
    try:
        response = requests.post(
            f"{scraper_url}/scrape",
            json={"state": state, "county": county, "force_refresh": True},
            timeout=600
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                result_data = data.get('data', {})
                return {
                    'success': True,
                    'completeness': result_data.get('data_completeness', 0),
                    'confidence': result_data.get('scraper_confidence', 0),
                    'sources': len(result_data.get('sources', [])),
                    'error': None
                }

        return {
            'success': False,
            'completeness': 0,
            'confidence': 0,
            'sources': 0,
            'error': f"HTTP {response.status_code}"
        }

    except Exception as e:
        return {
            'success': False,
            'completeness': 0,
            'confidence': 0,
            'sources': 0,
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(description='Scrape all US jurisdictions')
    parser.add_argument('--states', type=str, help='Comma-separated list of state codes (e.g., MD,VA,DC)')
    parser.add_argument('--test-mode', action='store_true', help='Only scrape first 2 counties per state')
    parser.add_argument('--scraper-url', type=str, default='http://localhost:8001', help='Scraper service URL')
    parser.add_argument('--output', type=str, default='scrape_results.csv', help='Output CSV file')

    args = parser.parse_args()

    # Determine which states to process
    if args.states:
        states_to_process = [s.strip().upper() for s in args.states.split(',')]
    else:
        states_to_process = ALL_STATES

    print("=" * 60)
    print("Mortgage Calculator - Jurisdiction Scraper")
    print("=" * 60)
    print(f"States to process: {len(states_to_process)}")
    print(f"Scraper URL: {args.scraper_url}")
    print(f"Test mode: {args.test_mode}")
    print("=" * 60)
    print()

    # Check scraper service is running
    try:
        health = requests.get(f"{args.scraper_url}/health", timeout=5)
        if health.status_code == 200:
            print("✓ Scraper service is running")
            print(f"  Provider: {health.json().get('llm_provider')}")
            print()
        else:
            print("✗ Scraper service returned error")
            return
    except Exception as e:
        print(f"✗ Cannot connect to scraper service: {e}")
        print("  Make sure the scraper service is running:")
        print(f"  docker-compose up scraper-agent")
        return

    # Prepare results
    results = []
    total_jurisdictions = 0

    for state in states_to_process:
        counties = SAMPLE_COUNTIES.get(state, [])
        if args.test_mode:
            counties = counties[:2]
        total_jurisdictions += len(counties)

    print(f"Total jurisdictions to scrape: {total_jurisdictions}")
    print()

    # Start scraping
    start_time = datetime.now()

    with tqdm(total=total_jurisdictions, desc="Scraping") as pbar:
        for state in states_to_process:
            counties = SAMPLE_COUNTIES.get(state, [])
            if args.test_mode:
                counties = counties[:2]

            for county in counties:
                pbar.set_description(f"Scraping {county}, {state}")

                result = scrape_jurisdiction(args.scraper_url, state, county)

                results.append({
                    'state': state,
                    'county': county,
                    'success': result['success'],
                    'completeness': result['completeness'],
                    'confidence': result['confidence'],
                    'sources_found': result['sources'],
                    'error': result['error'],
                    'timestamp': datetime.now().isoformat()
                })

                pbar.update(1)

                # Brief pause to avoid overwhelming the service
                asyncio.sleep(0.5)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Save results
    df = pd.DataFrame(results)
    df.to_csv(args.output, index=False)

    # Print summary
    print()
    print("=" * 60)
    print("Scraping Complete!")
    print("=" * 60)
    print(f"Total time: {duration:.1f} seconds")
    print(f"Total jurisdictions: {len(results)}")
    print(f"Successful: {df['success'].sum()} ({df['success'].mean() * 100:.1f}%)")
    print(f"Failed: {(~df['success']).sum()}")
    print()
    print(f"Average completeness: {df['completeness'].mean():.1f}%")
    print(f"Average confidence: {df['confidence'].mean():.1f}%")
    print(f"Average sources per jurisdiction: {df['sources_found'].mean():.1f}")
    print()
    print(f"Results saved to: {args.output}")
    print()

    # Show failed jurisdictions if any
    failed = df[~df['success']]
    if len(failed) > 0:
        print("Failed jurisdictions:")
        print(failed[['state', 'county', 'error']].to_string(index=False))


if __name__ == '__main__':
    main()
