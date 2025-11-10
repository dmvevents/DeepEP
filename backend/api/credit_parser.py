"""
Credit Report Parser Service

Normalizes tri-merge credit report JSON into structured Tradeline models.
Handles: tradelines, inquiries, late payments (DLA), special flags (IBR/defer/cosigned).

Author: Backend/Django Engineer
Date: 2025-11-09
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import logging

from django.db import transaction
from django.utils import timezone

from .models import CreditReport, Tradeline, AuditEvent

logger = logging.getLogger(__name__)


class CreditReportParser:
    """
    Parses tri-merge credit report JSON and creates normalized Tradeline objects.

    Supports standard tri-merge formats from major bureaus (Equifax, Experian, TransUnion).
    """

    def __init__(self, user, loan_estimate=None):
        """
        Initialize parser with user context.

        Args:
            user: Django User instance (borrower)
            loan_estimate: Optional LoanEstimate instance to associate
        """
        self.user = user
        self.loan_estimate = loan_estimate
        self.credit_report = None

    @transaction.atomic
    def parse_and_save(self, credit_data: Dict[str, Any]) -> CreditReport:
        """
        Parse tri-merge credit JSON and save to database.

        Args:
            credit_data: Dict containing tri-merge credit report data

        Returns:
            CreditReport instance with related Tradeline objects

        Expected credit_data structure:
        {
            "report_id": "CR-123456",
            "report_date": "2025-11-09",
            "bureau": "merged",  # or "equifax", "experian", "transunion"
            "scores": {
                "equifax": 720,
                "experian": 715,
                "transunion": 718
            },
            "tradelines": [
                {
                    "creditor_name": "Wells Fargo",
                    "account_number": "****1234",
                    "account_type": "mortgage",
                    "status": "open",
                    "current_balance": 250000.00,
                    "monthly_payment": 1500.00,
                    "credit_limit": null,
                    "opened_date": "2020-03-15",
                    "last_payment_date": "2025-10-01",
                    "days_past_due": 0,
                    "payment_history": {
                        "months_reviewed": 36,
                        "lates_30": [2, 0],  # [24mo, 36mo]
                        "lates_60": [1, 1],
                        "lates_90": [0, 0]
                    },
                    "flags": {
                        "deferred": false,
                        "ibr": false,
                        "cosigned": false,
                        "disputed": false
                    },
                    "remarks": "Account in good standing"
                }
            ],
            "inquiries": [
                {
                    "creditor": "Chase Bank",
                    "date": "2025-10-15",
                    "type": "hard"
                }
            ]
        }
        """
        try:
            # Create CreditReport
            self.credit_report = self._create_credit_report(credit_data)

            # Parse and save tradelines
            tradelines_data = credit_data.get('tradelines', [])
            tradelines = self._parse_tradelines(tradelines_data)

            # Update summary statistics
            self._update_credit_report_stats()

            # Log audit event
            self._log_credit_pull()

            logger.info(
                f"Successfully parsed credit report for user {self.user.username}: "
                f"{len(tradelines)} tradelines"
            )

            return self.credit_report

        except Exception as e:
            logger.error(f"Error parsing credit report for {self.user.username}: {str(e)}")
            raise

    def _create_credit_report(self, credit_data: Dict) -> CreditReport:
        """Create CreditReport instance from parsed data."""
        report_date_str = credit_data.get('report_date')
        report_date = datetime.fromisoformat(report_date_str) if report_date_str else timezone.now()

        # Calculate expiration (120 days from report date)
        expires_at = report_date + relativedelta(days=120)

        credit_report = CreditReport.objects.create(
            user=self.user,
            loan_estimate=self.loan_estimate,
            bureau=credit_data.get('bureau', 'merged'),
            status='pulled',
            report_id=credit_data.get('report_id', ''),
            report_date=report_date,
            expires_at=expires_at,
            equifax_score=credit_data.get('scores', {}).get('equifax'),
            experian_score=credit_data.get('scores', {}).get('experian'),
            transunion_score=credit_data.get('scores', {}).get('transunion'),
            raw_data=credit_data,
        )

        return credit_report

    def _parse_tradelines(self, tradelines_data: List[Dict]) -> List[Tradeline]:
        """Parse list of tradeline dictionaries into Tradeline model instances."""
        tradelines = []

        for tl_data in tradelines_data:
            try:
                tradeline = self._create_tradeline(tl_data)
                tradelines.append(tradeline)
            except Exception as e:
                logger.warning(
                    f"Failed to parse tradeline {tl_data.get('creditor_name')}: {str(e)}"
                )
                continue

        return tradelines

    def _create_tradeline(self, tl_data: Dict) -> Tradeline:
        """Create a single Tradeline instance from parsed data."""
        # Parse dates
        opened_date = self._parse_date(tl_data.get('opened_date'))
        last_payment_date = self._parse_date(tl_data.get('last_payment_date'))

        # Parse payment history
        payment_history = tl_data.get('payment_history', {})
        lates_30 = payment_history.get('lates_30', [0, 0])
        lates_60 = payment_history.get('lates_60', [0, 0])
        lates_90 = payment_history.get('lates_90', [0, 0])

        # Parse flags
        flags = tl_data.get('flags', {})

        # Determine payment count and <10 payments flag
        months_reviewed = payment_history.get('months_reviewed', 0)
        payment_count = payment_history.get('payment_count', months_reviewed)
        has_less_than_10_payments = payment_count < 10

        # Create Tradeline
        tradeline = Tradeline.objects.create(
            credit_report=self.credit_report,
            account_type=self._normalize_account_type(tl_data.get('account_type', 'other')),
            creditor_name=tl_data.get('creditor_name', 'Unknown Creditor'),
            account_number=self._mask_account_number(tl_data.get('account_number', '')),
            current_balance=Decimal(str(tl_data.get('current_balance', 0.00))),
            monthly_payment=Decimal(str(tl_data.get('monthly_payment', 0.00))),
            credit_limit=self._parse_decimal(tl_data.get('credit_limit')),
            status=self._normalize_status(tl_data.get('status', 'open')),
            opened_date=opened_date,
            last_payment_date=last_payment_date,
            days_past_due=int(tl_data.get('days_past_due', 0)),
            # DLA tracking
            lates_30_count_24mo=lates_30[0] if len(lates_30) > 0 else 0,
            lates_60_count_24mo=lates_60[0] if len(lates_60) > 0 else 0,
            lates_90_count_24mo=lates_90[0] if len(lates_90) > 0 else 0,
            lates_30_count_36mo=lates_30[1] if len(lates_30) > 1 else 0,
            lates_60_count_36mo=lates_60[1] if len(lates_60) > 1 else 0,
            lates_90_count_36mo=lates_90[1] if len(lates_90) > 1 else 0,
            # Special flags
            is_deferred=flags.get('deferred', False),
            is_ibr=flags.get('ibr', False),
            is_cosigned=flags.get('cosigned', False),
            is_disputed=flags.get('disputed', False),
            has_less_than_10_payments=has_less_than_10_payments,
            # Payment metadata
            payment_count=payment_count,
            months_reviewed=months_reviewed if months_reviewed > 0 else None,
            remarks=tl_data.get('remarks', ''),
            # Store raw data for audit
            raw_data=tl_data,
        )

        return tradeline

    def _update_credit_report_stats(self):
        """Update CreditReport summary statistics from tradelines."""
        if not self.credit_report:
            return

        tradelines = self.credit_report.tradelines.all()

        # Count tradelines
        self.credit_report.total_tradelines = tradelines.count()

        # Sum monthly debt (exclude charged off, closed, paid accounts)
        active_tradelines = tradelines.filter(
            status__in=['open']
        )
        total_monthly_debt = sum(
            tl.monthly_payment for tl in active_tradelines
        )
        self.credit_report.total_monthly_debt = Decimal(str(total_monthly_debt))

        # Count inquiries from raw data
        inquiries = self.credit_report.raw_data.get('inquiries', [])
        self.credit_report.total_inquiries = len(inquiries)

        self.credit_report.save()

    def _log_credit_pull(self):
        """Log audit event for credit pull."""
        # Mask SSN to last 4 digits only
        ssn_last_four = ''
        if hasattr(self.user, 'profile') and hasattr(self.user.profile, 'ssn'):
            ssn_last_four = AuditEvent.mask_ssn(self.user.profile.ssn)

        AuditEvent.objects.create(
            event_type='credit_pull',
            user=self.user,
            borrower_name=f"{self.user.first_name} {self.user.last_name}".strip(),
            ssn_last_four=ssn_last_four,
            loan_estimate=self.loan_estimate,
            context={
                'credit_report_id': self.credit_report.id,
                'bureau': self.credit_report.bureau,
                'middle_score': self.credit_report.middle_score,
                'tradelines_count': self.credit_report.total_tradelines,
            }
        )

    # === Helper Methods ===

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str).date()
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _parse_decimal(value: Any) -> Optional[Decimal]:
        """Parse value to Decimal or None."""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _mask_account_number(account_num: str) -> str:
        """
        Ensure only last 4 digits are stored for PII protection.
        Input: "1234567890" or "****7890"
        Output: "7890"
        """
        if not account_num:
            return ''
        # Remove non-digits
        clean = ''.join(filter(str.isdigit, account_num))
        # Return last 4 only
        return clean[-4:] if len(clean) >= 4 else clean

    @staticmethod
    def _normalize_account_type(account_type: str) -> str:
        """Normalize account type to match model choices."""
        account_type_lower = account_type.lower().replace(' ', '_')

        mapping = {
            'mortgage': 'mortgage',
            'home': 'mortgage',
            'auto': 'auto',
            'auto_loan': 'auto',
            'car': 'auto',
            'vehicle': 'auto',
            'student': 'student',
            'student_loan': 'student',
            'education': 'student',
            'credit_card': 'credit_card',
            'creditcard': 'credit_card',
            'card': 'credit_card',
            'revolving': 'credit_card',
            'personal': 'personal',
            'personal_loan': 'personal',
            'installment': 'installment',
            'collection': 'collection',
            'collections': 'collection',
        }

        return mapping.get(account_type_lower, 'other')

    @staticmethod
    def _normalize_status(status: str) -> str:
        """Normalize account status to match model choices."""
        status_lower = status.lower()

        mapping = {
            'open': 'open',
            'active': 'open',
            'current': 'open',
            'closed': 'closed',
            'paid': 'paid',
            'paid_off': 'paid',
            'paidoff': 'paid',
            'charge_off': 'charge_off',
            'chargeoff': 'charge_off',
            'charged_off': 'charge_off',
            'collection': 'collection',
            'collections': 'collection',
        }

        return mapping.get(status_lower, 'open')


def parse_credit_report(user, credit_data: Dict, loan_estimate=None) -> CreditReport:
    """
    Convenience function to parse credit report.

    Args:
        user: Django User instance
        credit_data: Tri-merge credit report JSON
        loan_estimate: Optional LoanEstimate to associate

    Returns:
        CreditReport instance with normalized tradelines
    """
    parser = CreditReportParser(user, loan_estimate)
    return parser.parse_and_save(credit_data)
