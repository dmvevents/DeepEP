# Generated manually on 2025-11-09 23:59
# Phase 1: Intake & Credit - Mortgage Status Tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_add_credit_normalized_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='mortgage_statuses',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='List of mortgage status objects tracking forbearance, modifications, transfers, and foreclosures'
            ),
        ),
    ]
