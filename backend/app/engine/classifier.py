"""OfferCheck Pure-Python Machine Learning Text Classifier & Score Fusion Engine.

Designed for robust, cross-platform execution without external C-extensions or
AppLocker/DLL constraints. Implements a TF-IDF weighted Log-Odds / Naive Bayes
statistical text classifier for fraud/scam detection, and fuses ML probability
with deterministic heuristic rule scoring.
"""
from collections import Counter
import json
import math
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

MODEL_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = MODEL_DIR / "model_weights.json"

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it", "its", "itself", "let's",
    "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "should", "shouldn't", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "wasn't", "we", "were", "weren't", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "won't", "would", "wouldn't", "you", "your", "yours",
    "yourself", "yourselves"
}

# Baseline Training Corpus: Genuine Corporate/CDC vs Scam/Syndicate Offers
TRAINING_SAMPLES: List[Tuple[str, int]] = [
    # Genuine Samples (Label 0)
    ("Bennett Campus Recruitment 2026: Cisco Summer Internship Online Coding Round. "
     "Initial screening for Cisco Summer Internship Program finalized. "
     "Shortlisted students invited to take Online Technical Assessment round on HackerRank. "
     "Official Portal: Review specifications at careers.cisco.com. "
     "Bennett University and Cisco never charge registration fees or deposits. Do not share OTPs.", 0),
    ("CDC Announcement: Microsoft Explore Internship - Virtual Interview Shortlist. "
     "Candidates completed coding assessment shortlisted for Virtual Technical Interview on Teams. "
     "Track status directly on Microsoft Careers at careers.microsoft.com. Neither Bennett nor Microsoft requests deposits.", 0),
    ("Google STEP Internship 2026: Official Technical Schedule. "
     "Google STEP Internship drive open for first and second year B.Tech CSE students. "
     "Apply via Google Careers careers.google.com. Bennett University CDC maintains zero tolerance policy against fees.", 0),
    ("Infosys InStep 2026: Internship Application Status Update. "
     "Thank you for applying to Infosys InStep Global Internship. "
     "Selected for Technical Mentorship Round. Slot selection on official portal infy.com. Infosys strictly prohibits monetary collection.", 0),
    ("TCS CodeVita Season 12: Interview Invitation for High Scorers. "
     "Invited for technical interview for TCS Research Internship program. "
     "Login to TCS NextStep nextstep.tcs.com. TCS does not ask for money or security deposits at any stage.", 0),
    ("Amazon WOW Internship 2026: Online Assessment Instructions. "
     "Complete Amazon Online Assessment for Software Development Engineer Intern role on HackerRank. "
     "Official portal amazon.jobs. Amazon never asks candidates to pay fees for laptops, training, or onboarding.", 0),
    ("Adobe SheCodes Mentorship & Summer Trainee Program 2026. "
     "Application for Adobe Research Trainee drive advanced to project evaluation round. "
     "Review assignment details on Adobe Career Portal. Adobe does not charge processing fees.", 0),
    ("Flipkart Runway Season 4: Coding Challenge Access Link. "
     "Coding test starts Sunday on Unstop. Finalists proceed to virtual panel interviews with Flipkart engineers. "
     "Flipkart never solicits payments for internship placement.", 0),
    ("Oracle Cloud Infrastructure (OCI) Internship Drive 2026. "
     "Technical screening for summer intern candidates. Details provisioned on Oracle Taleo candidate portal. "
     "Oracle never asks for registration fees or financial deposits.", 0),
    ("IBM Quantum & AI Student Internship Program 2026. "
     "Pleased to invite you to technical interview round for IBM Quantum Computing Internship. "
     "Confirm attendance via IBM Careers candidate dashboard. IBM never charges fees.", 0),

    # Fake / Scam Samples (Label 1)
    ("[Final Reminder] Academic Internship Program – Enrollment Update. "
     "Enrollment for Training Program is still pending. Final deadline tomorrow 7:30 pm. "
     "Registration Link: docs.google.com/forms. Failure to register will result in removal from batch and no certificate.", 1),
    ("Urgent: Confirmation of Bennett University Internship Offer - Deposit Required. "
     "Shortlisted directly for Bennett Off-Campus Trainee Placement. "
     "Pay mandatory document verification charge of Rs. 1500 to desk UPI id: deskverify@upi within 24 hours.", 1),
    ("CONGRATULATIONS: Selected as Web Developer Intern (Immediate Joining). "
     "Direct selection without interview. Stipend: Rs. 45,000/month. 100% placement guarantee. Work 2 hours daily no skills. "
     "Pay refundable security and laptop courier fee of Rs. 999 via UPI to hrtech@upi. Send screenshot to Telegram t.me.", 1),
    ("Urgent Freelance Data Entry Interns Required - Earn Rs 40,000/month. "
     "Immediate requirements for remote part-time interns. 1 hour daily, no skills required. "
     "Contact recruitment manager on Telegram: t.me/fastdata_interns. Send Aadhaar card copy.", 1),
    ("Remote Equipment Cheque Delivery for Student Intern Onboarding. "
     "Direct selection without interview. Advance cashier's cheque of $2,500 couriered to your home address. "
     "Deposit cheque in your bank, keep $500, wire remaining $2,000 to approved equipment vendor.", 1),
    ("Offer Letter: Direct Appointment as Junior AI Engineer (No Interview Needed). "
     "Selected without interview. Stipend: Rs. 60,000/month. "
     "To activate employee portal, pay seat booking fee of Rs. 1,200 to hr@upi within 12 hours. Hurry only 3 slots left.", 1),
    ("Urgent: Complete your WhatsApp Interview for Data Science Internship. "
     "Shortlisted for internship. Screening exclusively on WhatsApp: wa.me/919876543210. "
     "Have your PAN card and bank details ready on chat. Do not reply to email.", 1),
    ("Mandatory Training Certificate Required for Cloud Internship Onboarding. "
     "Selected for Cloud Developer Internship. Pay mandatory processing fee of Rs. 2,999 at bit.ly/edutech-pay. "
     "Failure to pay within 24 hours leads to offer cancellation.", 1),
    ("Urgent Document Verification: Send Aadhaar and Net Banking Details. "
     "Shortlisted for virtual internship. Reply immediately with Aadhaar card photo, PAN card number, cancelled cheque for stipend.", 1),
    ("Download and Run Coding Assessment Tool (assessment.exe). "
     "Download and run attached assessment tool setup.exe. Disable antivirus software temporarily during installation to avoid false alarms.", 1)
]


