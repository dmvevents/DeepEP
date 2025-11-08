"""
OCR Service - Document Extraction for Mortgage Applications

Extracts structured data from mortgage documents:
- Pay stubs
- W-2 forms
- Bank statements
- Tax returns (1040, Schedule C)

Uses OLLAMA with vision models (Granite3.2-vision, Llama 3.2 Vision)

Created by: Neumann Rashid AI Development
Date: November 8, 2025
"""

import os
import json
import base64
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import ollama
from PIL import Image
import io
from loguru import logger

# Initialize FastAPI app
app = FastAPI(
    title="Mortgage Document OCR Service",
    description="Extract structured data from mortgage documents using vision models",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
PRIMARY_MODEL = os.getenv("OCR_PRIMARY_MODEL", "granite3.2-vision")
FALLBACK_MODEL = os.getenv("OCR_FALLBACK_MODEL", "llama3.2-vision:11b")
CONFIDENCE_THRESHOLD = int(os.getenv("CONFIDENCE_THRESHOLD", "70"))

# Configure logger
logger.add("logs/ocr_service.log", rotation="100 MB", retention="30 days")


# Response Models
class ExtractionResult(BaseModel):
    """Base model for extraction results"""
    success: bool
    document_type: str
    extracted_data: Dict
    confidence_score: int = Field(ge=0, le=100)
    model_used: str
    processing_time_ms: float
    warnings: List[str] = []
    raw_text: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    models_available: List[str]
    timestamp: str


# Utility Functions
def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


async def extract_with_ollama(
    image_bytes: bytes,
    document_type: str,
    extraction_prompt: str,
    model: str = PRIMARY_MODEL
) -> Dict:
    """
    Extract data from document using OLLAMA vision model.

    Args:
        image_bytes: Image data as bytes
        document_type: Type of document (paystub, w2, etc.)
        extraction_prompt: Prompt for extraction
        model: OLLAMA model to use

    Returns:
        Dict with extracted data
    """
    start_time = datetime.now()

    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Save temporarily
        temp_path = f"/tmp/{document_type}_{datetime.now().timestamp()}.png"
        image.save(temp_path)

        # Call OLLAMA with vision model
        response = ollama.chat(
            model=model,
            messages=[{
                'role': 'user',
                'content': extraction_prompt,
                'images': [temp_path]
            }]
        )

        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)

        # Parse response
        response_text = response['message']['content']

        # Try to extract JSON from response
        try:
            # Look for JSON in markdown code blocks
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_str = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                # Try to find JSON object in the text
                json_str = response_text.strip()
                # If it starts with text before {, try to extract just the JSON
                if '{' in json_str:
                    json_start_idx = json_str.find('{')
                    json_end_idx = json_str.rfind('}') + 1
                    json_str = json_str[json_start_idx:json_end_idx]

            extracted_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from response: {e}, using raw text")
            # Create a more useful fallback that includes partial data
            extracted_data = {
                "raw_response": response_text,
                "parsing_error": str(e),
                "_note": "Could not parse structured JSON - manual review needed"
            }

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "success": True,
            "extracted_data": extracted_data,
            "model_used": model,
            "processing_time_ms": processing_time,
            "raw_text": response_text
        }

    except Exception as e:
        logger.error(f"Extraction failed with {model}: {str(e)}")
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "success": False,
            "error": str(e),
            "model_used": model,
            "processing_time_ms": processing_time
        }


