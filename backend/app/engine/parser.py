"""Email feature extractor for OfferCheck.

Parses headers, auth results (SPF/DKIM/DMARC), URLs, phone numbers,
monetary amounts, greetings, and extracts company/role indicators.
Supports both plain text input and raw RFC-822 (.eml) parsing.
"""
import email
from email import policy
import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# Common free webmail domains used by scammers instead of corporate domains
FREE_MAIL_PROVIDERS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.in", "outlook.com",
    "hotmail.com", "live.com", "rediffmail.com", "zoho.com", "proton.me",
    "protonmail.com", "icloud.com", "aol.com", "mail.com", "gmx.com", "yandex.com"
}

# Generic greeting indicators
GENERIC_GREETING_PATTERNS = [
    re.compile(r"^\s*dear\s+(?:candidate|student|applicant|job\s*seeker|fresher|intern|sir\/madam|sir|madam)\b", re.I | re.M),
    re.compile(r"^\s*hello\s+(?:candidate|applicant|student|job\s*seeker)\b", re.I | re.M),
    re.compile(r"^\s*respected\s+(?:sir|madam|applicant)\b", re.I | re.M),
    re.compile(r"^\s*attention:\s*(?:job\s*seeker|applicant|student)\b", re.I | re.M),
]

# Currency & amount patterns (e.g. ₹45,000, Rs. 10,000, $5,000)
AMOUNT_PATTERN = re.compile(
    r"(?:rs\.?|inr|₹|\$|€|£)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+)",
    re.IGNORECASE
)

# URL regex
URL_PATTERN = re.compile(
    r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
    re.IGNORECASE
)


class HeaderAuth(BaseModel):
    """Email authentication header results."""
    spf: str = "none"  # pass, fail, softfail, neutral, none
    dkim: str = "none"  # pass, fail, none
    dmarc: str = "none"  # pass, fail, none
    raw_auth_results: Optional[str] = None


class EmailFeatures(BaseModel):
    """Structured features extracted from an email."""
    sender: str = ""
    sender_domain: str = ""
    is_free_mail: bool = False
    reply_to: Optional[str] = None
    reply_to_domain: Optional[str] = None
    reply_to_mismatch: bool = False
    subject: str = ""
    body: str = ""
    urls: List[str] = Field(default_factory=list)
    domains_in_body: List[str] = Field(default_factory=list)
    amounts: List[str] = Field(default_factory=list)
    greeting_type: str = "unknown"  # "generic", "personalized", "none"
    company_name: Optional[str] = None
    role_name: Optional[str] = None
    auth: HeaderAuth = Field(default_factory=HeaderAuth)


def extract_domain(email_address: str) -> str:
    """Extract clean domain from email address."""
    if not email_address:
        return ""
    clean = email_address.strip().lower()
    # Handle angle brackets: "Name <user@domain.com>"
    match = re.search(r"<([^>]+)>", clean)
    if match:
        clean = match.group(1)
    if "@" in clean:
        return clean.split("@")[-1].strip()
    return clean


def is_free_email_provider(email_address: str) -> bool:
    """Check if the sender email address uses a public free mail service."""
    domain = extract_domain(email_address)
    return domain in FREE_MAIL_PROVIDERS


def check_reply_to_mismatch(sender: str, reply_to: str) -> bool:
    """Check if Reply-To domain differs from the From sender domain."""
    s_dom = extract_domain(sender)
    r_dom = extract_domain(reply_to)
    return bool(r_dom and r_dom != s_dom)


def parse_email_headers(headers_str: str) -> Dict[str, str]:
    """Parse authentication headers and return dict of status values."""
    auth = parse_header_auth(headers_str)
    return {"spf": auth.spf, "dkim": auth.dkim, "dmarc": auth.dmarc}



