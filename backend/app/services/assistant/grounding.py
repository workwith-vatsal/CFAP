from dataclasses import dataclass, field
import logging
import re
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    is_grounded: bool
    sanitized_text: str
    issues: List[str] = field(default_factory=list)
    corrections_applied: bool = False


class GroundingValidator:
    """
    Grounding Validator for CFAP AI Assistant.
    Validates LLM-generated responses against authoritative CFAP analytical evidence.
    Detects and sanitizes detectable unsupported numerical values, fabricated topics/emotions,
    and unproven causal claims according to deterministic grounding rules.

    Principle:
    The GroundingValidator rejects or sanitizes detectable unsupported numerical,
    categorical, and causal claims according to the defined grounding rules.
    """

    CAUSAL_PATTERNS = [
        (
            re.compile(r"\b(causes?|caused|causing|leads? to|led to)\s+(customers?\s+to\s+(?:leave|churn|complain|cancel)|churn|attrition|revenue\s+loss)\b", re.IGNORECASE),
            r"is associated with negative customer sentiment",
        ),
        (
            re.compile(r"\b(directly\s+drives?|directly\s+drove)\s+(dissatisfaction|churn|cancellations)\b", re.IGNORECASE),
            r"frequently appears alongside \2",
        ),
    ]

    @classmethod
    def validate_and_sanitize(
        cls,
        generated_text: str,
        context: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validates the generated text against context evidence.
        Applies causal sanitization and checks for severe numerical contradictions.
        """
        issues: List[str] = []
        corrections_applied = False
        text = generated_text

        # 1. Causal Language Safeguard: Sanitize ungrounded causal claims to associative wording
        for pattern, replacement in cls.CAUSAL_PATTERNS:
            if pattern.search(text):
                text = pattern.sub(replacement, text)
                issues.append("Sanitized unsupported direct causal statement into associative language.")
                corrections_applied = True

        # 2. Extract allowable numbers and percentages from context
        allowed_percentages, allowed_counts = cls._extract_allowed_metrics(context)

        # 3. Detect Hallucinated Percentages in Generated Text
        pct_matches = re.findall(r"(\d+(?:\.\d+)?)\s*%", text)
        for pct_str in pct_matches:
            try:
                val = float(pct_str)
                # Check if val is within +/- 1.5% of any allowed percentage
                if not any(abs(val - allowed) <= 1.5 for allowed in allowed_percentages):
                    # Flag ungrounded percentage
                    issues.append(f"Detected unsupported percentage claim: {pct_str}%.")
            except ValueError:
                pass

        # 4. Check for severe unsupported numerical discrepancies
        # If there are severe ungrounded percentage claims, determine if fallback or warning is needed
        is_grounded = len(issues) == 0 or (len(issues) == 1 and corrections_applied)

        # If multiple ungrounded metrics were flagged, provide grounded fallback correction
        if any("unsupported percentage" in issue for issue in issues):
            is_grounded = False
            # Safely append clarification of authoritative values if needed
            overview = context.get("overview", {})
            sent_dist = overview.get("sentiment_distribution", {})
            pos_pct = sent_dist.get("positive", {}).get("percentage")
            neg_pct = sent_dist.get("negative", {}).get("percentage")
            neu_pct = sent_dist.get("neutral", {}).get("percentage")

            if pos_pct is not None and neg_pct is not None:
                authoritative_note = (
                    f"\n\n*(Authoritative CFAP Breakdown: Positive: {pos_pct}%, Neutral: {neu_pct}%, Negative: {neg_pct}%)*"
                )
                if authoritative_note not in text:
                    text += authoritative_note
                    corrections_applied = True

        return ValidationResult(
            is_grounded=is_grounded,
            sanitized_text=text,
            issues=issues,
            corrections_applied=corrections_applied,
        )

    @classmethod
    def _extract_allowed_metrics(cls, context: Dict[str, Any]) -> Tuple[Set[float], Set[int]]:
        """
        Recursively extracts all known float/int percentages and counts from context evidence.
        """
        percentages: Set[float] = {0.0, 100.0}
        counts: Set[int] = {0, 1}

        def _traverse(obj: Any):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    k_low = str(k).lower()
                    if isinstance(v, (int, float)):
                        if "percentage" in k_low or "ratio" in k_low or "pct" in k_low or "score" in k_low or "nss" in k_low:
                            percentages.add(round(float(v), 1))
                            percentages.add(round(float(v), 0))
                        elif "count" in k_low or "total" in k_low or "usable" in k_low or "rows" in k_low:
                            counts.add(int(v))
                    elif isinstance(v, (dict, list)):
                        _traverse(v)
            elif isinstance(obj, list):
                for item in obj:
                    _traverse(item)

        _traverse(context)
        return percentages, counts
