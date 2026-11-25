from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AnalyzeRequest(BaseModel):
    """Payload submitted to POST /v1/analyze."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sender": "recruitment@cisco-careers.net",
                "company": "Cisco",
                "subject": "Offer Letter",
                "text": "Congratulations! You have been selected directly without interview. Pay Rs. 1500 registration fee via UPI.",
                "raw_eml": None
            }
        }
    )

    sender: str = Field(..., description="Sender email address (from headers)", min_length=3, max_length=255)
    company: Optional[str] = Field(None, description="Claimed company name", max_length=255)
    subject: Optional[str] = Field(None, description="Email subject line", max_length=500)
    text: Optional[str] = Field(None, description="Plaintext or HTML email body")
    raw_eml: Optional[str] = Field(None, description="Raw RFC 822 .eml string containing headers and body")



class FindingItem(BaseModel):
    """Finding summary item within an analysis response."""
    rule_id: str
    weight: int
    confidence: float
    evidence: str


class AnalyzeResponse(BaseModel):
    """Response returned from POST /v1/analyze."""
    id: str
    score: int = Field(..., ge=0, le=100)
    verdict: str  # "low_risk" | "suspicious" | "likely_fake"
    status: str
    sender_domain: str
    company: Optional[str]
    findings: List[FindingItem]
    what_to_do_next: List[str]
