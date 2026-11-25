from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base


class Domain(Base):
    """
    Cached domain intelligence and blocklist repository.
    Matches schema: domains(domain, age_days, registrar, blocklisted, checked_at)
    """
    __tablename__ = "domains"

    domain: Mapped[str] = mapped_column(String(255), primary_key=True)
    age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    registrar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    blocklisted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Domain(domain={self.domain}, age_days={self.age_days}, blocklisted={self.blocklisted})>"
