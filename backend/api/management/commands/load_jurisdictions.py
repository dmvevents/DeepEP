"""
Management command to load US states and counties
"""
from django.core.management.base import BaseCommand
from api.models import State, County


class Command(BaseCommand):
    help = 'Load US states and counties into database'

    def handle(self, *args, **kwargs):
        self.stdout.write('Loading US jurisdictions...')

        # Load all 50 states
        states_data = [
            ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
            ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'),
            ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
            ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'),
            ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
            ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
            ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
            ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
            ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
            ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
            ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'),
            ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
            ('WI', 'Wisconsin'), ('WY', 'Wyoming')
        ]

        states_created = 0
        for code, name in states_data:
            state, created = State.objects.get_or_create(
                code=code,
                defaults={'name': name, 'active': True}
            )
            if created:
                states_created += 1
                self.stdout.write(f'Created state: {name} ({code})')

        self.stdout.write(self.style.SUCCESS(f'States: {states_created} created, {len(states_data) - states_created} already exist'))

        # Sample counties for Maryland (for testing)
        # In production, you'd want to load all ~3,143 US counties from a data file
        md_counties = [
            'Allegany', 'Anne Arundel', 'Baltimore', 'Calvert', 'Caroline',
            'Carroll', 'Cecil', 'Charles', 'Dorchester', 'Frederick',
            'Garrett', 'Harford', 'Howard', 'Kent', 'Montgomery',
            'Prince George\'s', 'Queen Anne\'s', 'Somerset', 'St. Mary\'s',
            'Talbot', 'Washington', 'Wicomico', 'Worcester', 'Baltimore City'
        ]

        md_state = State.objects.get(code='MD')
        counties_created = 0

        for county_name in md_counties:
            county, created = County.objects.get_or_create(
                state=md_state,
                name=county_name,
                defaults={'active': True}
            )
            if created:
                counties_created += 1
                self.stdout.write(f'Created county: {county_name}, MD')

        self.stdout.write(self.style.SUCCESS(f'Sample counties: {counties_created} created'))
        self.stdout.write(self.style.SUCCESS('✓ Jurisdictions loaded successfully'))
        self.stdout.write(self.style.WARNING('Note: Only Maryland counties loaded as sample. Load full county data from CSV/JSON for production.'))
