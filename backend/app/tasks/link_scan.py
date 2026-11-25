"""Link reputation tasks (Google Safe Browsing & safe worker URL expansion)."""
import os
from typing import Dict, Any, List
import httpx
from backend.app.core.config import settings
from backend.app.celery_app import celery_app


def expand_short_urls(urls: List[str], max_hops: int = 5) -> List[Dict[str, Any]]:
    """
    Expands shortened/redirected links in an isolated worker.
    Never fetched from the API host. Does not execute JavaScript or download binary bodies.
    """
    results = []
    headers = {"User-Agent": "OfferCheck-SecurityScanner/1.0"}

    with httpx.Client(timeout=4.0, follow_redirects=False, headers=headers) as client:
        for u in urls:
            current_url = u
            hops = 0
            chain = [current_url]

            try:
                while hops < max_hops:
                    # Issue HEAD request only to inspect Location header safely
                    resp = client.head(current_url)
                    if resp.status_code in (301, 302, 303, 307, 308) and "Location" in resp.headers:
                        loc = resp.headers["Location"]
                        chain.append(loc)
                        current_url = loc
                        hops += 1
                    else:
                        break
            except Exception as e:
                pass

            results.append({
                "initial_url": u,
                "final_url": current_url,
                "hops": hops,
                "redirect_chain": chain,
                "was_shortened": hops > 0
            })

    return results


def query_safe_browsing(urls: List[str], api_key: str = settings.GOOGLE_SAFE_BROWSING_API_KEY) -> Dict[str, Any]:
    """Checks URLs against Google Safe Browsing Lookup API v4."""
    if not api_key or not urls:
        return {"threats_found": False, "matches": []}

    endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}"
    payload = {
        "client": {
            "clientId": "offercheck",
            "clientVersion": "1.0.0"
        },
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": u} for u in urls[:10]]
        }
    }

    try:
        with httpx.Client(timeout=6.0) as client:
            resp = client.post(endpoint, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                matches = data.get("matches", [])
                return {
                    "threats_found": len(matches) > 0,
                    "matches": matches
                }
    except Exception:
        pass

    return {"threats_found": False, "matches": []}


@celery_app.task(name="tasks.scan_links_reputation", bind=True)
def scan_links_reputation(self, urls: List[str]) -> Dict[str, Any]:
    """Celery task expanding short links and checking Google Safe Browsing."""
    if not urls:
        return {"status": "skipped", "message": "No URLs to scan"}

    expanded = expand_short_urls(urls)
    final_urls = [e["final_url"] for e in expanded]

    safe_browsing = query_safe_browsing(final_urls)

    score_delta = 0
    if safe_browsing.get("threats_found"):
        score_delta += 60  # Critical threat identified

    return {
        "expanded_links": expanded,
        "safe_browsing": safe_browsing,
        "score_delta": score_delta
    }
