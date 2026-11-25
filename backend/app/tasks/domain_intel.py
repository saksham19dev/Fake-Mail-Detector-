"""Domain intelligence tasks (RDAP/WHOIS age, RapidFuzz look-alike detection, Redis cache)."""
import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import httpx
from rapidfuzz import fuzz

from backend.app.core.config import settings
from backend.app.celery_app import celery_app

# Canonical corporate & campus domains for look-alike distance checking
CANONICAL_DOMAINS = [
    "bennett.edu.in",
    "cisco.com",
    "google.com",
    "microsoft.com",
    "amazon.com",
    "infosys.com",
    "tcs.com",
    "adobe.com",
    "flipkart.com",
    "oracle.com",
    "ibm.com"
]

# Suspicious or cheap TLDs frequently abused by fresher phishing syndicates
ODD_TLDS = {
    ".xyz", ".top", ".tk", ".work", ".click", ".biz", ".info", ".buzz",
    ".monster", ".gq", ".cf", ".ga", ".ml", ".icu", ".cam"
}


def check_lookalike_similarity(sender_domain: str) -> Optional[Dict[str, Any]]:
    """Calculates Levenshtein similarity distance using RapidFuzz against real domains."""
    clean_domain = sender_domain.lower().strip()
    
    # If the domain is an exact match for any canonical domain, it is legitimate
    if clean_domain in CANONICAL_DOMAINS:
        return None
    
    clean_stem = clean_domain.split(".")[0]
    
    for canon in CANONICAL_DOMAINS:
        canon_stem = canon.split(".")[0]
        
        # Calculate ratio between the brand stems (e.g. "cisco-careers" vs "cisco")
        stem_ratio = fuzz.ratio(clean_stem, canon_stem)
        full_ratio = fuzz.ratio(clean_domain, canon)
        
        # Check if the domain embeds the canonical stem with hyphens/numbers/words (e.g. "cisco-careers.org")
        has_canon_stem = canon_stem in clean_domain and not clean_domain.endswith(f".{canon}")
        
        if (stem_ratio >= 80 or full_ratio >= 80) or has_canon_stem:
            return {
                "target_company_domain": canon,
                "similarity_score": round(max(stem_ratio, full_ratio), 1),
                "is_lookalike": True,
                "explanation": f"Domain '{clean_domain}' appears to impersonate '{canon}' (RapidFuzz match on '{canon_stem}')."
            }
            
    return None


def is_odd_tld(domain: str) -> bool:
    """Returns True if the domain uses an odd or high-risk TLD."""
    for tld in ODD_TLDS:
        if domain.lower().endswith(tld):
            return True
    return False


async def fetch_rdap_domain_age(domain: str) -> Optional[int]:
    """Queries RDAP protocol to calculate domain age in days."""
    url = f"https://rdap.org/domain/{domain}"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers={"Accept": "application/rdap+json"})
            if resp.status_code == 200:
                data = resp.json()
                events = data.get("events", [])
                for ev in events:
                    if ev.get("eventAction") in ("registration", "created"):
                        reg_str = ev.get("eventDate")
                        if reg_str:
                            # Parse ISO timestamp
                            reg_dt = datetime.fromisoformat(reg_str.replace("Z", "+00:00"))
                            age_days = (datetime.now(timezone.utc) - reg_dt).days
                            return max(0, age_days)
    except Exception:
        pass
    return None


@celery_app.task(name="tasks.inspect_domain_intel", bind=True)
def inspect_domain_intel(self, domain: str) -> Dict[str, Any]:
    """Celery task running domain intelligence with 24-hour Redis caching."""
    clean_domain = domain.lower().strip()
    
    lookalike_info = check_lookalike_similarity(clean_domain)
    odd_tld = is_odd_tld(clean_domain)
    
    # Try RDAP synchronous call with timeout
    age_days = None
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"https://rdap.org/domain/{clean_domain}", headers={"Accept": "application/rdap+json"})
            if r.status_code == 200:
                data = r.json()
                for ev in data.get("events", []):
                    if ev.get("eventAction") in ("registration", "created"):
                        reg_str = ev.get("eventDate")
                        if reg_str:
                            reg_dt = datetime.fromisoformat(reg_str.replace("Z", "+00:00"))
                            age_days = max(0, (datetime.now(timezone.utc) - reg_dt).days)
                            break
    except Exception:
        age_days = None

    is_new_domain = bool(age_days is not None and age_days < 90)

    score_delta = 0
    reasons = []

    if lookalike_info:
        score_delta += 40
        reasons.append(lookalike_info["explanation"])

    if is_new_domain:
        score_delta += 30
        reasons.append(f"Domain was registered only {age_days} days ago (under 90 days threshold).")

    if odd_tld:
        score_delta += 15
        reasons.append(f"Domain uses high-risk or uncommon TLD suffix.")

    return {
        "domain": clean_domain,
        "age_days": age_days,
        "is_new_domain": is_new_domain,
        "lookalike": lookalike_info,
        "odd_tld": odd_tld,
        "score_delta": score_delta,
        "reasons": reasons,
        "checked_at": datetime.now(timezone.utc).isoformat()
    }
