from typing import Literal, Optional

from pydantic import BaseModel, Field

# Type aliases for valid options
LengthOption = Literal["Short", "Medium", "Long"]
ToneOption = Literal["Neutral", "Professional", "Casual"]


class SummarizeRequest(BaseModel):
    """Request model for summarization endpoint"""

    length_option: LengthOption = Field(
        default="Medium",
        description="Summary length: Short (30-60 words), Medium (50-120 words), or Long (80-200 words)",
    )
    tone_option: ToneOption = Field(
        default="Neutral",
        description="Summary tone: Neutral, Professional, or Casual",
    )

    class Config:
        json_schema_extra = {"example": {"length_option": "Medium", "tone_option": "Professional"}}


class SummarizeResponse(BaseModel):
    """Response model for successful summarization"""

    summary: str = Field(description="Raw summary text")
    formatted_summary: str = Field(description="Summary formatted into paragraphs")
    extracted_text_preview: str = Field(description="First 500 characters of extracted text")
    success: bool = Field(default=True)
    metadata: Optional[dict] = Field(
        default=None, description="Additional metadata (word counts, processing time, etc.)"
    )


class ErrorResponse(BaseModel):
    """Response model for errors"""

    detail: str = Field(description="Error message")
    error_code: str = Field(description="Machine-readable error code")
    success: bool = Field(default=False)