def calculate_confidence_score(extracted_data: Dict, document_type: str) -> int:
    """
    Calculate confidence score based on completeness of extracted data.

    Args:
        extracted_data: Extracted data dictionary
        document_type: Type of document

    Returns:
        Confidence score (0-100)
    """
    # If we fell back to raw_response, give it 30% confidence
    if 'raw_response' in extracted_data and 'parsing_error' in extracted_data:
        # Check if raw response has substantial content
        raw_text = extracted_data.get('raw_response', '')
        if len(raw_text) > 100:  # Has some meaningful content
            return 30
        else:
            return 10

    required_fields = {
        'paystub': ['employee_name', 'gross_income_current', 'pay_period_start', 'pay_period_end'],
        'w2': ['employee_name', 'tax_year', 'box_1_wages'],
        'bank_statement': ['account_holder', 'statement_period_start', 'ending_balance'],
        'tax_return': ['taxpayer_name', 'tax_year', 'adjusted_gross_income'],
        'schedule_c': ['business_name', 'tax_year', 'net_profit_loss'],
    }

    fields = required_fields.get(document_type, [])
    if not fields:
        return 50  # Unknown document type

    # Count how many required fields are present and non-empty
    present_fields = 0
    for field in fields:
        # Handle nested fields (like pay_period_start)
        if field in extracted_data:
            value = extracted_data[field]
            # Check if value is not None, not empty string, not 0
            if value and value != "" and value != 0:
                present_fields += 1

    # Calculate percentage
    if len(fields) == 0:
        return 50

    confidence = int((present_fields / len(fields)) * 100)

    return confidence


# Extraction Prompts
PAYSTUB_PROMPT = """
Extract the following information from this pay stub and return ONLY a JSON object:

{
  "employee_name": "Full name of employee",
  "employer_name": "Name of employer/company",
  "pay_period_start": "Start date (YYYY-MM-DD)",
  "pay_period_end": "End date (YYYY-MM-DD)",
  "pay_date": "Payment date (YYYY-MM-DD)",
  "gross_income_current": 0.00,
  "gross_income_ytd": 0.00,
  "hourly_rate": 0.00,
  "hours_worked": 0.0,
  "overtime_hours": 0.0,
  "overtime_pay": 0.00,
  "deductions": {
    "federal_tax_current": 0.00,
    "federal_tax_ytd": 0.00,
    "state_tax_current": 0.00,
    "state_tax_ytd": 0.00,
    "fica_current": 0.00,
    "fica_ytd": 0.00,
    "medicare_current": 0.00,
    "medicare_ytd": 0.00,
    "health_insurance": 0.00,
    "retirement_401k": 0.00
  },
  "net_pay": 0.00
}

Extract all numerical values accurately. Use 0 or empty string for missing fields.
"""

W2_PROMPT = """
Extract the following information from this W-2 form and return ONLY a JSON object:

{
  "employee_name": "Employee full name",
  "employee_ssn": "Last 4 digits only",
  "employer_name": "Employer name",
  "employer_ein": "Employer ID",
  "employer_address": "Full address",
  "tax_year": 2024,
  "box_1_wages": 0.00,
  "box_2_federal_tax": 0.00,
  "box_3_ss_wages": 0.00,
  "box_4_ss_tax": 0.00,
  "box_5_medicare_wages": 0.00,
  "box_6_medicare_tax": 0.00,
  "box_12_codes": [
    {"code": "D", "amount": 0.00}
  ],
  "box_14_other": [
    {"description": "", "amount": 0.00}
  ],
  "state_wages": 0.00,
  "state_tax": 0.00,
  "state": "XX"
}

Extract all box values accurately. Use 0 for missing numerical values.
"""

BANK_STATEMENT_PROMPT = """
Extract the following information from this bank statement and return ONLY a JSON object:

{
  "account_holder": "Account holder name",
  "account_number_last4": "Last 4 digits",
  "bank_name": "Bank name",
  "statement_period_start": "Start date (YYYY-MM-DD)",
  "statement_period_end": "End date (YYYY-MM-DD)",
  "beginning_balance": 0.00,
  "ending_balance": 0.00,
  "total_deposits": 0.00,
  "total_withdrawals": 0.00,
  "deposits": [
    {"date": "YYYY-MM-DD", "description": "", "amount": 0.00}
  ],
  "withdrawals": [
    {"date": "YYYY-MM-DD", "description": "", "amount": 0.00}
  ]
}

Extract balances and major transactions. Use 0 for missing values.
"""

