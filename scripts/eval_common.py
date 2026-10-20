"""Helpers shared by the eval validator and the result classifier."""

from __future__ import annotations

import re
import sys

# A scenario counts as skill-context-dependent when its text names one of these, and also one of
# the required terms below. Such scenarios are only fair as with-skill regression coverage.
SKILL_CONTEXT_TERMS = (
    "skill bundle",
    "skill package",
    "skill-provided",
    "skill-only context",
    "agent instructions",
    "from the skill",
    "bundled reference",
    "exact wording",
    "exact text",
    "exact checklist",
    "exact procedure",
    "exact command",
)
SKILL_CONTEXT_REQUIRED_TERMS = (
    "exact",
    "skill-provided",
    "skill-only context",
    "skill package",
    "agent instructions",
    "from the skill",
    "bundled reference",
)


def error(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def normalized_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def normalized(text: str) -> str:
    return " ".join(normalized_words(text))


def is_skill_context_dependent(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in SKILL_CONTEXT_TERMS) and any(
        term in lowered for term in SKILL_CONTEXT_REQUIRED_TERMS
    )
