"""Unit tests for Normalizer and PII Redaction modules."""
import pytest
from app.engine.normalizer import normalize_email_text, strip_html_tags
from app.engine.pii import redact_pii


class TestNormalizer:
    """Tests for HTML stripping, entity decoding, and Unicode normalization."""

    def test_strip_html_tags(self):
        html_input = "<p>Congratulations! You are selected.</p><br><div>Visit <b>here</b></div>"
        cleaned = strip_html_tags(html_input)
        assert "<p>" not in cleaned
        assert "<b>" not in cleaned
        assert "Congratulations! You are selected." in cleaned
        assert "Visit here" in cleaned

    def test_unescape_html_entities(self):
        text = "Pay &pound;50 &amp; register at &quot;Portal&quot;"
        normalized = normalize_email_text(text)
        assert "£50" in normalized
        assert "&" in normalized
        assert '"Portal"' in normalized

    def test_unicode_normalization_nfkc(self):
        # Decomposed characters or fullwidth forms
        fullwidth = "Ｈｅｌｌｏ Ｉｎｔｅｒｎ"
        normalized = normalize_email_text(fullwidth)
        assert normalized == "Hello Intern"

    def test_whitespace_collapse(self):
        text = "Line 1\r\n\r\n\r\n\r\nLine 2   with   extra   spaces"
        normalized = normalize_email_text(text)
        assert "Line 1\n\nLine 2 with extra spaces" == normalized


class TestPIIRedaction:
    """Tests for Indian & international PII redaction."""

    def test_redact_aadhaar(self):
        text = "Please verify my Aadhaar 4234 5678 9012 before joining."
        redacted, counts = redact_pii(text)
        assert "[REDACTED_AADHAAR]" in redacted
        assert "4234 5678 9012" not in redacted
        assert counts["aadhaar"] == 1

    def test_redact_pan(self):
        text = "Candidate PAN is ABCDE1234F for stipend processing."
        redacted, counts = redact_pii(text)
        assert "[REDACTED_PAN]" in redacted
        assert "ABCDE1234F" not in redacted
        assert counts["pan"] == 1

    def test_redact_phone(self):
        text = "Contact HR at +91 9876543210 or 9123456789."
        redacted, counts = redact_pii(text)
        assert "[REDACTED_PHONE]" in redacted
        assert "9876543210" not in redacted
        assert counts["phone"] >= 1

    def test_redact_bank_account(self):
        text = "Send stipend to account number: 123456789012 at SBI."
        redacted, counts = redact_pii(text)
        assert "[REDACTED_BANK_ACCOUNT]" in redacted
        assert "123456789012" not in redacted
        assert counts["bank_account"] == 1

    def test_redact_upi(self):
        text = "Transfer registration fee to payments@axisbank immediately."
        redacted, counts = redact_pii(text)
        assert "[REDACTED_UPI]" in redacted
        assert "payments@axisbank" not in redacted
        assert counts["upi"] == 1

