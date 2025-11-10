"""
Pricing Adapter - Phase 3: Scenario Desk

Plug-in adapter interface for investor bot/API pricing with 3 rails logic.
Supports multiple pricing strategies: rate/points/credit combinations.

Author: Backend/Django Engineer
Date: November 10, 2025
"""

from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@dataclass
class LoanParameters:
    """
    Loan parameters for pricing request.
    """
    loan_amount: Decimal
    property_value: Decimal
    credit_score: int
    loan_type: str  # 'conventional', 'fha', 'va', 'usda'
    occupancy: str  # 'primary', 'secondary', 'investment'
    property_type: str  # 'single_family', 'condo', 'townhouse', 'multi_family'
    loan_term_months: int  # 360, 180, etc.
    loan_purpose: str  # 'purchase', 'refinance', 'cash_out'
    documentation_type: str  # 'full_doc', 'alt_doc', 'no_doc'

    # Optional fields
    state: Optional[str] = None
    county: Optional[str] = None
    zip_code: Optional[str] = None
    debt_to_income_ratio: Optional[Decimal] = None

    @property
    def ltv_ratio(self) -> Decimal:
        """Calculate loan-to-value ratio"""
        if self.property_value > 0:
            return (self.loan_amount / self.property_value * 100).quantize(
                Decimal('0.01'), ROUND_HALF_UP
            )
        return Decimal('0')


@dataclass
class PricingOption:
    """
    Single pricing option with rate, points, and credit.

    The "3 rails" are:
    1. Rate: Interest rate (APR)
    2. Points: Origination points (discount/premium)
    3. Credit: Lender credit (negative points)
    """
    rate: Decimal  # Annual percentage rate (e.g., 6.750)
    points: Decimal  # Origination points (e.g., 1.0 = 1% of loan amount)
    credit: Decimal  # Lender credit in dollars (negative = cost to borrower)

    # Additional metadata
    lock_days: int = 30  # Rate lock period
    program_name: str = ""  # e.g., "30-Year Fixed Conventional"
    investor_name: str = ""  # e.g., "Fannie Mae", "Freddie Mac"
    notes: str = ""

    # Pricing adjustments breakdown
    adjustments: Dict[str, Decimal] = None

    def __post_init__(self):
        if self.adjustments is None:
            self.adjustments = {}

    @property
    def effective_rate(self) -> Decimal:
        """
        Calculate effective rate including points/credit impact.
        This is simplified - actual APR calculation is more complex.
        """
        # Rough approximation: 0.25% rate for every 1% point
        adjustment = self.points * Decimal('0.25')
        return (self.rate - adjustment).quantize(Decimal('0.001'), ROUND_HALF_UP)

    @property
    def net_cost(self) -> Decimal:
        """
        Calculate net cost/credit to borrower.
        Positive = cost, Negative = credit
        """
        return self.points - self.credit

    def get_upfront_cost(self, loan_amount: Decimal) -> Decimal:
        """
        Calculate total upfront cost in dollars.

        Args:
            loan_amount: Loan amount in dollars

        Returns:
            Total upfront cost (points - credit) in dollars
        """
        points_cost = (loan_amount * self.points / 100).quantize(
            Decimal('0.01'), ROUND_HALF_UP
        )
        return points_cost - self.credit


@dataclass
class PricingResponse:
    """
    Response from pricing adapter containing multiple options.
    """
    options: List[PricingOption]
    loan_parameters: LoanParameters
    timestamp: datetime
    provider: str  # Adapter name (e.g., "OptimalBlue", "MockInvestor")

    # Metadata
    request_id: str = ""
    execution_time_ms: int = 0
    error: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    def get_best_rate_option(self) -> Optional[PricingOption]:
        """Get option with lowest rate"""
        if not self.options:
            return None
        return min(self.options, key=lambda x: x.rate)

    def get_zero_cost_option(self) -> Optional[PricingOption]:
        """Get option closest to zero net cost"""
        if not self.options:
            return None
        return min(self.options, key=lambda x: abs(x.net_cost))

    def get_max_credit_option(self) -> Optional[PricingOption]:
        """Get option with maximum lender credit"""
        if not self.options:
            return None
        return max(self.options, key=lambda x: x.credit)


