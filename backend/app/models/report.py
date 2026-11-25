from datetime import datetime, timezone
import uuid
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class Report(Base):
    """
    Audit report generated for an email analysis.
    Matches schema: reports(id, created_at, sender_domain, company, score, verdict, status, redacted_text, eml_s3_key)
    """
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    sender_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)  # "low_risk" | "suspicious" | "likely_fake"
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    redacted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    eml_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationships
    findings = relationship(
        "Finding", back_populates="report", cascade="all, delete-orphan", lazy="selectin"
    )
    feedback_entries = relationship(
        "Feedback", back_populates="report", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, score={self.score}, verdict={self.verdict})>"
