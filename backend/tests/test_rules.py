"""Unit tests for OfferCheck Rules Engine and all YAML rules."""
import pytest
from pathlib import Path
from app.engine.parser import parse_features, EmailFeatures, HeaderAuth
from app.engine.rules import RulesEngine, Finding


@pytest.fixture
def engine():
    """Instantiate RulesEngine with default rules.yaml."""
    rules_path = Path(__file__).parent.parent / "app" / "rules.yaml"
    return RulesEngine(rules_path=rules_path)


class TestRulesEngine:
    """Tests for all individual rules defined in rules.yaml."""

    def test_rule_fee_request(self, engine):
        """Rule 1: Upfront fee, registration charge, or security deposit."""
        text = "To confirm your internship, you must pay a mandatory registration fee of Rs. 999 via UPI."
        feat = parse_features(sender="hr@company.com", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_FEE_REQUEST" in rule_ids
        assert result.is_payment_demand is True

    def test_rule_cheque_overpayment(self, engine):
        """Rule 2: Fake cheque / advance overpayment scam."""
        text = "We will mail you a cheque for home office equipment. Please deposit the check and wire the excess to our vendor."
        feat = parse_features(sender="recruiter@company.com", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_CHEQUE_OVERPAYMENT" in rule_ids
        assert result.is_payment_demand is True

    def test_rule_id_otp_request(self, engine):
        """Rule 3: Aadhaar, PAN, OTP, or banking credential request."""
        text = "Before receiving your offer letter, please send your Aadhaar card copy and bank account details."
        feat = parse_features(sender="hr@portal.org", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_ID_OTP_REQUEST" in rule_ids

    def test_rule_whatsapp_telegram(self, engine):
        """Rule 4: WhatsApp or Telegram-only redirection."""
        text = "Do not reply to this email. Contact our recruitment manager on Telegram: t.me/fastinterns_official."
        feat = parse_features(sender="jobs@tech.org", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_WHATSAPP_TELEGRAM" in rule_ids

    def test_rule_no_interview(self, engine):
        """Rule 5: Selected without interview or evaluation."""
        text = "Congratulations! You have been selected directly without any interview based on your profile."
        feat = parse_features(sender="careers@corp.com", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_NO_INTERVIEW" in rule_ids

    def test_rule_urgency_panic(self, engine):
        """Rule 6: Artificial urgency and countdown pressure."""
        text = "Only 2 slots available! Confirm your acceptance within 24 hours or the offer expires today."
        feat = parse_features(sender="recruitment@firm.com", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_URGENCY_PANIC" in rule_ids

    def test_rule_unrealistic_pay(self, engine):
        """Rule 7: Unrealistic stipend and 'no skills' claim."""
        text = "Part-time data entry intern. Earn Rs. 50,000 per month, work 1-2 hours daily, no prior skills required!"
        feat = parse_features(sender="quickjobs@portal.com", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_UNREALISTIC_PAY" in rule_ids

    def test_rule_short_links(self, engine):
        """Rule 8: Masked destination / URL shorteners."""
        text = "Click to download your appointment letter: https://bit.ly/internship-offer-2026"
        feat = parse_features(sender="hr@corp.com", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_SHORT_LINKS" in rule_ids

    def test_rule_generic_greeting(self, engine):
        """Rule 9: Generic impersonal greeting."""
        text = "Dear Candidate,\n\nWe are pleased to offer you the internship."
        feat = parse_features(sender="recruiter@corp.com", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_GENERIC_GREETING" in rule_ids

    def test_rule_suspicious_attachment(self, engine):
        """Rule 10: Suspicious software setup or executable."""
        text = "Please download and run the attached portal setup tool: assessment.exe to proceed."
        feat = parse_features(sender="hr@setup.com", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_SUSPICIOUS_ATTACHMENT" in rule_ids

    def test_rule_coercive_disqualification(self, engine):
        """Rule 11: Coercive threats of placement removal or disqualification."""
        text = "Failure to register before the deadline will result in removal from the current training batch. Complete registration to avoid disqualification."
        feat = parse_features(sender="training@desk.org", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_COERCIVE_DISQUALIFICATION" in rule_ids

    def test_rule_unverified_form(self, engine):
        """Rule 12: Generic Google Form used for academic enrollment."""
        text = "Fill your confidential internship registration form here: https://docs.google.com/forms/d/e/1FAIpQLSc/viewform"
        feat = parse_features(sender="placement@desk.org", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_UNVERIFIED_FORM" in rule_ids

    def test_rule_free_mail_sender(self, engine):
        """Rule 13: Free webmail sender detection."""
        feat = parse_features(sender="corporate.recruiter2026@gmail.com", body="Official internship offer from Microsoft.")
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_FREE_MAIL_SENDER" in rule_ids

    def test_rule_replyto_mismatch(self, engine):
        """Rule 14: Reply-To domain mismatch."""
        feat = parse_features(
            sender="hr@microsoft.com",
            reply_to="attacker.mailbox@gmail.com",
            body="Job offer letter."
        )
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_REPLYTO_MISMATCH" in rule_ids

    def test_rule_auth_failure(self, engine):
        """Rule 15: SPF, DKIM, or DMARC authentication failure."""
        headers = "Received-SPF: fail (domain does not authorize IP)\nAuthentication-Results: dkim=fail; dmarc=fail"
        feat = parse_features(sender="recruiter@spoofed.com", body="Offer letter.", raw_headers=headers)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_AUTH_FAILURE" in rule_ids

    def test_rule_structured_interview_positive_sign(self, engine):
        """Rule 16: Positive sign for structured technical evaluation."""
        text = "You are invited for the online coding assessment on HackerRank followed by a technical interview panel."
        feat = parse_features(sender="campus@cisco.com", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_STRUCTURED_INTERVIEW" in rule_ids
        # Weight should be negative (score reduction)
        finding = next(f for f in result.findings if f.rule_id == "RULE_STRUCTURED_INTERVIEW")
        assert finding.weight < 0

    def test_rule_official_portal_positive_sign(self, engine):
        """Rule 17: Positive sign for recognized corporate careers portal."""
        text = "Track your application status on our official careers portal at https://careers.microsoft.com/myworkdayjobs"
        feat = parse_features(sender="university@microsoft.com", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE_OFFICIAL_PORTAL" in rule_ids
        finding = next(f for f in result.findings if f.rule_id == "RULE_OFFICIAL_PORTAL")
        assert finding.weight < 0


class TestRulesEngineAdvancedLogic:
    """Tests for negation suppression, hard overrides, and clamping."""

    def test_negation_guard_suppresses_false_positives(self, engine):
        """Verify safety warnings like 'never ask for fees' do NOT trigger fee rules."""
        text = (
            "Important Security Notice: Bennett University and Cisco never charge any registration fee, "
            "training deposit, or laptop fees. Do not share your password or OTP with anyone."
        )
        feat = parse_features(sender="sudeepta.chauhan@bennett.edu.in", body=text)
        result = engine.evaluate(feat)
        rule_ids = [f.rule_id for f in result.findings]
        # Must NOT flag fee request or OTP request
        assert "RULE_FEE_REQUEST" not in rule_ids
        assert "RULE_ID_OTP_REQUEST" not in rule_ids
        assert result.is_payment_demand is False

    def test_hard_override_payment_plus_free_mail(self, engine):
        """Hard override: payment request + free-mail sender must score >= 75."""
        text = "Pay Rs. 500 registration fee to confirm your slot."
        feat = parse_features(sender="quickhr@gmail.com", body=text)
        result = engine.evaluate(feat)
        assert result.is_payment_demand is True
        assert result.is_free_mail is True
        assert result.hard_override_triggered is True
        assert result.score >= 75

    def test_hard_override_blocklisted_domain(self, engine):
        """Hard override: blocklisted domain must score 100."""
        text = "Welcome to our company."
        feat = parse_features(sender="hr@known-scam-domain.com", body=text)
        result = engine.evaluate(feat, is_domain_blocklisted=True)
        assert result.hard_override_triggered is True
        assert result.score == 100

    def test_score_clamping(self, engine):
        """Score must never exceed 100 or drop below 0."""
        clean_text = "HackerRank technical interview coding round at https://careers.google.com"
        feat_clean = parse_features(sender="campus@google.com", body=clean_text)
        res_clean = engine.evaluate(feat_clean)
        assert res_clean.score >= 0

        scam_text = (
            "Pay registration fee Rs 999. Selected directly without interview. "
            "Mail you a cashier cheque for equipment. Wire the excess. "
            "Download assessment.exe. Send Aadhaar card. Join t.me/scam. Offer expires within 24 hours."
        )
        feat_scam = parse_features(sender="scammer@gmail.com", body=scam_text)
        res_scam = engine.evaluate(feat_scam)
        assert res_scam.score <= 100
        assert res_scam.score >= 75

