from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.analyze import FindingItem


class FindingResponse(FindingItem):
    """Detailed finding object with persistent DB id."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    report_id: str


class ReportResponse(BaseModel):
    """Schema for GET /v1/reports/{id}."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    sender_domain: str
    company: Optional[str]
    score: int
    verdict: str
    status: str
    redacted_text: Optional[str] = None
    findings: List[FindingResponse]
    what_to_do_next: List[str]