def parse_header_auth(headers_str: str) -> HeaderAuth:
    """Extract SPF, DKIM, and DMARC status from raw header block."""
    auth = HeaderAuth()
    if not headers_str:
        return auth

    auth.raw_auth_results = headers_str

    # SPF Extraction
    spf_match = re.search(r"(?:Received-SPF|spf)=([a-zA-Z]+)", headers_str, re.IGNORECASE)
    if spf_match:
        val = spf_match.group(1).lower()
        if "pass" in val:
            auth.spf = "pass"
        elif "fail" in val or "softfail" in val:
            auth.spf = "fail"
        else:
            auth.spf = val

    # DKIM Extraction
    dkim_match = re.search(r"dkim=([a-zA-Z]+)", headers_str, re.IGNORECASE)
    if dkim_match:
        val = dkim_match.group(1).lower()
        if "pass" in val:
            auth.dkim = "pass"
        elif "fail" in val:
            auth.dkim = "fail"
        else:
            auth.dkim = val
    elif "dkim-signature:" in headers_str.lower():
        auth.dkim = "pass"

    # DMARC Extraction
    dmarc_match = re.search(r"dmarc=([a-zA-Z]+)", headers_str, re.IGNORECASE)
    if dmarc_match:
        val = dmarc_match.group(1).lower()
        if "pass" in val:
            auth.dmarc = "pass"
        elif "fail" in val:
            auth.dmarc = "fail"
        else:
            auth.dmarc = val

    return auth


def parse_raw_eml(raw_eml_bytes: bytes) -> Dict[str, Any]:
    """Parse a raw .eml file into sender, reply-to, subject, body, and headers."""
    msg = email.message_from_bytes(raw_eml_bytes, policy=policy.default)

    sender = msg.get("From", "")
    reply_to = msg.get("Reply-To", "")
    subject = msg.get("Subject", "")

    # Extract all headers as text
    headers_lines = []
    for k, v in msg.items():
        headers_lines.append(f"{k}: {v}")
    headers_text = "\n".join(headers_lines)

    # Extract body (prefer text/plain, fallback to text/html)
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get("Content-Disposition", ""))
            if ctype == "text/plain" and "attachment" not in cdispo:
                body = part.get_content()
                break
            elif ctype == "text/html" and not body and "attachment" not in cdispo:
                body = part.get_content()
    else:
        body = msg.get_content()

    return {
        "sender": sender,
        "reply_to": reply_to,
        "subject": subject,
        "body": body,
        "headers_text": headers_text,
    }


def parse_features(
    sender: str = "",
    subject: str = "",
    body: str = "",
    reply_to: Optional[str] = None,
    company: Optional[str] = None,
    raw_headers: Optional[str] = None,
    raw_eml: Optional[bytes] = None,
) -> EmailFeatures:
    """Parse text and headers into EmailFeatures model."""
    headers_text = raw_headers or ""

    # If raw .eml is provided, extract metadata
    if raw_eml:
        eml_data = parse_raw_eml(raw_eml)
        sender = sender or eml_data["sender"]
        reply_to = reply_to or eml_data["reply_to"]
        subject = subject or eml_data["subject"]
        body = body or eml_data["body"]
        headers_text = headers_text or eml_data["headers_text"]

    sender_domain = extract_domain(sender)
    is_free = sender_domain in FREE_MAIL_PROVIDERS

    reply_to_domain = extract_domain(reply_to) if reply_to else ""
    mismatch = bool(reply_to_domain and reply_to_domain != sender_domain)

    # Extract URLs and unique domains in body
    urls = URL_PATTERN.findall(body)
    domains_in_body = []
    for u in urls:
        m = re.search(r"https?://([^/:\s]+)", u)
        if m:
            d = m.group(1).lower()
            if d not in domains_in_body:
                domains_in_body.append(d)

    # Extract monetary amounts
    amounts = [m.group(0) for m in AMOUNT_PATTERN.finditer(body)]

    # Determine greeting type
    greeting_type = "none"
    for p in GENERIC_GREETING_PATTERNS:
        if p.search(body):
            greeting_type = "generic"
            break
    if greeting_type == "none":
        # Check if personalized greeting exists (e.g. "Dear Saksham", "Hello Alex")
        if re.search(r"^\s*(?:dear|hi|hello)\s+[A-Z][a-z]+", body, re.M):
            greeting_type = "personalized"

    # Header authentication
    auth = parse_header_auth(headers_text)

    # Role extraction heuristic
    role_match = re.search(r"\b([A-Za-z\s]+(?:Intern|Internship|Trainee|Developer|Engineer|Analyst))\b", subject + " " + body, re.I)
    role_name = role_match.group(1).strip() if role_match else None

    return EmailFeatures(
        sender=sender,
        sender_domain=sender_domain,
        is_free_mail=is_free,
        reply_to=reply_to,
        reply_to_domain=reply_to_domain,
        reply_to_mismatch=mismatch,
        subject=subject,
        body=body,
        urls=urls,
        domains_in_body=domains_in_body,
        amounts=amounts,
        greeting_type=greeting_type,
        company_name=company,
        role_name=role_name,
        auth=auth,
    )

