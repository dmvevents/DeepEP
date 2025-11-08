"""
Property Lookup API Endpoints

FastAPI endpoints for property address lookup and data retrieval.
Connects frontend to PropertyLookupService.

Created by: Neumann Rashid AI Development
Date: November 8, 2025
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from decimal import Decimal
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from property_lookup.property_service import PropertyLookupService


# Initialize FastAPI app
app = FastAPI(
    title="Property Lookup API",
    description="API for property address lookup and tax data retrieval",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize PropertyLookupService
property_service = PropertyLookupService(
    tax_scraper_url="http://localhost:8001",
    geocoding_api_key=None,  # Add if using external geocoding
    property_api_key=None     # Add if using external property API
)


# Pydantic models for request/response
class PropertyLookupRequest(BaseModel):
    """Request model for property lookup"""
    address: str = Field(..., description="Full property address", min_length=10)


class PropertyAddressResponse(BaseModel):
    """Property address details"""
    street_address: str
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    county: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    formatted_address: Optional[str]


class PropertyDataResponse(BaseModel):
    """Complete property data response"""
    address: PropertyAddressResponse
    estimated_value: Optional[float]
    tax_assessment_value: Optional[float]
    annual_property_tax: Optional[float]
    monthly_property_tax: Optional[float]
    property_type: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    square_feet: Optional[int]
    year_built: Optional[int]

    # Tax and fee data
    tax_rate: Optional[float]
    transfer_tax_rate: Optional[float]
    recordation_tax_rate: Optional[float]
    recording_fees: Optional[Dict[str, Any]]
    insurance_estimate: Optional[float]

    # Metadata
    data_source: Optional[str]
    confidence_score: Optional[int]
    last_updated: Optional[str]


class PropertyTaxCalculationRequest(BaseModel):
    """Request model for property tax calculation"""
    property_value: float = Field(..., description="Property value", gt=0)
    state: Optional[str] = Field(None, description="State code (e.g., MD)")
    county: Optional[str] = Field(None, description="County name")
    tax_rate: Optional[float] = Field(None, description="Annual tax rate (if known)")


class PropertyTaxCalculationResponse(BaseModel):
    """Response model for property tax calculation"""
    property_value: float
    annual_tax_rate: float
    annual_property_tax: float
    monthly_property_tax: float
    state: Optional[str]
    county: Optional[str]


class InsuranceEstimateRequest(BaseModel):
    """Request model for insurance estimation"""
    property_value: float = Field(..., description="Property value", gt=0)
    state: Optional[str] = Field(None, description="State code")
    county: Optional[str] = Field(None, description="County name")


class InsuranceEstimateResponse(BaseModel):
    """Response model for insurance estimation"""
    property_value: float
    annual_premium: float
    monthly_premium: float
    rate_per_100k: float
    state: Optional[str]
    county: Optional[str]


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Property Lookup API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "lookup": "/api/property/lookup",
            "calculate_tax": "/api/property/calculate-tax",
            "estimate_insurance": "/api/property/estimate-insurance",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "property-lookup-api",
        "dependencies": {
            "tax_scraper": "http://localhost:8001",
            "geocoding": "internal",
        }
    }


@app.post("/api/property/lookup", response_model=PropertyDataResponse)
async def lookup_property(request: PropertyLookupRequest):
    """
    Look up property by address.

    Returns complete property information including:
    - Address details (county, coordinates)
    - Tax rates and estimates
    - Recording fees
    - Insurance estimates

    Example:
    ```
    POST /api/property/lookup
    {
        "address": "123 Main Street, Rockville, MD 20850"
    }
    ```
    """
    try:
        # Call property lookup service
        property_data = property_service.lookup_property(request.address)

        # Convert to response model
        response = PropertyDataResponse(
            address=PropertyAddressResponse(
                street_address=property_data.address.street_address,
                city=property_data.address.city,
                state=property_data.address.state,
                zip_code=property_data.address.zip_code,
                county=property_data.address.county,
                latitude=property_data.address.latitude,
                longitude=property_data.address.longitude,
                formatted_address=property_data.address.formatted_address
            ),
            estimated_value=float(property_data.estimated_value) if property_data.estimated_value else None,
            tax_assessment_value=float(property_data.tax_assessment_value) if property_data.tax_assessment_value else None,
            annual_property_tax=float(property_data.annual_property_tax) if property_data.annual_property_tax else None,
            monthly_property_tax=float(property_data.monthly_property_tax) if property_data.monthly_property_tax else None,
            property_type=property_data.property_type,
            bedrooms=property_data.bedrooms,
            bathrooms=property_data.bathrooms,
            square_feet=property_data.square_feet,
            year_built=property_data.year_built,
            tax_rate=float(property_data.tax_rate) if property_data.tax_rate else None,
            transfer_tax_rate=float(property_data.transfer_tax_rate) if property_data.transfer_tax_rate else None,
            recordation_tax_rate=float(property_data.recordation_tax_rate) if property_data.recordation_tax_rate else None,
            recording_fees=property_data.recording_fees,
            insurance_estimate=float(property_data.insurance_estimate) if property_data.insurance_estimate else None,
            data_source=property_data.data_source,
            confidence_score=property_data.confidence_score,
            last_updated=property_data.last_updated
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Property lookup failed: {str(e)}")


@app.get("/api/property/lookup")
async def lookup_property_get(
    address: str = Query(..., description="Property address", min_length=10)
):
    """
    Look up property by address (GET method).

    Example:
    ```
    GET /api/property/lookup?address=123%20Main%20St,%20Rockville,%20MD%2020850
    ```
    """
    request = PropertyLookupRequest(address=address)
    return await lookup_property(request)


@app.post("/api/property/calculate-tax", response_model=PropertyTaxCalculationResponse)
async def calculate_property_tax(request: PropertyTaxCalculationRequest):
    """
    Calculate monthly property tax.

    Example:
    ```
    POST /api/property/calculate-tax
    {
        "property_value": 500000,
        "state": "MD",
        "county": "Montgomery"
    }
    ```
    """
    try:
        monthly_tax = property_service.calculate_monthly_property_tax(
            property_value=Decimal(str(request.property_value)),
            tax_rate=Decimal(str(request.tax_rate)) if request.tax_rate else None,
            state=request.state,
            county=request.county
        )

        # Get tax rate for response
        if request.tax_rate:
            tax_rate = request.tax_rate
        else:
            # Fetch from database
            tax_data = property_service._get_tax_data(request.state, request.county)
            if tax_data and 'property_tax' in tax_data:
                tax_rate = float(tax_data['property_tax'].get('total_rate', 0.012))
            else:
                tax_rate = 0.012  # Default 1.2%

        annual_tax = float(monthly_tax) * 12

        return PropertyTaxCalculationResponse(
            property_value=request.property_value,
            annual_tax_rate=tax_rate,
            annual_property_tax=annual_tax,
            monthly_property_tax=float(monthly_tax),
            state=request.state,
            county=request.county
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tax calculation failed: {str(e)}")


@app.post("/api/property/estimate-insurance", response_model=InsuranceEstimateResponse)
async def estimate_insurance(request: InsuranceEstimateRequest):
    """
    Estimate monthly homeowners insurance.

    Example:
    ```
    POST /api/property/estimate-insurance
    {
        "property_value": 500000,
        "state": "MD",
        "county": "Montgomery"
    }
    ```
    """
    try:
        monthly_insurance = property_service.estimate_insurance(
            property_value=Decimal(str(request.property_value)),
            state=request.state,
            county=request.county
        )

        annual_premium = float(monthly_insurance) * 12
        rate_per_100k = (annual_premium / request.property_value) * 100000

        return InsuranceEstimateResponse(
            property_value=request.property_value,
            annual_premium=annual_premium,
            monthly_premium=float(monthly_insurance),
            rate_per_100k=rate_per_100k,
            state=request.state,
            county=request.county
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insurance estimation failed: {str(e)}")


# Development server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "property_api:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    )
