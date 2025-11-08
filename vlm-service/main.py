"""
VLM (Vision Language Model) Service for Document OCR

Uses Claude's vision API for document processing on Mac M4
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import anthropic
import base64
import os
from typing import Optional
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VLM OCR Service",
    description="Vision Language Model service for document OCR using Claude",
    version="1.0.0"
)

# Initialize Claude client
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    logger.warning("ANTHROPIC_API_KEY not set!")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


class OCRRequest(BaseModel):
    """OCR request model"""
    document_type: str
    extract_fields: Optional[list] = None


class OCRResponse(BaseModel):
    """OCR response model"""
    success: bool
    text: str
    extracted_data: dict
    confidence: int


DOCUMENT_EXTRACTION_PROMPTS = {
    "pay_stub": """Extract the following information from this pay stub image:
- Employee name
- Employer name
- Pay period start and end dates
- Gross pay amount
- Net pay amount
- Year-to-date earnings
- Pay frequency (weekly, bi-weekly, monthly)

Return JSON format with these exact keys:
{
    "employee_name": "...",
    "employer_name": "...",
    "pay_period_start": "YYYY-MM-DD",
    "pay_period_end": "YYYY-MM-DD",
    "gross_pay": 0.00,
    "net_pay": 0.00,
    "ytd_earnings": 0.00,
    "pay_frequency": "..."
}""",

    "w2": """Extract the following information from this W-2 form image:
- Employee name and SSN (last 4 digits only)
- Employer name and EIN
- Box 1: Wages, tips, other compensation
- Box 2: Federal income tax withheld
- Box 16: State wages, tips, etc.
- Box 17: State income tax

Return JSON format.""",

    "bank_statement": """Extract the following information from this bank statement image:
- Bank/institution name
- Account holder name
- Account number (last 4 digits only)
- Statement period
- Beginning balance
- Ending balance
- Average balance (if shown)

Return JSON format.""",

    "tax_return": """Extract the following information from this tax return (1040) image:
- Tax year
- Filing status
- Adjusted Gross Income (AGI)
- Total income
- Taxable income
- Total tax
- Refund or amount owed

Return JSON format.""",

    "purchase_agreement": """Extract the following information from this purchase agreement image:
- Property address
- Purchase price
- Earnest money deposit
- Closing date
- Buyer name(s)
- Seller name(s)
- Contingencies mentioned

Return JSON format.""",

    "insurance": """Extract the following information from this insurance declaration page:
- Policy holder name
- Property address
- Policy number
- Coverage amount (dwelling)
- Annual premium
- Effective date
- Expiration date
- Insurance company name

Return JSON format."""
}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "VLM OCR Service",
        "version": "1.0.0",
        "status": "operational",
        "provider": "Claude Vision API"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not client:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": "Claude API key not configured"}
        )

    return {
        "status": "healthy",
        "provider": "Claude (Anthropic)",
        "api_configured": bool(ANTHROPIC_API_KEY)
    }


@app.post("/ocr", response_model=OCRResponse)
async def process_document(
    file: UploadFile = File(...),
    document_type: str = "other"
):
    """
    Process a document image with OCR using Claude Vision

    Args:
        file: Image file (JPG, PNG, PDF)
        document_type: Type of document (pay_stub, w2, bank_statement, etc.)

    Returns:
        OCR text and extracted structured data
    """
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Claude API not configured. Set ANTHROPIC_API_KEY environment variable."
        )

    try:
        logger.info(f"Processing {document_type} document: {file.filename}")

        # Read file
        contents = await file.read()

        # Encode as base64
        image_data = base64.standard_b64encode(contents).decode("utf-8")

        # Determine media type
        media_type = "image/jpeg"
        if file.filename.lower().endswith('.png'):
            media_type = "image/png"
        elif file.filename.lower().endswith('.pdf'):
            media_type = "application/pdf"
        elif file.filename.lower().endswith('.webp'):
            media_type = "image/webp"

        # Get extraction prompt
        extraction_prompt = DOCUMENT_EXTRACTION_PROMPTS.get(
            document_type,
            "Extract all text and relevant information from this document. Return as JSON."
        )

        # Call Claude Vision API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": f"{extraction_prompt}\n\nIMPORTANT: Return ONLY valid JSON, no other text."
                        }
                    ],
                }
            ],
        )

        # Extract response
        response_text = message.content[0].text

        # Try to parse as JSON
        import json
        try:
            extracted_data = json.loads(response_text)
            confidence = 90  # Claude is generally high confidence
        except json.JSONDecodeError:
            # If not valid JSON, return text only
            extracted_data = {"raw_text": response_text}
            confidence = 70

        logger.info(f"Successfully processed {file.filename}")

        return OCRResponse(
            success=True,
            text=response_text,
            extracted_data=extracted_data,
            confidence=confidence
        )

    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(e)}"
        )


@app.post("/ocr/batch")
async def process_batch(files: list[UploadFile] = File(...)):
    """
    Process multiple documents at once

    Args:
        files: List of image files

    Returns:
        List of OCR results
    """
    results = []

    for file in files:
        try:
            result = await process_document(file, document_type="other")
            results.append({
                "filename": file.filename,
                "success": True,
                "result": result
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })

    return {"results": results}


@app.post("/extract/{document_type}")
async def extract_structured_data(
    document_type: str,
    file: UploadFile = File(...)
):
    """
    Extract structured data from specific document type

    This endpoint uses document-specific extraction prompts
    for better accuracy.
    """
    return await process_document(file, document_type=document_type)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
