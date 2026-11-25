import uuid
from sqlalchemy import String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class Finding(Base):
    """
    Individual heuristic or machine learning indicator identified in an email.
    Matches schema: findings(id, report_id, rule_id, weight, confidence, evidence)
    """
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    report_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship back to report
    report = relationship("Report", back_populates="findings")

    def __repr__(self) -> str:
        return f"<Finding(id={self.id}, rule_id={self.rule_id}, weight={self.weight})>"
