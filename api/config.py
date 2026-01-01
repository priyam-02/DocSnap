from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration from environment variables"""

    # HuggingFace API
    HF_API_TOKEN: str = Field(..., description="HuggingFace API token")

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173",
        description="Comma-separated list of allowed origins",
    )

    # File upload
    MAX_FILE_SIZE_MB: int = Field(default=10, description="Maximum file size in MB")

    # Rate limiting
    RATE_LIMIT_PER_HOUR: int = Field(default=10, description="Max requests per IP per hour")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Convert comma-separated string to list"""
        return [origin.strip() for origin in v.split(",")]

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",  # Ignore extra environment variables
    }


# Global config instance
settings = Settings()
