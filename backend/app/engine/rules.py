"""OfferCheck Heuristic Rules Engine.

Loads detection rules from rules.yaml, executes regex pattern evaluation with
contextual negation awareness, evaluates header/sender signals, extracts evidence,
and enforces hard override constraints.
"""
from pathlib import Path
import re
from typing import List, Optional, Dict, Any
import yaml
from pydantic import BaseModel, Field

from .parser import EmailFeatures

# Negation & protective disclaimer window (characters to inspect before a match)
NEGATION_WINDOW_CHARS = 65

# Regex identifying defensive disclaimers rather than scammer demands
NEGATION_CONTEXT_REGEX = re.compile(
    r"(?:"
    r"never\s*(?:ask|charge|request|demand|require|take|collect)?|"
    r"do\s*not\s*(?:pay|transfer|send|share|disclose|give)?|"
    r"don't\s*(?:pay|transfer|send|share|disclose|give)?|"
    r"not\s*(?:require|charge|ask|demand)?|"
    r"no\s*(?:fee|deposit|charge|money|payment)?|"
    r"free\s*of\s*(?:cost|charge)|"
    r"caution:|warning:|beware\s*of|"
    r"we\s*(?:will\s*never|do\s*not)\b"
    r")",
    re.IGNORECASE
)


class Finding(BaseModel):
    """An individual finding identified by the rules engine."""
    rule_id: str
    rule_name: str
    category: str
    level: str  # "red_flag", "caution", "good_sign"
    weight: int
    confidence: float = 1.0
    evidence: str
    explanation: str


class Rule(BaseModel):
    """Rule definition loaded from rules.yaml."""
    id: str
    name: str
    category: str
    level: str
    weight: int
    is_payment_demand: bool = False
    description: str
    explanation: str
    patterns: List[str] = Field(default_factory=list)
    compiled_patterns: List[re.Pattern] = Field(default_factory=list, exclude=True)


class RuleEvaluationResult(BaseModel):
    """Aggregate result from rules engine execution."""
    raw_score: int
    score: int  # Clamped 0-100
    findings: List[Finding] = Field(default_factory=list)
    is_payment_demand: bool = False
    is_free_mail: bool = False
    hard_override_triggered: bool = False
    hard_override_reason: Optional[str] = None