TAX_RETURN_PROMPT = """
Extract the following information from this tax return (Form 1040) and return ONLY a JSON object:

{
  "tax_year": 2023,
  "taxpayer_name": "Primary taxpayer name",
  "spouse_name": "Spouse name if joint",
  "filing_status": "Single/Married Filing Jointly/etc",
  "ssn_last4": "Last 4 digits",
  "address": "Full address",
  "wages_line1": 0.00,
  "taxable_interest": 0.00,
  "business_income": 0.00,
  "capital_gains": 0.00,
  "adjusted_gross_income": 0.00,
  "standard_deduction": 0.00,
  "taxable_income": 0.00,
  "total_tax": 0.00,
  "federal_tax_withheld": 0.00,
  "refund_amount": 0.00,
  "schedules_attached": ["Schedule C", "Schedule E"]
}

Extract all line items from Form 1040. Use 0 for missing values.
"""

SCHEDULE_C_PROMPT = """
Extract the following information from this Schedule C (Self-Employment) and return ONLY a JSON object:

{
  "tax_year": 2023,
  "business_name": "Business name",
  "business_code": "Code",
  "business_address": "Address",
  "accounting_method": "Cash/Accrual",
  "gross_receipts": 0.00,
  "returns_and_allowances": 0.00,
  "cost_of_goods_sold": 0.00,
  "gross_profit": 0.00,
  "expenses": {
    "advertising": 0.00,
    "car_and_truck": 0.00,
    "depreciation": 0.00,
    "insurance": 0.00,
    "interest": 0.00,
    "legal_professional": 0.00,
    "office_expense": 0.00,
    "rent_lease": 0.00,
    "repairs_maintenance": 0.00,
    "supplies": 0.00,
    "taxes_licenses": 0.00,
    "travel": 0.00,
    "meals": 0.00,
    "utilities": 0.00,
    "wages": 0.00,
    "other": 0.00
  },
  "total_expenses": 0.00,
  "net_profit_loss": 0.00
}

Extract all expense categories. Use 0 for missing values.
"""


