import email
from email import policy
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, FindingItem
from backend.app.models.report import Report
from backend.app.models.finding import Finding
from backend.app.models.domain import Domain
from backend.app.db.session import get_db
from backend.app.core.config import settings

from backend.app.engine.normalizer import normalize_text
from backend.app.engine.pii import redact_pii
from backend.app.engine.parser import parse_features
from backend.app.engine.rules import RulesEngine

router = APIRouter()

# Instantiate rules engine once from configured YAML
rules_engine = RulesEngine(settings.RULES_PATH)


def build_what_to_do_next(verdict: str) -> List[str]:
    """Generates educational student guidance based on calibrated verdict."""
    if verdict == "likely_fake":
        return [
            "Do NOT transfer money, pay any registration or equipment fees, or buy gift cards.",
            "Do NOT share government identification (Aadhaar, PAN card, voter ID, passport photos) or OTPs.",
            "Report the fraudulent email to the National Cybercrime Reporting Portal at cybercrime.gov.in or call Helpline 1930.",
            "Inform Bennett University Career Development Centre (CDC) so campus security filters can block the sender domain.",
            "Permanently mark the email as junk or phishing in your student Outlook webmail."
        ]
    elif verdict == "suspicious":
        return [
            "Verify the company directly by checking their official career portal (careers.company.com) on Google.",
            "Never communicate via personal Telegram or WhatsApp handles for formal recruitment.",
            "Consult with your department faculty placement coordinator or Bennett CDC mentors before taking action.",
            "Verify if the sending domain (@domain.com) matches the legitimate corporate website."
        ]
    else:
        return [
            "Verify the application status on the official company careers portal.",
            "Prepare for the scheduled technical coding rounds or HR interview rounds.",
            "Note that Bennett CDC and legitimate enterprise employers never request fees at any stage."
        ]


@router.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_200_OK, tags=["Analysis"])
async def analyze_offer(
    payload: AnalyzeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Core detection pipeline:
    1. Ingestion & EML parsing
    2. HTML normalization & Unicode NFKC
    3. PII redaction (Aadhaar, PAN, Bank, Phone, UPI)
    4. Feature extraction (SPF, DKIM, DMARC, Reply-To, Free-mail, URLs, Amounts)
    5. Rules engine evaluation (YAML) with negation guards & overrides
    6. Score fusion & verdict calibration
    7. Database persistence
    """
    raw_text = payload.text or ""
    headers_block = ""
    reply_to = None
    subject = payload.subject or ""
    raw_eml_bytes = None

    # Parse .eml if provided
    if payload.raw_eml:
        raw_eml_bytes = payload.raw_eml.encode("utf-8")
        try:
            msg = email.message_from_string(payload.raw_eml, policy=policy.default)
            headers_block = str(msg)
            reply_to = msg.get("Reply-To")
            if not subject:
                subject = msg.get("Subject", "")
            if not raw_text:
                body_part = msg.get_body(preferencelist=('plain', 'html'))
                if body_part:
                    raw_text = body_part.get_content()
        except Exception:
            pass  # Fall back to raw_text

    if not raw_text and not payload.raw_eml:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either 'text' or 'raw_eml' must be provided for evaluation."
        )

    # 1. Normalize
    normalized = normalize_text(raw_text)

    # 2. Redact sensitive PII
    redacted_text, _ = redact_pii(normalized)

    # 3. Extract features
    features = parse_features(
        sender=payload.sender,
        subject=subject,
        body=redacted_text,
        reply_to=reply_to,
        company=payload.company,
        raw_headers=headers_block,
        raw_eml=raw_eml_bytes
    )

    # 4. Check domain blocklist from DB
    sender_domain = features.sender_domain
    domain_record = await db.get(Domain, sender_domain)
    is_blocklisted = bool(domain_record and domain_record.blocklisted)

    # 5. Evaluate through RulesEngine
    rule_results = rules_engine.evaluate(
        features=features,
        is_domain_blocklisted=is_blocklisted
    )

    final_score = rule_results.score
    if final_score >= 55:
        verdict = "likely_fake"
    elif final_score >= 25:
        verdict = "suspicious"
    else:
        verdict = "low_risk"

    # Assemble finding items
    all_findings: List[FindingItem] = [
        FindingItem(
            rule_id=f.rule_id,
            weight=f.weight,
            confidence=f.confidence,
            evidence=f.evidence
        )
        for f in rule_results.findings
    ]

    # 6. Persist Report & Findings to DB
    db_report = Report(
        sender_domain=sender_domain,
        company=payload.company,
        score=final_score,
        verdict=verdict,
        status="completed",
        redacted_text=redacted_text,
        eml_s3_key=None
    )
    db.add(db_report)
    await db.flush()  # Populate db_report.id

    for f in all_findings:
        db_finding = Finding(
            report_id=db_report.id,
            rule_id=f.rule_id,
            weight=f.weight,
            confidence=f.confidence,
            evidence=f.evidence
        )
        db.add(db_finding)

    await db.commit()

    what_next = build_what_to_do_next(verdict)

    return AnalyzeResponse(
        id=db_report.id,
        score=final_score,
        verdict=verdict,
        status="completed",
        sender_domain=sender_domain,
        company=payload.company,
        findings=all_findings,
        what_to_do_next=what_next
    )