class RulesEngine:
    """Core heuristic evaluation engine."""

    def __init__(self, rules_path: Optional[str | Path] = None) -> None:
        if rules_path is None:
            rules_path = Path(__file__).parent.parent / "rules.yaml"
        self.rules_path = Path(rules_path)
        self.rules: Dict[str, Rule] = {}
        self.load_rules()

    def load_rules(self) -> None:
        """Load rules from YAML and compile regex patterns."""
        if not self.rules_path.exists():
            raise FileNotFoundError(f"Rules definition file not found: {self.rules_path}")

        with open(self.rules_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        rules_list = data.get("rules", [])
        self.rules.clear()

        for r_dict in rules_list:
            rule = Rule(**r_dict)
            compiled = []
            for p_str in rule.patterns:
                try:
                    compiled.append(re.compile(p_str, re.IGNORECASE))
                except re.error as err:
                    print(f"Warning: Failed to compile pattern '{p_str}' in rule {rule.id}: {err}")
            rule.compiled_patterns = compiled
            self.rules[rule.id] = rule

    def evaluate(
        self,
        features: EmailFeatures,
        is_domain_blocklisted: bool = False
    ) -> RuleEvaluationResult:
        """Evaluate features against all loaded rules."""
        combined_text = f"{features.subject}\n\n{features.body}"
        findings: List[Finding] = []
        raw_score = 0
        has_payment_demand = False

        # ----------------------------------------------------------------------
        # 1. Evaluate Text Pattern Rules
        # ----------------------------------------------------------------------
        for rule in self.rules.values():
            if not rule.compiled_patterns:
                continue

            for pat in rule.compiled_patterns:
                match = pat.search(combined_text)
                if not match:
                    continue

                # Contextual Negation Guard:
                # Check preceding window to prevent flagging defensive warnings
                start_idx = match.start()
                prefix = combined_text[max(0, start_idx - NEGATION_WINDOW_CHARS):start_idx]
                if NEGATION_CONTEXT_REGEX.search(prefix):
                    # Suppressed as an advisory statement
                    continue

                # Valid match found
                matched_snippet = match.group(0).strip()
                # Create surrounding snippet evidence (up to 30 chars around match)
                snippet_start = max(0, start_idx - 25)
                snippet_end = min(len(combined_text), match.end() + 25)
                evidence = combined_text[snippet_start:snippet_end].replace("\n", " ").strip()

                if rule.is_payment_demand:
                    has_payment_demand = True

                raw_score += rule.weight

                findings.append(Finding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    category=rule.category,
                    level=rule.level,
                    weight=rule.weight,
                    confidence=1.0,
                    evidence=f"...{evidence}..." if snippet_start > 0 else f"{evidence}...",
                    explanation=rule.explanation,
                ))
                # Only record rule once even if multiple patterns match
                break

        # ----------------------------------------------------------------------
        # 2. Evaluate Sender & Header Specific Rules
        # ----------------------------------------------------------------------
        # Free-mail sender check
        if features.is_free_mail and "RULE_FREE_MAIL_SENDER" in self.rules:
            r = self.rules["RULE_FREE_MAIL_SENDER"]
            raw_score += r.weight
            findings.append(Finding(
                rule_id=r.id,
                rule_name=r.name,
                category=r.category,
                level=r.level,
                weight=r.weight,
                confidence=1.0,
                evidence=f"Sender address: {features.sender} (domain: @{features.sender_domain})",
                explanation=r.explanation,
            ))

        # Reply-To domain mismatch check
        if features.reply_to_mismatch and "RULE_REPLYTO_MISMATCH" in self.rules:
            r = self.rules["RULE_REPLYTO_MISMATCH"]
            raw_score += r.weight
            findings.append(Finding(
                rule_id=r.id,
                rule_name=r.name,
                category=r.category,
                level=r.level,
                weight=r.weight,
                confidence=1.0,
                evidence=f"From: @{features.sender_domain} vs Reply-To: @{features.reply_to_domain}",
                explanation=r.explanation,
            ))

        # Email authentication failure check (SPF / DKIM / DMARC)
        auth = features.auth
        if (auth.spf == "fail" or auth.dkim == "fail" or auth.dmarc == "fail") and "RULE_AUTH_FAILURE" in self.rules:
            r = self.rules["RULE_AUTH_FAILURE"]
            raw_score += r.weight
            failed_protocols = []
            if auth.spf == "fail": failed_protocols.append("SPF: FAIL")
            if auth.dkim == "fail": failed_protocols.append("DKIM: FAIL")
            if auth.dmarc == "fail": failed_protocols.append("DMARC: FAIL")
            findings.append(Finding(
                rule_id=r.id,
                rule_name=r.name,
                category=r.category,
                level=r.level,
                weight=r.weight,
                confidence=1.0,
                evidence=", ".join(failed_protocols),
                explanation=r.explanation,
            ))

        # ----------------------------------------------------------------------
        # 3. Score Normalization & Hard Overrides
        # ----------------------------------------------------------------------
        final_score = raw_score
        hard_override = False
        override_reason = None

        # Hard Override A: Blocklisted domain => 100
        if is_domain_blocklisted:
            final_score = 100
            hard_override = True
            override_reason = "Sender domain is blocklisted for verified fraud."

        # Hard Override B: Payment request + free-mail sender => at least 75
        elif has_payment_demand and features.is_free_mail:
            if final_score < 75:
                final_score = 75
            hard_override = True
            override_reason = "Payment request originating from a personal free webmail provider."

        # Hard Override C: Payment demand in general forces at least 70
        elif has_payment_demand and final_score < 70:
            final_score = 70
            hard_override = True
            override_reason = "Upfront payment or deposit requested for internship offer."

        # Clamp strictly between 0 and 100
        clamped_score = max(0, min(100, final_score))

        return RuleEvaluationResult(
            raw_score=raw_score,
            score=clamped_score,
            findings=findings,
            is_payment_demand=has_payment_demand,
            is_free_mail=features.is_free_mail,
            hard_override_triggered=hard_override,
            hard_override_reason=override_reason,
        )

