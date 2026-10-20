"""Helpers shared by the eval validator and the result classifier."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

MAIN_SUITE = "evals"
REFERENCE_SUITE = "evals-reference"
REGRESSION_SUITE = "evals-regression"
SUITES = (MAIN_SUITE, REFERENCE_SUITE, REGRESSION_SUITE)
SIDECAR_NAME = "criteria-meta.json"

# Phrases that say a scenario needs the skill's own text to be solved. A scenario that uses one is
# only fair as with-skill regression coverage. docs/agents/evals.md lists the same phrases.
SKILL_CONTEXT_PHRASES = (
    "skill bundle",
    "the skill's",
    "as the skill says",
    "from the skill",
    "bundled",
)


def error(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def normalized_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def normalized(text: str) -> str:
    return " ".join(normalized_words(text))


def skill_context_phrase(text: str) -> str | None:
    """Return the first phrase that marks the text as needing the skill's own words, if any."""
    lowered = text.lower()
    return next((phrase for phrase in SKILL_CONTEXT_PHRASES if phrase in lowered), None)


def load_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{path}: invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return None, [f"{path}: the root must be an object"]
    return data, []


def load_criteria(criteria_file: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Load criteria.json and merge the repository metadata kept in criteria-meta.json.

    Tessl's schema for criteria.json is context, type, and checklist items with name,
    description, and max_score. Everything this repository adds (invocation, task type,
    evidence type, per-item categories) lives in criteria-meta.json next to it, so
    `tessl eval lint` stays clean. The merged view is what every check reads.
    """
    data, failures = load_json(criteria_file)
    if data is None:
        return None, failures
    if "metadata" in data:
        failures.append(f"{criteria_file}: move the metadata object to {SIDECAR_NAME}")
    checklist = data.get("checklist")
    items = [item for item in checklist if isinstance(item, dict)] if isinstance(checklist, list) else []
    if any("category" in item for item in items):
        failures.append(f"{criteria_file}: move checklist categories to {SIDECAR_NAME}")
    data["metadata"] = {}
    sidecar_file = criteria_file.with_name(SIDECAR_NAME)
    if not sidecar_file.is_file():
        failures.append(f"{sidecar_file}: missing; it must carry metadata and categories")
        return data, failures
    sidecar, sidecar_failures = load_json(sidecar_file)
    failures.extend(sidecar_failures)
    if sidecar is None:
        return data, failures
    unknown = sorted(set(sidecar) - {"metadata", "categories"})
    if unknown:
        failures.append(f"{sidecar_file}: unknown keys {unknown}; use metadata and categories")
    metadata = sidecar.get("metadata")
    if not isinstance(metadata, dict):
        failures.append(f"{sidecar_file}: metadata must be an object")
        metadata = {}
    categories = sidecar.get("categories")
    if not isinstance(categories, dict):
        failures.append(f"{sidecar_file}: categories must map checklist names to categories")
        categories = {}
    names = {str(item.get("name")) for item in items}
    for name in sorted(set(categories) - names):
        failures.append(f"{sidecar_file}: category for unknown checklist item {name!r}")
    for item in items:
        category = categories.get(str(item.get("name")))
        if category is None:
            failures.append(f"{sidecar_file}: no category for checklist item {item.get('name')!r}")
        else:
            item["category"] = category
    data["metadata"] = metadata
    return data, failures
