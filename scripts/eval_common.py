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

INVOCATIONS = ("natural", "explicit")
TASK_TYPES = ("implementation", "cleanup", "review")

# Phrases that say a scenario needs the skill's own text to be solved. A scenario whose task or
# criteria wording (see scenario_wording) uses one is only fair as with-skill regression coverage.
# docs/agents/evals.md lists the same phrases.
SKILL_CONTEXT_PHRASES = (
    "skill bundle",
    "the skill's",
    "as the skill says",
    "from the skill",
    "bundled",
)
SKILL_CONTEXT_PATTERNS = tuple(
    (phrase, re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)) for phrase in SKILL_CONTEXT_PHRASES
)


def error(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def normalized_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def normalized(text: str) -> str:
    return " ".join(normalized_words(text))


def skill_context_phrase(text: str) -> str | None:
    """Return the first phrase, as a whole word, that marks the text as needing the skill's words."""
    return next((phrase for phrase, pattern in SKILL_CONTEXT_PATTERNS if pattern.search(text)), None)


def checklist_items(data: dict[str, Any] | None) -> list[dict[str, Any]]:
    checklist = data.get("checklist") if data else None
    return [item for item in checklist if isinstance(item, dict)] if isinstance(checklist, list) else []


def scenario_wording(task_text: str, data: dict[str, Any] | None) -> str:
    """Return task.md plus the criteria context and every check's name and description."""
    parts = [task_text, str(data.get("context", "")) if data else ""]
    parts.extend(f"{item.get('name', '')} {item.get('description', '')}" for item in checklist_items(data))
    return "\n".join(parts)


def load_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{path}: invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return None, [f"{path}: the root must be an object"]
    return data, []


def load_criteria(criteria_file: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Load criteria.json and merge in criteria-meta.json from the same folder.

    Tessl's schema for criteria.json is context, type, and checklist items with name,
    description, and max_score. Everything this repository adds (invocation, task type,
    evidence type, per-item categories) lives in criteria-meta.json, so `tessl eval lint`
    stays clean. The merged view is what every check reads.
    """
    data, failures = load_json(criteria_file)
    if data is None:
        return None, failures
    if "metadata" in data:
        failures.append(f"{criteria_file}: move the metadata object to {SIDECAR_NAME}")
    if any("category" in item for item in checklist_items(data)):
        failures.append(f"{criteria_file}: move checklist categories to {SIDECAR_NAME}")
    data["metadata"] = {}
    sidecar_file = criteria_file.with_name(SIDECAR_NAME)
    if not sidecar_file.is_file():
        failures.append(f"{sidecar_file}: missing; it must carry metadata and categories")
        return data, failures
    sidecar, sidecar_failures = load_json(sidecar_file)
    failures.extend(sidecar_failures)
    if sidecar is not None:
        failures.extend(merge_sidecar(data, sidecar, sidecar_file))
    return data, failures


def merge_sidecar(data: dict[str, Any], sidecar: dict[str, Any], sidecar_file: Path) -> list[str]:
    """Copy metadata and per-check categories from criteria-meta.json into the criteria data."""
    failures: list[str] = []
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
    items = checklist_items(data)
    for name in sorted(set(categories) - {str(item.get("name")) for item in items}):
        failures.append(f"{sidecar_file}: category for unknown checklist item {name!r}")
    for item in items:
        category = categories.get(str(item.get("name")))
        if category is None:
            failures.append(f"{sidecar_file}: no category for checklist item {item.get('name')!r}")
        else:
            item["category"] = category
    data["metadata"] = metadata
    return failures
