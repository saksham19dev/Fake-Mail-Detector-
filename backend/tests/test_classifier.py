"""Unit tests for pure-Python ML ScamClassifier and Score Fusion Engine."""
import pytest
from pathlib import Path
from backend.app.engine.classifier import ScamClassifier, fuse_scores, extract_ngrams


def test_ngram_extraction():
    """Verify unigrams and bigrams are extracted properly."""
    text = "Cisco summer internship coding round"
    ngrams = extract_ngrams(text)
    assert "cisco" in ngrams
    assert "cisco_summer" in ngrams
    assert "internship_coding" in ngrams


def test_classifier_initialization_and_prediction(tmp_path):
    """Test model training and persistence."""
    model_file = tmp_path / "test_weights.json"
    clf = ScamClassifier(model_path=model_file)
    assert model_file.exists()
    assert len(clf.feature_weights) > 0


def test_classifier_genuine_email():
    """Genuine internship announcements should have low scam probability (< 0.40)."""
    clf = ScamClassifier()
    genuine_text = (
        "Bennett University Campus Recruitment. Cisco Summer Internship technical round scheduled on HackerRank. "
        "Review official details on careers.cisco.com. Bennett University and Cisco never charge registration fees."
    )
    prob = clf.predict_proba(genuine_text)
    assert prob < 0.40


def test_classifier_scam_email():
    """Scam emails with urgency and payment demands should have high scam probability (> 0.60)."""
    clf = ScamClassifier()
    scam_text = (
        "Congratulations! You are selected as Web Developer Intern without interview. "
        "Pay mandatory refundable laptop courier fee of Rs. 1500 to hr@upi within 24 hours. "
        "Send payment screenshot on Telegram."
    )
    prob = clf.predict_proba(scam_text)
    assert prob > 0.60


def test_fuse_scores_calculation():
    """Verify 65% rules + 35% ML fusion formula."""
    # 0.65 * 40 + 0.35 * (0.80 * 100) = 26 + 28 = 54
    fused = fuse_scores(rule_score=40, ml_probability=0.80, hard_override=False)
    assert fused == 54

    # Clamping boundaries
    assert fuse_scores(rule_score=0, ml_probability=0.0) == 0
    assert fuse_scores(rule_score=100, ml_probability=1.0) == 100


def test_fuse_scores_hard_override():
    """Verify that hard overrides bypass ML dilution."""
    # When hard_override is True (e.g. fee + freemail = 75 or blocklist = 100)
    assert fuse_scores(rule_score=100, ml_probability=0.10, hard_override=True) == 100
    assert fuse_scores(rule_score=75, ml_probability=0.20, hard_override=True) == 75