class PricingAdapter(ABC):
    """
    Abstract base class for pricing adapters.

    Implement this interface to connect to different investor pricing engines:
    - OptimalBlue API
    - Encompass LO Connect
    - Custom investor bots
    - Mock pricing engines (for testing)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout_seconds: int = 30,
        **kwargs
    ):
        """
        Initialize pricing adapter.

        Args:
            api_key: API authentication key
            api_url: Base URL for pricing API
            timeout_seconds: Request timeout
            **kwargs: Additional adapter-specific configuration
        """
        self.api_key = api_key or getattr(settings, 'PRICING_API_KEY', '')
        self.api_url = api_url or getattr(settings, 'PRICING_API_URL', '')
        self.timeout_seconds = timeout_seconds
        self.config = kwargs

        logger.debug(f"{self.__class__.__name__} initialized: url={self.api_url}")

    @abstractmethod
    def get_pricing(self, loan_params: LoanParameters) -> PricingResponse:
        """
        Get pricing options for loan parameters.

        Args:
            loan_params: Loan parameters for pricing

        Returns:
            PricingResponse with multiple pricing options

        Raises:
            PricingError: If pricing request fails
        """
        pass

    @abstractmethod
    def validate_parameters(self, loan_params: LoanParameters) -> Tuple[bool, List[str]]:
        """
        Validate loan parameters before requesting pricing.

        Args:
            loan_params: Loan parameters to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        pass

    def get_adapter_info(self) -> Dict:
        """
        Get adapter metadata for logging/auditing.

        Returns:
            Dict with adapter name, version, configuration
        """
        return {
            'adapter_name': self.__class__.__name__,
            'api_url': self.api_url,
            'timeout_seconds': self.timeout_seconds,
            'config': self.config,
        }