def extract_ngrams(text: str) -> List[str]:
    """Extracts clean lowercase unigrams and bigrams from text."""
    # Normalize punctuation and find words
    words = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())
    clean_words = [w for w in words if w not in STOPWORDS]

    ngrams: List[str] = list(clean_words)
    # Generate bigrams
    for i in range(len(clean_words) - 1):
        bigram = f"{clean_words[i]}_{clean_words[i+1]}"
        ngrams.append(bigram)

    return ngrams


class ScamClassifier:
    """Pure-Python TF-IDF & Log-Odds Naive Bayes scam text classifier."""

    def __init__(self, model_path: Optional[Path | str] = None) -> None:
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.feature_weights: Dict[str, float] = {}
        self.bias: float = 0.0
        self._load_or_train()

    def _load_or_train(self) -> None:
        """Loads precomputed weights or fits from training samples."""
        if self.model_path.exists():
            try:
                with open(self.model_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.feature_weights = data.get("weights", {})
                    self.bias = data.get("bias", 0.0)
                    return
            except Exception as e:
                print(f"Warning: Could not load {self.model_path}: {e}. Retraining...")

        self.train_and_save()

    def train_and_save(self) -> None:
        """Computes smoothed log-odds ratios and persists model weights."""
        genuine_counts = Counter()
        scam_counts = Counter()
        n_genuine = 0
        n_scam = 0

        for text, label in TRAINING_SAMPLES:
            tokens = set(extract_ngrams(text))
            if label == 0:
                n_genuine += 1
                genuine_counts.update(tokens)
            else:
                n_scam += 1
                scam_counts.update(tokens)

        # Vocabulary of all observed tokens
        all_vocab = set(genuine_counts.keys()) | set(scam_counts.keys())
        alpha = 1.0  # Laplace smoothing parameter

        weights: Dict[str, float] = {}
        for token in all_vocab:
            # Smoothed probabilities
            p_token_given_scam = (scam_counts[token] + alpha) / (n_scam + 2 * alpha)
            p_token_given_genuine = (genuine_counts[token] + alpha) / (n_genuine + 2 * alpha)

            # Log-odds ratio: positive indicates scam, negative indicates genuine
            log_odds = math.log(p_token_given_scam / p_token_given_genuine)
            # Retain non-trivial weights
            if abs(log_odds) > 0.15:
                weights[token] = round(log_odds, 4)

        # Baseline class prior log-odds
        prior_scam = n_scam / (n_scam + n_genuine)
        prior_genuine = n_genuine / (n_scam + n_genuine)
        bias = math.log(prior_scam / prior_genuine)

        self.feature_weights = weights
        self.bias = round(bias, 4)

        # Ensure parent directory exists and save
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, "w", encoding="utf-8") as f:
            json.dump({"bias": self.bias, "weights": self.feature_weights}, f, indent=2)

    def predict_proba(self, text: str) -> float:
        """
        Calculates calibrated scam probability between 0.0 and 1.0 using sigmoid.
        """
        if not text or not text.strip():
            return 0.0

        tokens = extract_ngrams(text)
        if not tokens:
            return 0.0

        # Accumulate evidence
        z = self.bias
        matched_tokens = 0
        for token in set(tokens):
            if token in self.feature_weights:
                z += self.feature_weights[token]
                matched_tokens += 1

        # Sigmoid activation: 1 / (1 + exp(-z))
        # Clamp z to avoid overflow
        z_clamped = max(-20.0, min(20.0, z))
        prob = 1.0 / (1.0 + math.exp(-z_clamped))
        return round(prob, 4)


def fuse_scores(
    rule_score: int,
    ml_probability: float,
    hard_override: bool = False
) -> int:
    """
    Fuses deterministic heuristic rule score (65% weight) with ML text probability (35% weight).

    Formula:
        Final Score = round(0.65 * rule_score + 0.35 * (ml_probability * 100))

    Constraints:
    - If hard_override is True (e.g. domain blocklisted or fee + freemail),
      the rule_score is strictly preserved and cannot be diluted.
    - Clamped strictly between 0 and 100.
    """
    if hard_override:
        return max(0, min(100, int(rule_score)))

    ml_points = ml_probability * 100.0
    fused = 0.65 * rule_score + 0.35 * ml_points
    return max(0, min(100, round(fused)))


# Global singleton instance for high-speed inference
classifier = ScamClassifier()
