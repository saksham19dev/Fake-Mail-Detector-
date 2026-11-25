from datetime import datetime, timezone
import uuid
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class Feedback(Base):
    """
    User-submitted ground truth feedback calibrating system accuracy.
    Matches schema: feedback(id, report_id, label, note, created_at)
    """
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    report_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(16), nullable=False)  # "real" | "scam"
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationship back to report
    report = relationship("Report", back_populates="feedback_entries")

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, report_id={self.report_id}, label={self.label})>"
