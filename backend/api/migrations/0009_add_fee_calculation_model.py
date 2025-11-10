# Generated manually on 2025-11-10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("api", "0008_add_pricing_scenario_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeeCalculation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "property_value",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Property value/purchase price",
                        max_digits=12,
                    ),
                ),
                (
                    "loan_amount",
                    models.DecimalField(
                        decimal_places=2, help_text="Loan amount", max_digits=12
                    ),
                ),
                (
                    "loan_type",
                    models.CharField(
                        choices=[
                            ("conventional", "Conventional"),
                            ("fha", "FHA"),
                            ("va", "VA"),
                            ("usda", "USDA"),
                        ],
                        default="conventional",
                        max_length=20,
                    ),
                ),
                ("first_time_homebuyer", models.BooleanField(default=False)),
                ("is_new_construction", models.BooleanField(default=False)),
                ("closing_date", models.DateField(blank=True, null=True)),
                ("zip_code", models.CharField(blank=True, max_length=10)),
                (
                    "total_transfer_taxes",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "total_recording_fees",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "total_recordation_taxes",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "total_title_fees",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "total_prepaids",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "total_escrows",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "total_mortgage_insurance",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "total_fees",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                (
                    "fee_breakdown",
                    models.JSONField(
                        help_text="Complete fee breakdown with line items, sources, and calculation traces"
                    ),
                ),
                (
                    "deterministic_hash",
                    models.CharField(
                        db_index=True,
                        help_text="Hash of inputs for determinism verification",
                        max_length=32,
                    ),
                ),
                (
                    "jurisdiction",
                    models.CharField(
                        help_text="Jurisdiction (State-County) for this calculation",
                        max_length=100,
                    ),
                ),
                (
                    "tax_data_version",
                    models.CharField(
                        default="2.0",
                        help_text="Tax data schema version used",
                        max_length=10,
                    ),
                ),
                (
                    "calculation_timestamp",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "loan_estimate",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="fee_calculations",
                        to="api.loanestimate",
                    ),
                ),
                (
                    "pricing_scenario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="fee_calculations",
                        to="api.pricingscenario",
                    ),
                ),
                (
                    "tax_data",
                    models.ForeignKey(
                        blank=True,
                        help_text="TaxData version used for this calculation",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="fee_calculations",
                        to="api.taxdata",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="fee_calculations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-calculation_timestamp"],
            },
        ),
        migrations.AddIndex(
            model_name="feecalculation",
            index=models.Index(
                fields=["user", "-calculation_timestamp"],
                name="api_feecalc_user_id_calc_ts_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="feecalculation",
            index=models.Index(
                fields=["loan_estimate", "-calculation_timestamp"],
                name="api_feecalc_loan_est_id_calc_ts_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="feecalculation",
            index=models.Index(
                fields=["pricing_scenario", "-calculation_timestamp"],
                name="api_feecalc_pricing_scen_id_calc_ts_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="feecalculation",
            index=models.Index(
                fields=["deterministic_hash"], name="api_feecalc_det_hash_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="feecalculation",
            index=models.Index(
                fields=["jurisdiction", "-calculation_timestamp"],
                name="api_feecalc_jurisdiction_calc_ts_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="feecalculation",
            index=models.Index(
                fields=["-calculation_timestamp"], name="api_feecalc_calc_ts_idx"
            ),
        ),
    ]
