"""
Main FastAPI application for the LLM-powered scraper agent
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from scraper_agent import ScraperAgent
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Mortgage Tax Data Scraper",
    description="LLM-powered web scraper for mortgage tax data across all US jurisdictions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scraper agent
scraper = ScraperAgent()

# In-memory task tracking (use Redis in production)
tasks = {}


class ScrapeRequest(BaseModel):
    """Request model for scraping"""
    state: str
    county: str
    force_refresh: bool = False


class ScrapeResponse(BaseModel):
    """Response model for scraping"""
    success: bool
    task_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None


class TaskStatus(BaseModel):
    """Task status model"""
    task_id: str
    status: str  # pending, in_progress, success, failed
    progress: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Mortgage Tax Data Scraper",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "llm_provider": settings.LLM_PROVIDER,
        "search_provider": settings.WEB_SEARCH_PROVIDER
    }


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_jurisdiction(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Scrape tax data for a jurisdiction

    Synchronous mode: Returns data immediately
    Async mode: Returns task_id for status polling
    """
    try:
        logger.info(f"Scrape request received: {request.state}, {request.county}")

        # Validate state code
        if len(request.state) != 2:
            raise HTTPException(status_code=400, detail="State must be 2-letter code")

        # Check if data exists and is fresh (unless force_refresh)
        if not request.force_refresh:
            cached_data = scraper.get_cached_data(request.state, request.county)
            if cached_data:
                logger.info(f"Returning cached data for {request.county}, {request.state}")
                return ScrapeResponse(
                    success=True,
                    data=cached_data,
                    message="Cached data returned"
                )

        # For now, run synchronously
        # In production, use background_tasks or Celery
        logger.info(f"Starting scrape for {request.county}, {request.state}")
        result = await scraper.scrape(request.state, request.county)

        logger.info(f"Scrape completed for {request.county}, {request.state}")

        return ScrapeResponse(
            success=True,
            data=result,
            message="Scraping completed successfully"
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@app.get("/scrape/{state}/{county}", response_model=ScrapeResponse)
async def scrape_by_path(
    state: str,
    county: str,
    force_refresh: bool = False
):
    """
    Scrape tax data for a jurisdiction (GET endpoint)
    """
    request = ScrapeRequest(
        state=state,
        county=county,
        force_refresh=force_refresh
    )
    return await scrape_jurisdiction(request, BackgroundTasks())


@app.post("/scrape/async", response_model=ScrapeResponse)
async def scrape_async(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Scrape tax data asynchronously
    Returns task_id for status polling
    """
    import uuid

    task_id = str(uuid.uuid4())

    tasks[task_id] = {
        'status': 'pending',
        'started_at': datetime.utcnow().isoformat(),
        'state': request.state,
        'county': request.county
    }

    # Add background task
    background_tasks.add_task(
        run_scrape_task,
        task_id,
        request.state,
        request.county
    )

    return ScrapeResponse(
        success=True,
        task_id=task_id,
        message="Scraping task started"
    )


@app.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get status of an async scraping task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]

    return TaskStatus(
        task_id=task_id,
        status=task['status'],
        progress=task.get('progress'),
        result=task.get('result'),
        error=task.get('error'),
        started_at=task.get('started_at'),
        completed_at=task.get('completed_at')
    )


@app.get("/stats")
async def get_stats():
    """Get scraper statistics"""
    stats = scraper.get_stats()
    return stats


@app.post("/test")
async def test_scraper(request: ScrapeRequest):
    """
    Test endpoint for development
    Returns what the scraper would do without actually scraping
    """
    return {
        "message": "Test mode - no actual scraping performed",
        "request": {
            "state": request.state,
            "county": request.county,
            "force_refresh": request.force_refresh
        },
        "llm_provider": settings.LLM_PROVIDER,
        "search_provider": settings.WEB_SEARCH_PROVIDER,
        "cache_check": "Would check cache for existing data"
    }


async def run_scrape_task(task_id: str, state: str, county: str):
    """Background task to run scraping"""
    try:
        tasks[task_id]['status'] = 'in_progress'
        tasks[task_id]['progress'] = 10

        result = await scraper.scrape(state, county)

        tasks[task_id]['status'] = 'success'
        tasks[task_id]['progress'] = 100
        tasks[task_id]['result'] = result
        tasks[task_id]['completed_at'] = datetime.utcnow().isoformat()

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)
        tasks[task_id]['completed_at'] = datetime.utcnow().isoformat()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
