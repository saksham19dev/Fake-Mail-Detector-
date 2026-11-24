"""Detection, normalization, and rules engines."""
from .normalizer import normalize_email_text
from .pii import redact_pii
from .parser import parse_features, EmailFeatures
from .rules import RulesEngine, Finding, RuleEvaluationResult

__all__ = [
    "normalize_email_text",
    "redact_pii",
    "parse_features",
    "EmailFeatures",
    "RulesEngine",
    "Finding",
    "RuleEvaluationResult",
]

