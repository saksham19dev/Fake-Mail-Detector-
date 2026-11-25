import pytest
from backend.app.tasks.domain_intel import check_lookalike_similarity, is_odd_tld
from backend.app.tasks.link_scan import expand_short_urls


def test_lookalike_cisco_spoof():
    """Verify rapidfuzz detects cisco-careers.org mimicking cisco.com."""
    result = check_lookalike_similarity("cisco-careers.org")
    assert result is not None
    assert result["target_company_domain"] == "cisco.com"
    assert result["is_lookalike"] is True


def test_lookalike_bennett_spoof():
    """Verify rapidfuzz detects bennett-careers.org mimicking bennett.edu.in."""
    result = check_lookalike_similarity("bennett-careers.org")
    assert result is not None
    assert result["target_company_domain"] == "bennett.edu.in"
    assert result["is_lookalike"] is True


def test_canonical_domain_not_flagged_as_lookalike():
    """Verify genuine google.com and cisco.com are not lookalikes of themselves."""
    assert check_lookalike_similarity("google.com") is None
    assert check_lookalike_similarity("cisco.com") is None
    assert check_lookalike_similarity("bennett.edu.in") is None


def test_odd_tlds_detection():
    """Verify detection of high-risk / uncommon TLDs."""
    assert is_odd_tld("recruitment.xyz") is True
    assert is_odd_tld("jobs.top") is True
    assert is_odd_tld("apply.work") is True
    assert is_odd_tld("offer.biz") is True
    assert is_odd_tld("google.com") is False
    assert is_odd_tld("bennett.edu.in") is False


def test_url_expansion_safe_handling():
    """Verify expand_short_urls executes safely and formats output."""
    urls = ["https://example.com/test", "https://httpbin.org/status/200"]
    expanded = expand_short_urls(urls)
    assert len(expanded) == 2
    assert "final_url" in expanded[0]
    assert "was_shortened" in expanded[0]
