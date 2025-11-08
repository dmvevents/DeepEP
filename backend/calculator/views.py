"""
Calculator API views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from datetime import datetime
import logging

from api.models import County, TaxData, LoanEstimate
from api.serializers import LoanEstimateCreateSerializer, LoanEstimateSerializer
from .engine import MortgageCalculator

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_loan_estimate(request):
    """
    Calculate a loan estimate based on provided parameters

    POST /api/calculate/
    """
    # Validate input data
    serializer = LoanEstimateCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    try:
        # Get county and tax data
        county = County.objects.get(id=data['county_id'], active=True)
        tax_data = county.tax_data.filter(is_current=True).first()

        if not tax_data:
            return Response({
                'error': 'No tax data available for this county',
                'detail': 'Tax data needs to be scraped for this jurisdiction',
                'county': county.name,
                'state': county.state.code
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if tax data is stale
        if tax_data.is_stale:
            logger.warning(f"Using stale tax data for {county.name}, {county.state.code}")
            # Optionally trigger re-scrape here
            from django.conf import settings
            if getattr(settings, 'ENABLE_AUTO_RESCRAPE', True):
                from scraper_integration.tasks import scrape_county_data
                scrape_county_data.delay(county.state.code, county.name)

        # Initialize calculator with tax data
        calculator = MortgageCalculator(tax_data.data)

        # Perform calculation
        calculation_results = calculator.calculate(
            property_value=Decimal(str(data['property_value'])),
            loan_amount=Decimal(str(data['loan_amount'])),
            down_payment=Decimal(str(data['down_payment'])),
            interest_rate=Decimal(str(data['interest_rate'])),
            loan_term_years=data['loan_term_years'],
            closing_date=data['closing_date'],
            loan_type=data['loan_type'],
            property_type=data['property_type'],
            first_time_homebuyer=data['first_time_homebuyer'],
            zip_code=data.get('zip_code')
        )

        # Save the loan estimate if requested
        loan_estimate = None
        if data.get('save_estimate', False):
            loan_estimate = LoanEstimate.objects.create(
                user=request.user,
                property_address=data.get('property_address', ''),
                county=county,
                property_value=data['property_value'],
                property_type=data['property_type'],
                loan_amount=data['loan_amount'],
                down_payment=data['down_payment'],
                interest_rate=data['interest_rate'],
                loan_term_years=data['loan_term_years'],
                loan_type=data['loan_type'],
                first_time_homebuyer=data['first_time_homebuyer'],
                closing_date=data['closing_date'],
                calculation_results=calculation_results,
                tax_data=tax_data,
                is_saved=True,
                name=data.get('estimate_name', f"Estimate {datetime.now().strftime('%Y-%m-%d')}")
            )

        # Build response
        response_data = {
            'calculation': calculation_results,
            'tax_data_info': {
                'version': tax_data.version,
                'last_verified': tax_data.last_verified,
                'is_stale': tax_data.is_stale,
                'data_completeness': tax_data.data_completeness,
                'sources': tax_data.sources
            },
            'county_info': {
                'name': county.name,
                'state': county.state.code,
                'state_name': county.state.name
            }
        }

        if loan_estimate:
            response_data['saved_estimate'] = {
                'id': loan_estimate.id,
                'name': loan_estimate.name
            }

        return Response(response_data, status=status.HTTP_200_OK)

    except County.DoesNotExist:
        return Response({
            'error': 'County not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({
            'error': 'Validation error',
            'detail': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Calculation error: {str(e)}", exc_info=True)
        return Response({
            'error': 'Calculation failed',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_loan_estimate(request, estimate_id):
    """
    Retrieve a saved loan estimate

    GET /api/calculate/{estimate_id}/
    """
    try:
        loan_estimate = LoanEstimate.objects.get(
            id=estimate_id,
            user=request.user
        )

        serializer = LoanEstimateSerializer(loan_estimate)
        return Response(serializer.data)

    except LoanEstimate.DoesNotExist:
        return Response({
            'error': 'Loan estimate not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_loan_estimates(request):
    """
    List all loan estimates for the current user

    GET /api/calculate/
    """
    saved_only = request.query_params.get('saved_only', 'false').lower() == 'true'

    estimates = LoanEstimate.objects.filter(user=request.user)

    if saved_only:
        estimates = estimates.filter(is_saved=True)

    estimates = estimates.order_by('-created_at')

    from api.serializers import LoanEstimateListSerializer
    serializer = LoanEstimateListSerializer(estimates, many=True)

    return Response({
        'count': estimates.count(),
        'results': serializer.data
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_loan_estimate(request, estimate_id):
    """
    Delete a saved loan estimate

    DELETE /api/calculate/{estimate_id}/
    """
    try:
        loan_estimate = LoanEstimate.objects.get(
            id=estimate_id,
            user=request.user
        )

        loan_estimate.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    except LoanEstimate.DoesNotExist:
        return Response({
            'error': 'Loan estimate not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recalculate_estimate(request, estimate_id):
    """
    Recalculate an existing estimate with updated tax data

    POST /api/calculate/{estimate_id}/recalculate/
    """
    try:
        loan_estimate = LoanEstimate.objects.get(
            id=estimate_id,
            user=request.user
        )

        # Get latest tax data
        tax_data = loan_estimate.county.tax_data.filter(is_current=True).first()

        if not tax_data:
            return Response({
                'error': 'No current tax data available'
            }, status=status.HTTP_404_NOT_FOUND)

        # Initialize calculator with updated tax data
        calculator = MortgageCalculator(tax_data.data)

        # Perform calculation
        calculation_results = calculator.calculate(
            property_value=loan_estimate.property_value,
            loan_amount=loan_estimate.loan_amount,
            down_payment=loan_estimate.down_payment,
            interest_rate=loan_estimate.interest_rate,
            loan_term_years=loan_estimate.loan_term_years,
            closing_date=loan_estimate.closing_date,
            loan_type=loan_estimate.loan_type,
            property_type=loan_estimate.property_type,
            first_time_homebuyer=loan_estimate.first_time_homebuyer
        )

        # Update the loan estimate
        loan_estimate.calculation_results = calculation_results
        loan_estimate.tax_data = tax_data
        loan_estimate.save()

        serializer = LoanEstimateSerializer(loan_estimate)
        return Response(serializer.data)

    except LoanEstimate.DoesNotExist:
        return Response({
            'error': 'Loan estimate not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Recalculation error: {str(e)}", exc_info=True)
        return Response({
            'error': 'Recalculation failed',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
