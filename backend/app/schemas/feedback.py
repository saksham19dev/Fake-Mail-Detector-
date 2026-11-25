from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class FeedbackCreate(BaseModel):
    """Payload submitted to POST /v1/reports/{id}/feedback."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "label": "scam",
                "note": "They asked for UPI deposit to deskverify@upi after I responded."
            }
        }
    )

    label: Literal["real", "scam"] = Field(..., description="Ground truth verification: 'real' or 'scam'")
    note: Optional[str] = Field(None, max_length=1000, description="Optional user explanation")


class FeedbackResponse(BaseModel):
    """Response returned upon feedback submission."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    report_id: str
    label: str
    note: Optional[str]
    created_at: datetime

