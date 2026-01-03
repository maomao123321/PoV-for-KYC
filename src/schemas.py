from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentType(str, Enum):
    passport = "passport"
    drivers_license = "drivers_license"
    unknown = "unknown"


class Evidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    snippet: Optional[str] = None
    bbox: Optional[List[float]] = Field(
        default=None, description="Normalized [x1, y1, x2, y2]"
    )


class BaseDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")

    full_name: Optional[str] = None
    birth_date: Optional[date] = None
    document_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    nationality: Optional[str] = None
    mrz_raw: Optional[str] = None
    evidence: Dict[str, Evidence] = Field(default_factory=dict)
    
    @field_validator("evidence", mode="before")
    @classmethod
    def clean_evidence(cls, v: Any) -> Dict[str, Evidence]:
        """Remove None values from evidence dict"""
        if not isinstance(v, dict):
            return {}
        return {k: val for k, val in v.items() if val is not None}
    
    @field_validator("birth_date", "issue_date", "expiry_date", mode="before")
    @classmethod
    def parse_date_flexible(cls, v: Any) -> Optional[date]:
        """Parse dates in various formats"""
        if v is None or v == "":
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            # Try YYYY-MM-DD first
            try:
                return date.fromisoformat(v)
            except:
                pass
            # Try DD.MON.YYYY format (e.g., "17.JAN.1706")
            try:
                return datetime.strptime(v, "%d.%b.%Y").date()
            except:
                pass
            # Try other common formats
            for fmt in ["%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(v, fmt).date()
                except:
                    continue
        return None


class PassportInfo(BaseDocument):
    passport_type: Optional[str] = None


class DriversLicenseInfo(BaseDocument):
    license_class: Optional[str] = None
    address: Optional[str] = None


class ExtractionPayload(BaseModel):
    """Structured payload returned by Fireworks."""

    model_config = ConfigDict(extra="ignore")

    document_type: DocumentType = DocumentType.unknown
    ai_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    missing_fields: List[str] = Field(default_factory=list)
    passport: Optional[PassportInfo] = None
    drivers_license: Optional[DriversLicenseInfo] = None
    raw_text: Optional[str] = None


class ExtractionResult(BaseModel):
    """Wrapper for downstream validation."""

    model_config = ConfigDict(extra="ignore")

    payload: ExtractionPayload
    image_quality: float
    phash: str