class PricingError(Exception):
    """
    Exception raised when pricing request fails.
    """
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class MockPricingAdapter(PricingAdapter):
    """
    Mock pricing adapter for testing.

    Generates realistic pricing options using simplified logic:
    - Base rate from market rates
    - Points/credit variations (-2.0 to +2.0)
    - Adjustments for credit score, LTV, loan type
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Mock market base rates (from settings or defaults)
        self.base_rates = {
            'conventional_30yr': Decimal('6.750'),
            'conventional_15yr': Decimal('6.125'),
            'fha_30yr': Decimal('6.500'),
            'va_30yr': Decimal('6.375'),
            'usda_30yr': Decimal('6.625'),
        }

    def get_pricing(self, loan_params: LoanParameters) -> PricingResponse:
        """
        Generate mock pricing options.

        Creates 5-7 pricing options with different rate/points/credit combinations.
        """
        start_time = datetime.now()

        # Validate parameters
        is_valid, errors = self.validate_parameters(loan_params)
        if not is_valid:
            return PricingResponse(
                options=[],
                loan_parameters=loan_params,
                timestamp=datetime.now(),
                provider="MockInvestor",
                error="; ".join(errors),
            )

        try:
            # Get base rate
            base_rate = self._get_base_rate(loan_params)

            # Apply adjustments
            adjusted_rate = self._apply_adjustments(base_rate, loan_params)

            # Generate pricing options (3 rails)
            options = self._generate_pricing_options(adjusted_rate, loan_params)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                f"Mock pricing generated: {len(options)} options, "
                f"base_rate={base_rate}, adjusted_rate={adjusted_rate}"
            )

            return PricingResponse(
                options=options,
                loan_parameters=loan_params,
                timestamp=datetime.now(),
                provider="MockInvestor",
                execution_time_ms=int(execution_time),
            )

        except Exception as e:
            logger.error(f"Error generating mock pricing: {e}", exc_info=True)
            return PricingResponse(
                options=[],
                loan_parameters=loan_params,
                timestamp=datetime.now(),
                provider="MockInvestor",
                error=str(e),
            )

    def validate_parameters(self, loan_params: LoanParameters) -> Tuple[bool, List[str]]:
        """
        Validate loan parameters.
        """
        errors = []

        if loan_params.loan_amount <= 0:
            errors.append("Loan amount must be positive")

        if loan_params.property_value <= 0:
            errors.append("Property value must be positive")

        if loan_params.credit_score < 300 or loan_params.credit_score > 850:
            errors.append("Credit score must be between 300 and 850")

        if loan_params.ltv_ratio > 97:
            errors.append("LTV ratio exceeds maximum (97%)")

        if loan_params.loan_type not in ['conventional', 'fha', 'va', 'usda']:
            errors.append(f"Invalid loan type: {loan_params.loan_type}")

        if loan_params.loan_term_months not in [180, 360]:
            errors.append(f"Unsupported loan term: {loan_params.loan_term_months} months")

        return (len(errors) == 0, errors)

    def _get_base_rate(self, loan_params: LoanParameters) -> Decimal:
        """
        Get base rate for loan type and term.
        """
        term_years = loan_params.loan_term_months // 12
        key = f"{loan_params.loan_type}_{term_years}yr"

        return self.base_rates.get(key, self.base_rates['conventional_30yr'])

    def _apply_adjustments(self, base_rate: Decimal, loan_params: LoanParameters) -> Decimal:
        """
        Apply pricing adjustments (LLPAs) based on risk factors.

        Adjustments for:
        - Credit score
        - LTV ratio
        - Property type
        - Occupancy
        - Loan purpose
        """
        adjustment = Decimal('0')

        # Credit score adjustment
        if loan_params.credit_score < 620:
            adjustment += Decimal('1.500')
        elif loan_params.credit_score < 640:
            adjustment += Decimal('1.000')
        elif loan_params.credit_score < 660:
            adjustment += Decimal('0.750')
        elif loan_params.credit_score < 680:
            adjustment += Decimal('0.500')
        elif loan_params.credit_score < 700:
            adjustment += Decimal('0.250')
        elif loan_params.credit_score >= 760:
            adjustment -= Decimal('0.125')

        # LTV adjustment
        ltv = loan_params.ltv_ratio
        if ltv > 95:
            adjustment += Decimal('0.750')
        elif ltv > 90:
            adjustment += Decimal('0.500')
        elif ltv > 85:
            adjustment += Decimal('0.250')
        elif ltv <= 60:
            adjustment -= Decimal('0.125')

        # Occupancy adjustment
        if loan_params.occupancy == 'secondary':
            adjustment += Decimal('0.500')
        elif loan_params.occupancy == 'investment':
            adjustment += Decimal('1.000')

        # Property type adjustment
        if loan_params.property_type in ['condo', 'multi_family']:
            adjustment += Decimal('0.250')

        # Loan purpose adjustment
        if loan_params.loan_purpose == 'cash_out':
            adjustment += Decimal('0.375')

        return (base_rate + adjustment).quantize(Decimal('0.001'), ROUND_HALF_UP)

    def _generate_pricing_options(
        self,
        adjusted_rate: Decimal,
        loan_params: LoanParameters
    ) -> List[PricingOption]:
        """
        Generate pricing options with different rate/points/credit combinations.

        Creates 7 options:
        1. Best rate (highest points)
        2. Low points option
        3. Par rate (zero points)
        4. Low credit option
        5. Zero cost option
        6. High credit (higher rate)
        7. Max credit option
        """
        options = []
        loan_amount = loan_params.loan_amount

        # Option 1: Best rate (pay 2 points)
        options.append(PricingOption(
            rate=adjusted_rate - Decimal('0.500'),
            points=Decimal('2.000'),
            credit=Decimal('0'),
            lock_days=30,
            program_name=f"{loan_params.loan_term_months // 12}-Year Fixed {loan_params.loan_type.title()}",
            investor_name="MockInvestor",
            notes="Best rate - highest upfront cost",
        ))

        # Option 2: Low points (pay 1 point)
        options.append(PricingOption(
            rate=adjusted_rate - Decimal('0.250'),
            points=Decimal('1.000'),
            credit=Decimal('0'),
            lock_days=30,
            program_name=f"{loan_params.loan_term_months // 12}-Year Fixed {loan_params.loan_type.title()}",
            investor_name="MockInvestor",
            notes="Low points option",
        ))

        # Option 3: Par rate (zero points/credit)
        options.append(PricingOption(
            rate=adjusted_rate,
            points=Decimal('0.000'),
            credit=Decimal('0'),
            lock_days=30,
            program_name=f"{loan_params.loan_term_months // 12}-Year Fixed {loan_params.loan_type.title()}",
            investor_name="MockInvestor",
            notes="Par rate - no points or credits",
        ))

        # Option 4: Small credit (0.5% rate increase)
        credit_amt_4 = (loan_amount * Decimal('0.005')).quantize(Decimal('0.01'), ROUND_HALF_UP)
        options.append(PricingOption(
            rate=adjusted_rate + Decimal('0.125'),
            points=Decimal('0.000'),
            credit=credit_amt_4,
            lock_days=30,
            program_name=f"{loan_params.loan_term_months // 12}-Year Fixed {loan_params.loan_type.title()}",
            investor_name="MockInvestor",
            notes="Small lender credit",
        ))

        # Option 5: Zero cost (moderate credit)
        credit_amt_5 = (loan_amount * Decimal('0.010')).quantize(Decimal('0.01'), ROUND_HALF_UP)
        options.append(PricingOption(
            rate=adjusted_rate + Decimal('0.250'),
            points=Decimal('0.000'),
            credit=credit_amt_5,
            lock_days=30,
            program_name=f"{loan_params.loan_term_months // 12}-Year Fixed {loan_params.loan_type.title()}",
            investor_name="MockInvestor",
            notes="Zero closing cost option",
        ))

        # Option 6: High credit (1% rate increase)
        credit_amt_6 = (loan_amount * Decimal('0.015')).quantize(Decimal('0.01'), ROUND_HALF_UP)
        options.append(PricingOption(
            rate=adjusted_rate + Decimal('0.375'),
            points=Decimal('0.000'),
            credit=credit_amt_6,
            lock_days=30,
            program_name=f"{loan_params.loan_term_months // 12}-Year Fixed {loan_params.loan_type.title()}",
            investor_name="MockInvestor",
            notes="High lender credit",
        ))

        # Option 7: Max credit (1.5% rate increase)
        credit_amt_7 = (loan_amount * Decimal('0.020')).quantize(Decimal('0.01'), ROUND_HALF_UP)
        options.append(PricingOption(
            rate=adjusted_rate + Decimal('0.500'),
            points=Decimal('0.000'),
            credit=credit_amt_7,
            lock_days=30,
            program_name=f"{loan_params.loan_term_months // 12}-Year Fixed {loan_params.loan_type.title()}",
            investor_name="MockInvestor",
            notes="Maximum lender credit",
        ))

        return options


class PricingService:
    """
    Service for managing pricing adapters and caching results.

    Supports multiple adapters with fallback logic.
    """

    def __init__(self, primary_adapter: PricingAdapter, fallback_adapter: Optional[PricingAdapter] = None):
        """
        Initialize pricing service.

        Args:
            primary_adapter: Primary pricing adapter
            fallback_adapter: Optional fallback adapter if primary fails
        """
        self.primary_adapter = primary_adapter
        self.fallback_adapter = fallback_adapter

        logger.info(
            f"PricingService initialized: primary={primary_adapter.__class__.__name__}, "
            f"fallback={fallback_adapter.__class__.__name__ if fallback_adapter else None}"
        )

    def get_pricing(self, loan_params: LoanParameters, use_cache: bool = True) -> PricingResponse:
        """
        Get pricing with fallback logic.

        Args:
            loan_params: Loan parameters
            use_cache: Whether to use cached results (not implemented yet)

        Returns:
            PricingResponse
        """
        try:
            # Try primary adapter
            response = self.primary_adapter.get_pricing(loan_params)

            if response.error:
                logger.warning(f"Primary adapter returned error: {response.error}")
                if self.fallback_adapter:
                    logger.info("Attempting fallback adapter")
                    return self.fallback_adapter.get_pricing(loan_params)

            return response

        except Exception as e:
            logger.error(f"Primary adapter failed: {e}", exc_info=True)

            if self.fallback_adapter:
                logger.info("Attempting fallback adapter")
                try:
                    return self.fallback_adapter.get_pricing(loan_params)
                except Exception as fallback_error:
                    logger.error(f"Fallback adapter failed: {fallback_error}", exc_info=True)
                    raise PricingError(
                        "Both primary and fallback adapters failed",
                        code="ADAPTER_FAILURE",
                        details={'primary_error': str(e), 'fallback_error': str(fallback_error)}
                    )

            raise PricingError(str(e), code="ADAPTER_FAILURE")
