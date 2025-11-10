"""
Unit tests for Credit Report Parser

Tests parsing of tri-merge credit reports with various scenarios:
1. Clean credit profile (no lates, high scores)
2. Profile with recent lates and deferred student loans
3. Profile with cosigned accounts and <10 payments

Author: Backend/Django Engineer
Date: 2025-11-09
"""
from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date

from .credit_parser import CreditReportParser, parse_credit_report
from .models import CreditReport, Tradeline, AuditEvent


class CreditReportParserTestCase(TestCase):
    """Test credit report parsing with 3 sample scenarios."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='testborrower',
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )

    def test_sample_1_clean_credit_profile(self):
        """
        Sample 1: Clean credit profile
        - No late payments
        - All accounts in good standing
        - High credit scores
        - Mix of account types
        """
        credit_data = {
            "report_id": "CR-2025-001",
            "report_date": "2025-11-09",
            "bureau": "merged",
            "scores": {
                "equifax": 760,
                "experian": 755,
                "transunion": 758
            },
            "tradelines": [
                {
                    "creditor_name": "Wells Fargo Mortgage",
                    "account_number": "****5678",
                    "account_type": "mortgage",
                    "status": "open",
                    "current_balance": 325000.00,
                    "monthly_payment": 2100.00,
                    "credit_limit": None,
                    "opened_date": "2020-06-15",
                    "last_payment_date": "2025-10-01",
                    "days_past_due": 0,
                    "payment_history": {
                        "months_reviewed": 36,
                        "payment_count": 64,
                        "lates_30": [0, 0],
                        "lates_60": [0, 0],
                        "lates_90": [0, 0]
                    },
                    "flags": {
                        "deferred": False,
                        "ibr": False,
                        "cosigned": False,
                        "disputed": False
                    },
                    "remarks": "Account in good standing"
                },
                {
                    "creditor_name": "Chase Auto Finance",
                    "account_number": "****9012",
                    "account_type": "auto",
                    "status": "open",
                    "current_balance": 18500.00,
                    "monthly_payment": 450.00,
                    "credit_limit": None,
                    "opened_date": "2023-03-20",
                    "last_payment_date": "2025-10-15",
                    "days_past_due": 0,
                    "payment_history": {
                        "months_reviewed": 30,
                        "payment_count": 31,
                        "lates_30": [0, 0],
                        "lates_60": [0, 0],
                        "lates_90": [0, 0]
                    },
                    "flags": {
                        "deferred": False,
                        "ibr": False,
                        "cosigned": False,
                        "disputed": False
                    },
                    "remarks": ""
                },
                {
                    "creditor_name": "American Express",
                    "account_number": "****3456",
                    "account_type": "credit_card",
                    "status": "open",
                    "current_balance": 2500.00,
                    "monthly_payment": 125.00,
                    "credit_limit": 15000.00,
                    "opened_date": "2018-01-10",
                    "last_payment_date": "2025-10-25",
                    "days_past_due": 0,
                    "payment_history": {
                        "months_reviewed": 36,
                        "payment_count": 90,
                        "lates_30": [0, 0],
                        "lates_60": [0, 0],
                        "lates_90": [0, 0]
                    },
                    "flags": {
                        "deferred": False,
                        "ibr": False,
                        "cosigned": False,
                        "disputed": False
                    },
                    "remarks": "Excellent payment history"
                }
            ],
            "inquiries": [
                {
                    "creditor": "Rocket Mortgage",
                    "date": "2025-09-15",
                    "type": "hard"
                }
            ]
        }

        # Parse credit report
        credit_report = parse_credit_report(self.user, credit_data)

        # Assertions
        self.assertIsNotNone(credit_report)
        self.assertEqual(credit_report.user, self.user)
        self.assertEqual(credit_report.bureau, 'merged')
        self.assertEqual(credit_report.equifax_score, 760)
        self.assertEqual(credit_report.experian_score, 755)
        self.assertEqual(credit_report.transunion_score, 758)
        self.assertEqual(credit_report.middle_score, 758)  # Middle of 755, 758, 760
        self.assertEqual(credit_report.total_tradelines, 3)
        self.assertEqual(credit_report.total_inquiries, 1)

        # Check tradelines
        tradelines = credit_report.tradelines.all()
        self.assertEqual(tradelines.count(), 3)

        # Check mortgage tradeline
        mortgage = tradelines.get(account_type='mortgage')
        self.assertEqual(mortgage.creditor_name, 'Wells Fargo Mortgage')
        self.assertEqual(mortgage.account_number, '5678')
        self.assertEqual(mortgage.current_balance, Decimal('325000.00'))
        self.assertEqual(mortgage.monthly_payment, Decimal('2100.00'))
        self.assertEqual(mortgage.lates_30_count_24mo, 0)
        self.assertEqual(mortgage.lates_60_count_24mo, 0)
        self.assertEqual(mortgage.lates_90_count_24mo, 0)
        self.assertFalse(mortgage.is_deferred)
        self.assertFalse(mortgage.is_ibr)
        self.assertFalse(mortgage.is_cosigned)
        self.assertFalse(mortgage.has_less_than_10_payments)
        self.assertFalse(mortgage.has_recent_lates)

        # Check audit event was logged
        audit_events = AuditEvent.objects.filter(user=self.user, event_type='credit_pull')
        self.assertEqual(audit_events.count(), 1)

    def test_sample_2_recent_lates_and_deferred_student_loans(self):
        """
        Sample 2: Profile with credit issues
        - Recent late payments (30/60 day)
        - Deferred student loans
        - Lower credit scores
        - IBR plan on one student loan
        """
        credit_data = {
            "report_id": "CR-2025-002",
            "report_date": "2025-11-09",
            "bureau": "merged",
            "scores": {
                "equifax": 640,
                "experian": 638,
                "transunion": 642
            },
            "tradelines": [
                {
                    "creditor_name": "Bank of America",
                    "account_number": "****7890",
                    "account_type": "credit_card",
                    "status": "open",
                    "current_balance": 8500.00,
                    "monthly_payment": 250.00,
                    "credit_limit": 10000.00,
                    "opened_date": "2019-05-10",
                    "last_payment_date": "2025-09-20",
                    "days_past_due": 30,
                    "payment_history": {
                        "months_reviewed": 36,
                        "payment_count": 75,
                        "lates_30": [2, 3],  # 2 in last 24mo, 3 in last 36mo
                        "lates_60": [1, 1],  # 1 in both periods
                        "lates_90": [0, 0]
                    },
                    "flags": {
                        "deferred": False,
                        "ibr": False,
                        "cosigned": False,
                        "disputed": False
                    },
                    "remarks": "Currently past due"
                },
                {
                    "creditor_name": "Navient Student Loans",
                    "account_number": "****2345",
                    "account_type": "student",
                    "status": "open",
                    "current_balance": 45000.00,
                    "monthly_payment": 0.00,
                    "credit_limit": None,
                    "opened_date": "2016-08-01",
                    "last_payment_date": None,
                    "days_past_due": 0,
                    "payment_history": {
                        "months_reviewed": 36,
                        "payment_count": 24,
                        "lates_30": [0, 0],
                        "lates_60": [0, 0],
                        "lates_90": [0, 0]
                    },
                    "flags": {
                        "deferred": True,
                        "ibr": False,
                        "cosigned": False,
                        "disputed": False
                    },
                    "remarks": "In school deferment"
                },
                {
                    "creditor_name": "FedLoan Servicing",
                    "account_number": "****6789",
                    "account_type": "student",
                    "status": "open",
                    "current_balance": 32000.00,
                    "monthly_payment": 180.00,
                    "credit_limit": None,
                    "opened_date": "2015-09-01",
                    "last_payment_date": "2025-10-01",
                    "days_past_due": 0,
                    "payment_history": {
                        "months_reviewed": 36,
                        "payment_count": 48,
                        "lates_30": [0, 0],
                        "lates_60": [0, 0],
                        "lates_90": [0, 0]
                    },
                    "flags": {
                        "deferred": False,
                        "ibr": True,
                        "cosigned": False,
                        "disputed": False
                    },
                    "remarks": "Income-Based Repayment plan"
                }
            ],
            "inquiries": []
        }

        # Parse credit report
        credit_report = parse_credit_report(self.user, credit_data)

        # Assertions
        self.assertEqual(credit_report.middle_score, 640)
        self.assertEqual(credit_report.total_tradelines, 3)

        # Check credit card with lates
        cc = credit_report.tradelines.get(account_type='credit_card')
        self.assertEqual(cc.lates_30_count_24mo, 2)
        self.assertEqual(cc.lates_30_count_36mo, 3)
        self.assertEqual(cc.lates_60_count_24mo, 1)
        self.assertEqual(cc.lates_60_count_36mo, 1)
        self.assertEqual(cc.days_past_due, 30)
        self.assertTrue(cc.has_recent_lates)
        self.assertEqual(cc.total_lates_24mo, 3)  # 2 + 1 + 0

        # Check deferred student loan
        deferred_loan = credit_report.tradelines.filter(
            account_type='student',
            is_deferred=True
        ).first()
        self.assertIsNotNone(deferred_loan)
        self.assertEqual(deferred_loan.creditor_name, 'Navient Student Loans')
        self.assertTrue(deferred_loan.is_deferred)
        self.assertFalse(deferred_loan.is_ibr)
        self.assertEqual(deferred_loan.monthly_payment, Decimal('0.00'))

        # Check IBR student loan
        ibr_loan = credit_report.tradelines.filter(
            account_type='student',
            is_ibr=True
        ).first()
        self.assertIsNotNone(ibr_loan)
        self.assertEqual(ibr_loan.creditor_name, 'FedLoan Servicing')
        self.assertTrue(ibr_loan.is_ibr)
        self.assertFalse(ibr_loan.is_deferred)

    def test_sample_3_cosigned_and_new_accounts(self):
        """
        Sample 3: Profile with cosigned accounts and new tradelines
        - Cosigned auto loan
        - New accounts with <10 payments
        - Disputed tradeline
        - Closed accounts
        """
        credit_data = {
            "report_id": "CR-2025-003",
            "report_date": "2025-11-09",
            "bureau": "merged",
            "scores": {
                "equifax": 690,
                "experian": 685,
                "transunion": 688
            },
            "tradelines": [
                {
                    "creditor_name": "Toyota Financial",
                    "account_number": "****4567",
                    "account_type": "auto",
                    "status": "open",
                    "current_balance": 22000.00,
                    "monthly_payment": 420.00,
                    "credit_limit": None,
                    "opened_date": "2024-02-10",
                    "last_payment_date": "2025-10-05",
                    "days_past_due": 0,
                    "payment_history": {
                        "months_reviewed": 20,
                        "payment_count": 9,
                        "lates_30": [0, 0],
                        "lates_60": [0, 0],
                        "lates_90": [0, 0]
                    },
                    "flags": {
                        "deferred": False,
                        "ibr": False,
                        "cosigned": True,
                        "disputed": False
                    },
                    "remarks": "Co-borrower: Jane Doe"
                },
                {
                    "creditor_name": "Discover Card",
                    "account_number": "****8901",
                    "account_type": "credit_card",
                    "status": "open",
                    "current_balance": 1200.00,
                    "monthly_payment": 50.00,
                    "credit_limit": 5000.00,
                    "opened_date": "2025-04-01",
                    "last_payment_date": "2025-10-20",
                    "days_past_due": 0,
                    "payment_history": {
                        "months_reviewed": 7,
                        "payment_count": 7,
                        "lates_30": [0, 0],
                        "lates_60": [0, 0],
                        "lates_90": [0, 0]
                    },
                    "flags": {
                        "deferred": False,
                        "ibr": False,
                        "cosigned": False,
                        "disputed": False
                    },
                    "remarks": "New account"
                },
                {
                    "creditor_name": "Medical Collection Services",
                    "account_number": "****1122",
                    "account_type": "collection",
                    "status": "collection",
                    "current_balance": 850.00,
                    "monthly_payment": 0.00,
                    "credit_limit": None,
                    "opened_date": "2024-06-15",
                    "last_payment_date": None,
                    "days_past_due": 180,
                    "payment_history": {
                        "months_reviewed": 17,
                        "payment_count": 0,
                        "lates_30": [0, 0],
                        "lates_60": [0, 0],
                        "lates_90": [0, 0]
                    },
                    "flags": {
                        "deferred": False,
                        "ibr": False,
                        "cosigned": False,
                        "disputed": True
                    },
                    "remarks": "Disputed by consumer"
                },
                {
                    "creditor_name": "Capital One",
                    "account_number": "****3344",
                    "account_type": "credit_card",
                    "status": "closed",
                    "current_balance": 0.00,
                    "monthly_payment": 0.00,
                    "credit_limit": 3000.00,
                    "opened_date": "2017-03-15",
                    "last_payment_date": "2024-12-01",
                    "days_past_due": 0,
                    "payment_history": {
                        "months_reviewed": 36,
                        "payment_count": 85,
                        "lates_30": [0, 1],
                        "lates_60": [0, 0],
                        "lates_90": [0, 0]
                    },
                    "flags": {
                        "deferred": False,
                        "ibr": False,
                        "cosigned": False,
                        "disputed": False
                    },
                    "remarks": "Account closed by consumer"
                }
            ],
            "inquiries": [
                {
                    "creditor": "Toyota Financial",
                    "date": "2024-02-05",
                    "type": "hard"
                },
                {
                    "creditor": "Discover Bank",
                    "date": "2025-03-28",
                    "type": "hard"
                }
            ]
        }

        # Parse credit report
        credit_report = parse_credit_report(self.user, credit_data)

        # Assertions
        self.assertEqual(credit_report.total_tradelines, 4)
        self.assertEqual(credit_report.total_inquiries, 2)

        # Check cosigned auto loan
        cosigned_auto = credit_report.tradelines.get(
            account_type='auto',
            is_cosigned=True
        )
        self.assertEqual(cosigned_auto.creditor_name, 'Toyota Financial')
        self.assertTrue(cosigned_auto.is_cosigned)
        self.assertTrue(cosigned_auto.has_less_than_10_payments)
        self.assertEqual(cosigned_auto.payment_count, 9)

        # Check new credit card with <10 payments
        new_card = credit_report.tradelines.get(
            creditor_name='Discover Card'
        )
        self.assertTrue(new_card.has_less_than_10_payments)
        self.assertEqual(new_card.payment_count, 7)

        # Check disputed collection account
        collection = credit_report.tradelines.get(account_type='collection')
        self.assertTrue(collection.is_disputed)
        self.assertEqual(collection.status, 'collection')
        self.assertEqual(collection.days_past_due, 180)

        # Check closed account
        closed = credit_report.tradelines.get(status='closed')
        self.assertEqual(closed.creditor_name, 'Capital One')
        self.assertEqual(closed.current_balance, Decimal('0.00'))
        self.assertEqual(closed.lates_30_count_36mo, 1)

        # Verify only open accounts contribute to monthly debt
        self.assertGreater(credit_report.total_monthly_debt, 0)

    def test_parser_handles_missing_data_gracefully(self):
        """Test that parser handles missing or null fields gracefully."""
        credit_data = {
            "report_id": "CR-2025-004",
            "report_date": "2025-11-09",
            "bureau": "merged",
            "scores": {
                "equifax": 700
                # Missing experian and transunion
            },
            "tradelines": [
                {
                    "creditor_name": "Test Bank",
                    "account_type": "personal",
                    "status": "open",
                    "current_balance": 5000.00,
                    # Missing many optional fields
                    "payment_history": {
                        "payment_count": 15  # More than 10 payments
                    },
                    "flags": {}
                }
            ],
            "inquiries": []
        }

        # Should not raise exception
        credit_report = parse_credit_report(self.user, credit_data)

        self.assertIsNotNone(credit_report)
        self.assertEqual(credit_report.equifax_score, 700)
        self.assertIsNone(credit_report.experian_score)
        self.assertIsNone(credit_report.transunion_score)

        tradeline = credit_report.tradelines.first()
        self.assertEqual(tradeline.lates_30_count_24mo, 0)
        self.assertFalse(tradeline.is_deferred)
        # With payment_count=15, should be False
        self.assertFalse(tradeline.has_less_than_10_payments)
        self.assertEqual(tradeline.payment_count, 15)

    def test_account_number_masking(self):
        """Test that account numbers are properly masked to last 4 digits."""
        credit_data = {
            "report_id": "CR-2025-005",
            "report_date": "2025-11-09",
            "bureau": "merged",
            "scores": {"equifax": 700},
            "tradelines": [
                {
                    "creditor_name": "Test Bank",
                    "account_number": "1234567890",  # Full account number
                    "account_type": "credit_card",
                    "status": "open",
                    "current_balance": 1000.00,
                    "payment_history": {},
                    "flags": {}
                }
            ],
            "inquiries": []
        }

        credit_report = parse_credit_report(self.user, credit_data)
        tradeline = credit_report.tradelines.first()

        # Should only store last 4 digits
        self.assertEqual(tradeline.account_number, '7890')

    def test_account_type_normalization(self):
        """Test that various account type strings are normalized correctly."""
        test_cases = [
            ("MORTGAGE", "mortgage"),
            ("home", "mortgage"),
            ("Auto Loan", "auto"),
            ("credit_card", "credit_card"),
            ("CreditCard", "credit_card"),
            ("Revolving", "credit_card"),
            ("Student Loan", "student"),
            ("Unknown Type", "other"),
        ]

        for input_type, expected_type in test_cases:
            credit_data = {
                "report_id": f"CR-{input_type}",
                "report_date": "2025-11-09",
                "bureau": "merged",
                "scores": {"equifax": 700},
                "tradelines": [
                    {
                        "creditor_name": "Test",
                        "account_type": input_type,
                        "status": "open",
                        "current_balance": 1000.00,
                        "payment_history": {},
                        "flags": {}
                    }
                ],
                "inquiries": []
            }

            credit_report = parse_credit_report(self.user, credit_data)
            tradeline = credit_report.tradelines.first()
            self.assertEqual(
                tradeline.account_type,
                expected_type,
                f"Failed to normalize '{input_type}' to '{expected_type}'"
            )

            # Clean up for next iteration
            credit_report.delete()