# API Endpoints

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check available models
        models = ollama.list()
        model_names = [model['name'] for model in models.get('models', [])]

        return HealthResponse(
            status="healthy",
            models_available=model_names,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.post("/extract/paystub", response_model=ExtractionResult)
async def extract_paystub(file: UploadFile = File(...)):
    """Extract data from pay stub"""
    try:
        # Read file
        contents = await file.read()

        # Extract with primary model
        result = await extract_with_ollama(
            contents,
            "paystub",
            PAYSTUB_PROMPT,
            PRIMARY_MODEL
        )

        # Try fallback if primary failed
        if not result["success"]:
            logger.info(f"Primary model failed, trying fallback: {FALLBACK_MODEL}")
            result = await extract_with_ollama(
                contents,
                "paystub",
                PAYSTUB_PROMPT,
                FALLBACK_MODEL
            )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Extraction failed"))

        # Calculate confidence
        confidence = calculate_confidence_score(result["extracted_data"], "paystub")

        return ExtractionResult(
            success=True,
            document_type="paystub",
            extracted_data=result["extracted_data"],
            confidence_score=confidence,
            model_used=result["model_used"],
            processing_time_ms=result["processing_time_ms"],
            warnings=["Low confidence" if confidence < CONFIDENCE_THRESHOLD else ""],
            raw_text=result.get("raw_text")
        )

    except Exception as e:
        logger.error(f"Paystub extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract/w2", response_model=ExtractionResult)
async def extract_w2(file: UploadFile = File(...)):
    """Extract data from W-2 form"""
    try:
        contents = await file.read()

        result = await extract_with_ollama(
            contents,
            "w2",
            W2_PROMPT,
            PRIMARY_MODEL
        )

        if not result["success"]:
            result = await extract_with_ollama(
                contents,
                "w2",
                W2_PROMPT,
                FALLBACK_MODEL
            )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Extraction failed"))

        confidence = calculate_confidence_score(result["extracted_data"], "w2")

        return ExtractionResult(
            success=True,
            document_type="w2",
            extracted_data=result["extracted_data"],
            confidence_score=confidence,
            model_used=result["model_used"],
            processing_time_ms=result["processing_time_ms"],
            warnings=["Low confidence" if confidence < CONFIDENCE_THRESHOLD else ""],
            raw_text=result.get("raw_text")
        )

    except Exception as e:
        logger.error(f"W-2 extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract/bank-statement", response_model=ExtractionResult)
async def extract_bank_statement(file: UploadFile = File(...)):
    """Extract data from bank statement"""
    try:
        contents = await file.read()

        result = await extract_with_ollama(
            contents,
            "bank_statement",
            BANK_STATEMENT_PROMPT,
            PRIMARY_MODEL
        )

        if not result["success"]:
            result = await extract_with_ollama(
                contents,
                "bank_statement",
                BANK_STATEMENT_PROMPT,
                FALLBACK_MODEL
            )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Extraction failed"))

        confidence = calculate_confidence_score(result["extracted_data"], "bank_statement")

        return ExtractionResult(
            success=True,
            document_type="bank_statement",
            extracted_data=result["extracted_data"],
            confidence_score=confidence,
            model_used=result["model_used"],
            processing_time_ms=result["processing_time_ms"],
            warnings=["Low confidence" if confidence < CONFIDENCE_THRESHOLD else ""],
            raw_text=result.get("raw_text")
        )

    except Exception as e:
        logger.error(f"Bank statement extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract/tax-return", response_model=ExtractionResult)
async def extract_tax_return(file: UploadFile = File(...)):
    """Extract data from tax return (Form 1040)"""
    try:
        contents = await file.read()

        result = await extract_with_ollama(
            contents,
            "tax_return",
            TAX_RETURN_PROMPT,
            PRIMARY_MODEL
        )

        if not result["success"]:
            result = await extract_with_ollama(
                contents,
                "tax_return",
                TAX_RETURN_PROMPT,
                FALLBACK_MODEL
            )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Extraction failed"))

        confidence = calculate_confidence_score(result["extracted_data"], "tax_return")

        return ExtractionResult(
            success=True,
            document_type="tax_return",
            extracted_data=result["extracted_data"],
            confidence_score=confidence,
            model_used=result["model_used"],
            processing_time_ms=result["processing_time_ms"],
            warnings=["Low confidence" if confidence < CONFIDENCE_THRESHOLD else ""],
            raw_text=result.get("raw_text")
        )

    except Exception as e:
        logger.error(f"Tax return extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract/schedule-c", response_model=ExtractionResult)
async def extract_schedule_c(file: UploadFile = File(...)):
    """Extract data from Schedule C (Self-Employment)"""
    try:
        contents = await file.read()

        result = await extract_with_ollama(
            contents,
            "schedule_c",
            SCHEDULE_C_PROMPT,
            PRIMARY_MODEL
        )

        if not result["success"]:
            result = await extract_with_ollama(
                contents,
                "schedule_c",
                SCHEDULE_C_PROMPT,
                FALLBACK_MODEL
            )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Extraction failed"))

        confidence = calculate_confidence_score(result["extracted_data"], "schedule_c")

        return ExtractionResult(
            success=True,
            document_type="schedule_c",
            extracted_data=result["extracted_data"],
            confidence_score=confidence,
            model_used=result["model_used"],
            processing_time_ms=result["processing_time_ms"],
            warnings=["Low confidence" if confidence < CONFIDENCE_THRESHOLD else ""],
            raw_text=result.get("raw_text")
        )

    except Exception as e:
        logger.error(f"Schedule C extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Mortgage Document OCR Service",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "paystub": "/extract/paystub",
            "w2": "/extract/w2",
            "bank_statement": "/extract/bank-statement",
            "tax_return": "/extract/tax-return",
            "schedule_c": "/extract/schedule-c"
        },
        "created_by": "Neumann Rashid AI Development"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
