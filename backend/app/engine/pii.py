"""PII Redaction Engine for OfferCheck.

Redacts sensitive Indian and international identifiers before text is stored or processed:
- Aadhaar Numbers (12-digit UIDAI format)
- PAN Cards (Permanent Account Number, 10-char alphanumeric)
- Phone Numbers (Indian mobile & landline with country codes)
- Bank Account Numbers (9-18 digits near account indicators)
- Payment Card Numbers (Visa, MasterCard, RuPay 16-digit)
- UPI Handles (user@bank format)
"""
import re
from typing import Tuple

# Regex Patterns for Indian & Global PII
AADHAAR_PATTERN = re.compile(
    r"\b[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}\b",
    re.IGNORECASE
)

PAN_PATTERN = re.compile(
    r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
    re.IGNORECASE
)

# Indian & International Phone Numbers (+91 ..., 10 digits starting with 6-9)
PHONE_PATTERN = re.compile(
    r"(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b|"
    r"(?:\+\d{1,3}[\s-]?)?\(?\d{2,5}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}\b",
    re.IGNORECASE
)

# Credit/Debit Cards (13 to 19 digits with optional spaces or hyphens)
CARD_PATTERN = re.compile(
    r"\b(?:\d{4}[ -]?){3}\d{4}\b|\b\d{15,16}\b",
    re.IGNORECASE
)

# Bank Account Numbers: 9 to 18 digits preceded by banking keywords
BANK_ACCOUNT_PATTERN = re.compile(
    r"\b((?:a/c|acct|account|acc|bank|no|number|num)[\s:#.-]{1,15})(\d{9,18})\b",
    re.IGNORECASE
)

# UPI Handles
UPI_PATTERN = re.compile(
    r"\b[a-zA-Z0-9.\-_]{2,256}@(?!gmail|yahoo|outlook|hotmail|icloud|proton)[a-zA-Z]{2,64}\b",
    re.IGNORECASE
)


def redact_pii(text: str) -> Tuple[str, dict]:
    """Redact Personally Identifiable Information (PII) from email text.

    Returns:
        Tuple of (redacted_text, count_dict)
    """
    if not text:
        return "", {}

    counts = {
        "aadhaar": 0,
        "pan": 0,
        "phone": 0,
        "card": 0,
        "bank_account": 0,
        "upi": 0,
    }

    # Helper function to count replacements
    def _sub_and_count(pattern: re.Pattern, repl: str, target: str, key: str) -> str:
        matches = list(pattern.finditer(target))
        counts[key] += len(matches)
        return pattern.sub(repl, target)

    redacted = text

    # Redact in priority order
    redacted = _sub_and_count(AADHAAR_PATTERN, "[REDACTED_AADHAAR]", redacted, "aadhaar")
    redacted = _sub_and_count(PAN_PATTERN, "[REDACTED_PAN]", redacted, "pan")
    redacted = _sub_and_count(BANK_ACCOUNT_PATTERN, r"\g<1>[REDACTED_BANK_ACCOUNT]", redacted, "bank_account")
    redacted = _sub_and_count(CARD_PATTERN, "[REDACTED_CARD]", redacted, "card")
    redacted = _sub_and_count(PHONE_PATTERN, "[REDACTED_PHONE]", redacted, "phone")
    redacted = _sub_and_count(UPI_PATTERN, "[REDACTED_UPI]", redacted, "upi")

    return redacted, counts
