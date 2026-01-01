import asyncio
import os
import time
import uuid

import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sse_starlette.sse import EventSourceResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .logger import setup_logging
from .middleware import SecurityHeadersMiddleware
from .models import LengthOption, SummarizeResponse, ToneOption
from .streaming import summarize_stream_generator
from .utils.formatter import format_summary_to_paragraphs
from .utils.pdf_extractor import extract_text_from_pdf_bytes
from .utils.summarizer import summarize_text_async
from .utils.usage_tracker import usage_tracker

# Load environment variables from .env file
load_dotenv()

# Initialize Sentry for error tracking (production only)
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,  # Sample 10% of requests for performance monitoring
        profiles_sample_rate=0.1,  # Sample 10% for profiling
        environment=os.getenv("ENVIRONMENT", "development"),
        # Capture request bodies for debugging
        send_default_pii=False,  # Don't send PII by default
        # Set release version for tracking
        release=os.getenv("VERCEL_GIT_COMMIT_SHA", "dev"),
    )

# Initialize logger with config
logger = setup_logging(settings.LOG_LEVEL)

app = FastAPI(title="PDF Document Summarizer API")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


# Custom rate limit error handler
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler that provides helpful error messages"""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please try again later.",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "retry_after": "60 minutes",
        },
        headers={
            "Retry-After": "3600",
            "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_HOUR),
            "X-RateLimit-Reset": str(int(time.time()) + 3600),
        },
    )


# Request ID Middleware
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)

        logger.info("request_completed", request_id=request_id, status_code=response.status_code)

        return response


# Configure CORS with environment-based origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # From environment variable
    allow_methods=["GET", "POST", "OPTIONS"],  # Restrict to needed methods
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=False,  # Explicit for security
)

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "PDF Summarizer API"}


@app.post("/api/summarize", response_model=SummarizeResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_HOUR}/hour")
async def summarize_endpoint(
    request: Request,
    file: UploadFile = File(..., description="PDF file to summarize"),
    length_option: LengthOption = Form(
        "Medium", description="Summary length: Short, Medium, or Long"
    ),
    tone_option: ToneOption = Form(
        "Neutral", description="Summary tone: Neutral, Professional, or Casual"
    ),
):
    """
    Summarize a PDF document.

    Args:
        file: PDF file upload
        length_option: Summary length (Short, Medium, Long)
        tone_option: Summary tone (Neutral, Professional, Casual)

    Returns:
        SummarizeResponse: Contains summary, formatted version, and preview

    Raises:
        HTTPException: For various error conditions (file size, timeout, processing errors)

    Example Success Response:
        {
            "summary": "This document discusses...",
            "formatted_summary": "This document discusses...\\n\\nThe key points are...",
            "extracted_text_preview": "Chapter 1: Introduction...",
            "success": true,
            "metadata": {
                "original_word_count": 5000,
                "summary_word_count": 150,
                "compression_ratio": 0.03
            }
        }
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(400, "Only PDF files are supported")

        # Read file bytes
        file_bytes = await file.read()

        # File size validation using config
        max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_size:
            raise HTTPException(400, f"File too large (max {settings.MAX_FILE_SIZE_MB}MB)")

        # Check monthly quota before processing
        if usage_tracker.is_quota_exceeded():
            logger.warning("monthly_quota_exceeded")
            raise HTTPException(
                429,
                "Monthly API quota exceeded. Please try again next month or upgrade.",
            )

        # Set timeout for entire operation (50s to stay under Vercel 60s limit)
        try:
            async with asyncio.timeout(50):
                # Extract text from PDF
                text = await extract_text_from_pdf_bytes(file_bytes)

                if not text.strip():
                    raise HTTPException(
                        400, "No text found in PDF. The file may contain only images."
                    )

                # Track character usage for quota monitoring
                usage_tracker.track(len(text))
                logger.info(
                    "quota_usage",
                    chars_used=len(text),
                    remaining=usage_tracker.get_remaining(),
                    request_id=getattr(request.state, "request_id", None),
                )

                logger.info(
                    "pdf_extracted",
                    text_length=len(text),
                    word_count=len(text.split()),
                    filename=file.filename,
                    request_id=getattr(request.state, "request_id", None),
                )

                # Summarize text using HF API
                summary = await summarize_text_async(text, length_option, tone_option)

                logger.info(
                    "summarization_complete",
                    summary_length=len(summary),
                    length_option=length_option,
                    tone_option=tone_option,
                    request_id=getattr(request.state, "request_id", None),
                )

                # Format summary into paragraphs
                formatted_summary = format_summary_to_paragraphs(summary)

                return SummarizeResponse(
                    summary=summary,
                    formatted_summary=formatted_summary,
                    extracted_text_preview=text[:500] + ("..." if len(text) > 500 else ""),
                    metadata={
                        "original_word_count": len(text.split()),
                        "summary_word_count": len(summary.split()),
                        "compression_ratio": round(len(summary) / len(text), 3),
                    },
                )

        except asyncio.TimeoutError:
            raise HTTPException(
                504, "Processing timeout - document too large or processing took too long"
            )

    except KeyError as e:
        if "HF_API_TOKEN" in str(e):
            raise HTTPException(500, "Server configuration error: HF API token not set")
        raise HTTPException(500, f"Configuration error: {str(e)}")

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Log the error with context
        logger.error(
            "summarize_error",
            error=str(e),
            error_type=type(e).__name__,
            filename=file.filename if file else None,
            request_id=getattr(request.state, "request_id", None),
        )
        raise HTTPException(500, f"Failed to process document: {str(e)}")


@app.post("/api/summarize-stream")
@limiter.limit(f"{settings.RATE_LIMIT_PER_HOUR}/hour")
async def summarize_stream_endpoint(
    request: Request,
    file: UploadFile = File(..., description="PDF file to summarize"),
    length_option: LengthOption = Form(
        "Medium", description="Summary length: Short, Medium, or Long"
    ),
    tone_option: ToneOption = Form(
        "Neutral", description="Summary tone: Neutral, Professional, or Casual"
    ),
):
    """
    Stream summarization progress using Server-Sent Events.

    Client should listen to events:
    - extraction_started, extraction_complete
    - chunk_processing, chunk_complete
    - formatting, complete
    - error

    Returns:
        EventSourceResponse: Server-Sent Events stream
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    # Read file bytes
    file_bytes = await file.read()

    # File size validation
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_size:
        raise HTTPException(400, f"File too large (max {settings.MAX_FILE_SIZE_MB}MB)")

    # Check monthly quota before processing
    if usage_tracker.is_quota_exceeded():
        logger.warning("monthly_quota_exceeded_stream")
        raise HTTPException(
            429,
            "Monthly API quota exceeded. Please try again next month or upgrade.",
        )

    return EventSourceResponse(
        summarize_stream_generator(file_bytes, file.filename, length_option, tone_option)
    )
