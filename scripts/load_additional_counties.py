#!/usr/bin/env python3
"""Load counties for VA, DC, and PA into the database"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/Users/antonalexander/Github/real_estate_app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import State, County

# Virginia counties (sample - major counties)
VA_COUNTIES = [
    "Fairfax", "Prince William", "Virginia Beach City", "Loudoun",
    "Henrico", "Chesterfield", "Arlington", "Norfolk City",
    "Richmond City", "Alexandria City", "Chesapeake City", "Newport News City",
    "Hampton City", "Suffolk City", "Roanoke City", "Portsmouth City",
    "Albemarle", "Spotsylvania", "Stafford", "Montgomery"
]

# Pennsylvania counties (sample - major counties)
PA_COUNTIES = [
    "Philadelphia", "Allegheny", "Montgomery", "Bucks", "Delaware",
    "Chester", "Lancaster", "York", "Berks", "Westmoreland",
    "Lehigh", "Luzerne", "Northampton", "Dauphin", "Washington",
    "Erie", "Cumberland", "Lackawanna", "Butler", "Centre"
]

# DC is its own jurisdiction
DC_JURISDICTIONS = ["District of Columbia"]

def load_counties():
    """Load counties for VA, DC, and PA"""

    # Virginia
    va_state = State.objects.get(code='VA')
    print(f"\nLoading {len(VA_COUNTIES)} Virginia counties...")
    va_created = 0
    for county_name in VA_COUNTIES:
        county, created = County.objects.get_or_create(
            state=va_state,
            name=county_name,
            defaults={'active': True}
        )
        if created:
            va_created += 1
            print(f"  ✅ Created: {county_name}")
        else:
            print(f"  ⏭️  Exists: {county_name}")
    print(f"Virginia: {va_created} new, {len(VA_COUNTIES) - va_created} existing")

    # Pennsylvania
    pa_state = State.objects.get(code='PA')
    print(f"\nLoading {len(PA_COUNTIES)} Pennsylvania counties...")
    pa_created = 0
    for county_name in PA_COUNTIES:
        county, created = County.objects.get_or_create(
            state=pa_state,
            name=county_name,
            defaults={'active': True}
        )
        if created:
            pa_created += 1
            print(f"  ✅ Created: {county_name}")
        else:
            print(f"  ⏭️  Exists: {county_name}")
    print(f"Pennsylvania: {pa_created} new, {len(PA_COUNTIES) - pa_created} existing")

    # DC
    dc_state = State.objects.get(code='DC')
    print(f"\nLoading Washington DC...")
    dc_created = 0
    for jurisdiction_name in DC_JURISDICTIONS:
        county, created = County.objects.get_or_create(
            state=dc_state,
            name=jurisdiction_name,
            defaults={'active': True}
        )
        if created:
            dc_created += 1
            print(f"  ✅ Created: {jurisdiction_name}")
        else:
            print(f"  ⏭️  Exists: {jurisdiction_name}")
    print(f"DC: {dc_created} new, {len(DC_JURISDICTIONS) - dc_created} existing")

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Virginia: {County.objects.filter(state=va_state).count()} total counties")
    print(f"  Pennsylvania: {County.objects.filter(state=pa_state).count()} total counties")
    print(f"  DC: {County.objects.filter(state=dc_state).count()} total jurisdictions")
    print(f"{'='*60}")

if __name__ == '__main__':
    load_counties()
