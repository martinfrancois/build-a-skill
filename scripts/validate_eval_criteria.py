#!/usr/bin/env python3
"""Validate local Tessl scenario evals.

This is a repository guardrail, not a replacement for official Tessl lint or hosted evals.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def detect_skill_name() -> str:
    """Return the skill under test: $SKILL_NAME, or the only folder in skills/."""
    configured = os.environ.get("SKILL_NAME", "").strip()
    if configured:
        return configured
    found = sorted(path.parent.name for path in Path("skills").glob("*/SKILL.md"))
    if len(found) == 1:
        return found[0]
    raise SystemExit(
        f"error: found {len(found)} skills under skills/; set SKILL_NAME to the one to validate"
    )


SKILL_NAME = detect_skill_name()
SKILL_ROOT = Path("skills") / SKILL_NAME
# Every task.md must contain a line like "Assume Python 3.12." so both variants target the same
# version or environment.
ENVIRONMENT_PATTERN = re.compile(r"^Assume\s+\S.*$|[.!?]\s+Assume\s+\S", re.MULTILINE)
# Identifiers every task in this skill's domain is expected to share with the runtime references:
# language keywords, standard library names, and common words of the domain. Overlap on them is
# not a leak, so the runtime-reference overlap check ignores them. Fill in your domain's
# identifiers here when you replace the example convention.
DOMAIN_IDENTIFIERS = {
    "assert",
    "class",
    "cause",
    "def",
    "elif",
    "else",
    "error",
    "errors",
    "except",
    "exception",
    "false",
    "from",
    "import",
    "logger",
    "logging",
    "message",
    "none",
    "null",
    "raise",
    "return",
    "self",
    "string",
    "this",
    "throw",
    "true",
    "type",
    "with",
    # Example domain: error messages. Standard exception names and the words the convention
    # itself requires or bans.
    "connectionerror",
    "expected",
    "failed",
    "invalid",
    "permissionerror",
    "runtimeerror",
    "timeouterror",
    "valueerror",
}
ANSWER_KEY_MARKERS = (
    "Eval Cases",
    "Eval Scoring Rubric",
    "Scoring Rubric",
    "Expected:",
    "Rejected:",
    "hosted run",
    "run id",
    "scenario inventory",
    "baseline score",
    "uplift",
    "answer key",
)
COMPILE_WORDS = ("compile", "compiles", "coherent", "artifact", "creates")
BEHAVIOR_WORDS = (
    "behavior",
    "preserve",
    "exact",
    "return",
    "returns",
    "exception",
    "prompt",
    "output",
    "order",
    "lazy",
    "laziness",
    "side effect",
    "fallback",
    "parse",
    "redact",
)
CRITERION_CATEGORIES = {"safety", "quality", "maintainability"}
EVIDENCE_TYPES = {
    "ordinary_lift",
    "focused_main",
    "focused_reference",
    "solved_regression",
    "skill_context_dependent",
}
REGRESSION_EVIDENCE_TYPES = {"solved_regression", "skill_context_dependent"}
INTERNAL_LABEL_ALLOW_PATTERNS = (
    r"\bdo not deduct\b.{0,120}\b(?:hard[- ]stop|checklist|scan|marker|skill)\b",
    r"\baward full credit\b.{0,120}\b(?:hard[- ]stop|checklist|scan|marker|skill)\b",
    r"\ballow(?:s|ed)?\b.{0,120}\b(?:hard[- ]stop|checklist|scan|marker|skill)\b",
    r"\bbrief(?:ly)? uses\b.{0,120}\b(?:hard[- ]stop|checklist|scan|marker|skill)\b",
)
EXPLICIT_INVOCATION_PATTERNS = (
    rf"\${re.escape(SKILL_NAME)}\b",
    rf"(?:^|\s)/{re.escape(SKILL_NAME)}\b",
    rf"\buse\s+{re.escape(SKILL_NAME)}\b",
    rf"\buse\s+the\s+{re.escape(SKILL_NAME)}\s+skill\b",
    rf"\b{re.escape(SKILL_NAME)}\s+skill\b",
)

# README.md is left out on purpose: it names the example scenarios that a new skill replaces.
SCENARIO_REFERENCE_FILES = (
    Path("AGENTS.md"),
    Path("evals/NUMBERING.md"),
)
SCENARIO_REFERENCE_DIRS = (Path("docs"),)
AGENT_DOC_FORBIDDEN_EXTERNAL_HISTORY_PATTERNS = (
    re.compile(r"\bissue\s+#?\d+\b", re.IGNORECASE),
    re.compile(r"\bpr\s+#?\d+\b", re.IGNORECASE),
    re.compile(r"https://github\.com/[^)\s]+/(?:issues|pull)/\d+", re.IGNORECASE),
    re.compile(r"\b01[0-9a-f]{6}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE),
)


def error(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def scenario_dirs(paths: list[Path]) -> list[Path]:
    dirs: list[Path] = []
    for path in paths:
        if path.is_file() and path.name == "criteria.json":
            dirs.append(path.parent)
        elif path.is_dir():
            if (path / "criteria.json").is_file():
                dirs.append(path)
            else:
                children = sorted(child for child in path.iterdir() if child.is_dir())
                dirs.extend(children)
        else:
            raise FileNotFoundError(path)
    return sorted(dict.fromkeys(dirs))


def load_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{path}: invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return None, [f"{path}: criteria root must be an object"]
    return data, []


SIDECAR_NAME = "criteria-meta.json"


def load_criteria(criteria_file: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Load criteria.json and merge the repository metadata kept in criteria-meta.json.

    Tessl's schema for criteria.json is context, type, and checklist items with name,
    description, and max_score. Everything this repository adds (invocation, task type,
    evidence type, selection notes, per-item categories) lives in criteria-meta.json next to
    it, so `tessl eval lint` stays clean. The merged view is what every validator reads.
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
    sidecar_file = criteria_file.with_name(SIDECAR_NAME)
    if not sidecar_file.is_file():
        failures.append(f"{sidecar_file}: missing; it must carry metadata and categories")
        data.setdefault("metadata", {})
        return data, failures
    sidecar, sidecar_failures = load_json(sidecar_file)
    failures.extend(sidecar_failures)
    if sidecar is None:
        data.setdefault("metadata", {})
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


def invocation_from_task(task_text: str) -> bool:
    return any(re.search(pattern, task_text, re.IGNORECASE) for pattern in EXPLICIT_INVOCATION_PATTERNS)


def text_of(item: dict[str, Any]) -> str:
    return f"{item.get('name', '')} {item.get('description', '')}".lower()


def normalized_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def normalized_text(text: str) -> str:
    return " ".join(normalized_words(text))


def ngrams(words: list[str], size: int) -> set[tuple[str, ...]]:
    if len(words) < size:
        return set()
    return {tuple(words[index : index + size]) for index in range(len(words) - size + 1)}


def code_like_text(text: str) -> str:
    chunks = re.findall(r"```(?:[A-Za-z0-9_-]+)?\n(.*?)```", text, flags=re.DOTALL)
    chunks.extend(re.findall(r"`([^`\n]+)`", text))
    return "\n".join(chunks)


def task_similarity(left: str, right: str) -> float:
    left_words = normalized_words(left)
    right_words = normalized_words(right)
    left_text = " ".join(left_words)
    right_text = " ".join(right_words)
    if not left_text or not right_text:
        return 0.0
    exact_ratio = 1.0 if left_text == right_text else 0.0
    left_grams = ngrams(left_words, 8)
    right_grams = ngrams(right_words, 8)
    if not left_grams or not right_grams:
        return exact_ratio
    overlap = len(left_grams & right_grams) / min(len(left_grams), len(right_grams))
    return max(exact_ratio, overlap)


def domain_identifiers(text: str) -> set[str]:
    identifiers = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", code_like_text(text)))
    result: set[str] = set()
    for identifier in identifiers:
        lowered = identifier.lower()
        if lowered in DOMAIN_IDENTIFIERS or len(identifier) < 4:
            continue
        if identifier.isupper() and len(identifier) <= 6:
            continue
        result.add(identifier)
    return result


def api_markers(text: str) -> set[str]:
    markers = set(
        re.findall(
            r"\b[A-Z][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+\b"
            r"|\b[A-Za-z_][A-Za-z0-9_]*::[A-Za-z_][A-Za-z0-9_]*\b",
            text,
        )
    )
    return {marker for marker in markers if marker not in {"System.out"}}


def is_skill_context_dependent_text(text: str) -> bool:
    lowered = text.lower()
    context_terms = (
        "skill bundle",
        "skill package",
        "skill-provided",
        "skill-only context",
        "agent instructions",
        "from the skill",
        "from the skill bundle",
        "bundled reference",
        "bundled reference text",
        "exact skill-provided text",
        "exact wording",
        "exact text",
        "exact scan",
        "exact scan header",
        "exact checklist",
        "exact procedure",
        "exact command",
        "scan command from the skill",
    )
    required_terms = (
        "exact",
        "skill-provided",
        "skill-only context",
        "skill package",
        "agent instructions",
        "from the skill",
        "bundled reference",
    )
    return any(term in lowered for term in context_terms) and any(
        term in lowered for term in required_terms
    )


def validate_scenario(scenario: Path, main_eval_root: Path | None) -> list[str]:
    failures: list[str] = []
    task_file = scenario / "task.md"
    criteria_file = scenario / "criteria.json"
    capability_file = scenario / "capability.txt"

    if not task_file.is_file():
        failures.append(f"{scenario}: missing task.md")
    if not criteria_file.is_file():
        failures.append(f"{scenario}: missing criteria.json")
    if not capability_file.is_file():
        failures.append(f"{scenario}: missing capability.txt")
    elif not capability_file.read_text(encoding="utf-8").strip():
        failures.append(f"{capability_file}: capability must be non-empty")

    if not criteria_file.is_file():
        return failures

    data, json_failures = load_criteria(criteria_file)
    failures.extend(json_failures)
    if data is None:
        return failures

    if data.get("type") != "weighted_checklist":
        failures.append(f"{criteria_file}: type must be weighted_checklist")
    context = data.get("context")
    if (
        scenario.parent.name in {"evals-reference", "evals-regression"}
        and isinstance(context, str)
        and context.startswith("Main eval")
    ):
        failures.append(f"{criteria_file}: reference/regression scenario context must not start with 'Main eval'")

    checklist = data.get("checklist")
    if not isinstance(checklist, list) or not checklist:
        failures.append(f"{criteria_file}: checklist must be a non-empty array")
        checklist = []

    is_main_eval = main_eval_root is not None and scenario.parent.resolve() == main_eval_root.resolve()
    names: set[str] = set()
    total_score = 0
    compile_score = 0
    behavior_score = 0
    category_scores = {category: 0 for category in CRITERION_CATEGORIES}
    for index, item in enumerate(checklist, start=1):
        if not isinstance(item, dict):
            failures.append(f"{criteria_file}: checklist item {index} must be an object")
            continue
        name = item.get("name")
        description = item.get("description")
        max_score = item.get("max_score")
        if not isinstance(name, str) or not name.strip():
            failures.append(f"{criteria_file}: checklist item {index} needs a non-empty name")
            name = f"<item {index}>"
        if name in names:
            failures.append(f"{criteria_file}: duplicate criterion name: {name}")
        names.add(str(name))
        if not isinstance(description, str) or not description.strip():
            failures.append(f"{criteria_file}: checklist item {index} needs a non-empty description")
        if not isinstance(max_score, int) or max_score <= 0:
            failures.append(f"{criteria_file}: checklist item {index} needs a positive integer max_score")
            max_score = 0
        category = item.get("category")
        if category is not None and category not in CRITERION_CATEGORIES:
            failures.append(
                f"{criteria_file}: checklist item {index} has unsupported category {category!r}; "
                f"use one of {sorted(CRITERION_CATEGORIES)}"
            )
        if is_main_eval and category not in CRITERION_CATEGORIES:
            failures.append(
                f"{criteria_file}: main eval checklist item {index} needs category "
                f"safety, quality, or maintainability"
            )
        total_score += max_score
        if category in category_scores:
            category_scores[category] += max_score
        haystack = text_of(item)
        if any(word in haystack for word in COMPILE_WORDS):
            compile_score += max_score
        if any(word in haystack for word in BEHAVIOR_WORDS):
            behavior_score += max_score

    task_text = task_file.read_text(encoding="utf-8") if task_file.is_file() else ""
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        failures.append(f"{criteria_file}: missing metadata object")
        metadata = {}
    invocation = metadata.get("invocation")
    task_type = metadata.get("task_type")
    evidence_type = metadata.get("evidence_type")
    if invocation not in {"natural", "explicit"}:
        failures.append(f"{criteria_file}: metadata.invocation must be natural or explicit")
    if task_type not in {"implementation", "cleanup", "review"}:
        failures.append(f"{criteria_file}: metadata.task_type must be implementation, cleanup, or review")
    if evidence_type is not None and evidence_type not in EVIDENCE_TYPES:
        failures.append(
            f"{criteria_file}: metadata.evidence_type must be one of {sorted(EVIDENCE_TYPES)}"
        )
    if scenario.parent.name == "evals-regression" and evidence_type not in REGRESSION_EVIDENCE_TYPES:
        failures.append(
            f"{criteria_file}: regression scenarios must set metadata.evidence_type to "
            "solved_regression or skill_context_dependent"
        )
    scenario_text = f"{scenario.name}\n{task_text}\n{json.dumps(data, sort_keys=True)}"
    detected_skill_context = is_skill_context_dependent_text(scenario_text)
    if evidence_type == "skill_context_dependent" and scenario.parent.name != "evals-regression":
        failures.append(
            f"{criteria_file}: metadata.evidence_type=skill_context_dependent must live in evals-regression"
        )
    if evidence_type == "solved_regression" and scenario.parent.name != "evals-regression":
        failures.append(
            f"{criteria_file}: metadata.evidence_type=solved_regression must live in evals-regression"
        )
    if evidence_type == "focused_reference" and scenario.parent.name != "evals-reference":
        failures.append(
            f"{criteria_file}: metadata.evidence_type=focused_reference must live in evals-reference"
        )
    if evidence_type == "focused_main" and scenario.parent.name != "evals":
        failures.append(
            f"{criteria_file}: metadata.evidence_type=focused_main must live in evals"
        )
    if evidence_type == "ordinary_lift" and scenario.parent.name == "evals-regression":
        failures.append(
            f"{criteria_file}: metadata.evidence_type=ordinary_lift must live in evals or evals-reference"
        )
    if evidence_type != "skill_context_dependent" and detected_skill_context:
        failures.append(
            f"{criteria_file}: scenario appears skill-context-dependent; set "
            "metadata.evidence_type to skill_context_dependent and keep it in evals-regression"
        )
    if evidence_type != "skill_context_dependent" and task_type == "review":
        for index, item in enumerate(checklist, start=1):
            if not isinstance(item, dict):
                continue
            criterion_text = text_of(item)
            if any(re.search(pattern, criterion_text) for pattern in INTERNAL_LABEL_ALLOW_PATTERNS):
                failures.append(
                    f"{criteria_file}: checklist item {index} appears to allow internal workflow "
                    "labels in ordinary review output; prohibit them or move the scenario to "
                    "skill-context-dependent regression if exact workflow wording is required"
                )

    if task_text and not ENVIRONMENT_PATTERN.search(task_text):
        failures.append(
            f"{task_file}: task must state the version or environment to assume, "
            "e.g. 'Assume Python 3.12.'"
        )
    has_explicit_invocation = invocation_from_task(task_text)
    if invocation == "natural" and has_explicit_invocation:
        failures.append(f"{task_file}: natural scenario explicitly invokes the skill")
    if invocation == "explicit" and not has_explicit_invocation:
        failures.append(f"{criteria_file}: explicit scenario task does not invoke the skill")

    if is_main_eval and task_type == "implementation":
        if compile_score <= 0:
            failures.append(f"{criteria_file}: main eval implementation scenario needs compile/artifact criteria")
        if behavior_score <= 0:
            failures.append(f"{criteria_file}: main eval implementation scenario needs behavior criteria")
        if category_scores["quality"] <= 0:
            failures.append(f"{criteria_file}: main eval implementation scenario needs quality criteria")
    elif is_main_eval and task_type == "cleanup" and category_scores["quality"] <= 0:
        failures.append(f"{criteria_file}: main eval cleanup scenario needs quality criteria")

    return failures


def validate_cross_suite_duplicates(dirs: list[Path]) -> list[str]:
    failures: list[str] = []
    active = [scenario for scenario in dirs if scenario.parent.name == "evals"]
    reference = [
        scenario
        for scenario in dirs
        if scenario.parent.name in {"evals-reference", "evals-regression"}
    ]
    for active_scenario in active:
        active_task = (active_scenario / "task.md").read_text(encoding="utf-8")
        for reference_scenario in reference:
            reference_task = (reference_scenario / "task.md").read_text(encoding="utf-8")
            similarity = task_similarity(active_task, reference_task)
            if similarity >= 0.85:
                failures.append(
                    f"{active_scenario}: task.md is too similar to {reference_scenario} "
                    f"(normalized task overlap {similarity:.2f})"
                )
    return failures


def validate_runtime_reference_overlap(dirs: list[Path]) -> list[str]:
    failures: list[str] = []
    references_root = SKILL_ROOT / "references"
    if not references_root.exists():
        return failures

    runtime_text = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(references_root.glob("*.md"))
    )
    runtime_identifiers = domain_identifiers(runtime_text)
    runtime_grams = ngrams(normalized_words(runtime_text), 12)
    runtime_api_markers = api_markers(runtime_text)

    for scenario in dirs:
        suite = scenario.parent.name
        if suite not in {"evals", "evals-reference", "evals-regression"}:
            continue
        task_file = scenario / "task.md"
        criteria_file = scenario / "criteria.json"
        if not task_file.exists():
            continue
        task_text = task_file.read_text(encoding="utf-8")
        metadata: dict[str, Any] = {}
        if criteria_file.exists():
            data, _ = load_criteria(criteria_file)
            if isinstance(data, dict) and isinstance(data.get("metadata"), dict):
                metadata = data["metadata"]

        task_identifiers = domain_identifiers(task_text)
        shared_identifiers = sorted(task_identifiers & runtime_identifiers)
        task_words = normalized_words(task_text)
        task_grams = ngrams(task_words, 12)
        long_overlap_count = len(task_grams & runtime_grams)
        shared_api_markers = sorted(api_markers(task_text) & runtime_api_markers)
        has_distinctive_api_overlap = bool(shared_api_markers) and len(shared_identifiers) >= 2

        has_overlap = (
            len(shared_identifiers) >= 4
            or (len(shared_identifiers) >= 3 and long_overlap_count)
            or has_distinctive_api_overlap
        )
        if not has_overlap:
            continue

        evidence_type = metadata.get("evidence_type")
        rationale = metadata.get("runtime_reference_overlap_rationale")
        has_overlap_rationale = isinstance(rationale, str) and bool(rationale.strip())
        overlap_details = (
            f"shared identifiers: {', '.join(shared_identifiers[:12]) or '(none)'}; "
            f"shared API markers: {', '.join(shared_api_markers[:12]) or '(none)'}"
        )

        if evidence_type == "ordinary_lift":
            failures.append(
                f"{scenario}: metadata.evidence_type=ordinary_lift is incompatible with "
                f"runtime-reference overlap ({overlap_details}); de-domain the task/reference or "
                "reclassify the evidence so it is not reported as ordinary broad lift"
            )
            continue

        if suite == "evals":
            if evidence_type != "focused_main":
                failures.append(
                    f"{scenario}: main eval task overlaps runtime references ({overlap_details}); "
                    "de-domain the task/reference or set metadata.evidence_type=focused_main so "
                    "it is not reported as ordinary broad natural lift"
                )
            elif not has_overlap_rationale:
                failures.append(
                    f"{criteria_file}: focused main eval with runtime-reference overlap must set "
                    "metadata.runtime_reference_overlap_rationale"
                )
        elif suite == "evals-reference":
            if evidence_type != "focused_reference":
                failures.append(
                    f"{scenario}: reference task overlaps runtime references ({overlap_details}); "
                    "de-domain the task/reference or set metadata.evidence_type=focused_reference "
                    "so it is not reported as ordinary broad lift"
                )
            elif not has_overlap_rationale:
                failures.append(
                    f"{criteria_file}: focused reference eval with runtime-reference overlap must set "
                    "metadata.runtime_reference_overlap_rationale"
                )
        elif suite == "evals-regression" and evidence_type not in REGRESSION_EVIDENCE_TYPES:
            failures.append(
                f"{scenario}: regression task overlaps runtime references ({overlap_details}); "
                "classify it as solved_regression or skill_context_dependent regression evidence"
            )
    return failures


def validate_scenario_path_references() -> list[str]:
    failures: list[str] = []
    files = [path for path in SCENARIO_REFERENCE_FILES if path.exists()]
    for directory in SCENARIO_REFERENCE_DIRS:
        if directory.exists():
            files.extend(sorted(directory.rglob("*.md")))

    pattern = re.compile(r"`?((?:evals|evals-reference|evals-regression)/[A-Za-z0-9_.\-/]+)`?")
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            candidate = match.group(1).rstrip(".,);:")
            if "*" in candidate:
                continue
            if not Path(candidate).exists():
                failures.append(f"{path}: stale scenario path reference {candidate!r}")
    return failures


def validate_runtime_references() -> list[str]:
    failures: list[str] = []
    root = SKILL_ROOT / "references"
    if not root.exists():
        return failures
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for marker in ANSWER_KEY_MARKERS:
            if marker.lower() in text.lower():
                failures.append(f"{path}: runtime reference contains answer-key marker {marker!r}")
    legacy = SKILL_ROOT / "evals" / "evals.json"
    if legacy.exists():
        failures.append(f"{legacy}: eval files must not live inside the skill folder")
    return failures


def validate_agent_docs_self_contained() -> list[str]:
    failures: list[str] = []
    root = Path("docs/agents")
    if not root.exists():
        return failures
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for pattern in AGENT_DOC_FORBIDDEN_EXTERNAL_HISTORY_PATTERNS:
            match = pattern.search(text)
            if match:
                failures.append(
                    f"{path}: docs/agents must be self-contained; remove external history "
                    f"reference {match.group(0)!r}"
                )
    return failures


def validate_numbering(root: Path) -> list[str]:
    failures: list[str] = []
    if not root.exists():
        return failures
    numbers: dict[int, str] = {}
    documented_gap = root / "NUMBERING.md"
    for scenario in sorted(child for child in root.iterdir() if child.is_dir()):
        match = re.match(r"^(\d+)-", scenario.name)
        if not match:
            continue
        number = int(match.group(1))
        if number in numbers:
            failures.append(f"{root}: duplicate scenario number {number:02d}: {numbers[number]}, {scenario.name}")
        numbers[number] = scenario.name
    if numbers and not documented_gap.exists():
        all_numbers = sorted(numbers)
        expected = set(range(all_numbers[0], all_numbers[-1] + 1))
        missing = sorted(expected - set(all_numbers))
        if missing:
            failures.append(f"{root}: numbering gap(s) {missing}; add NUMBERING.md if intentional")
    return failures


def main() -> int:
    if len(sys.argv) < 2:
        return error("usage: validate_eval_criteria.py <eval-directory-or-criteria.json> [...]")

    paths = [Path(arg) for arg in sys.argv[1:]]
    try:
        dirs = scenario_dirs(paths)
    except FileNotFoundError as exc:
        return error(f"path not found: {exc.filename}")
    if not dirs:
        return error("no scenario directories found")

    main_eval_root = Path("evals") if Path("evals").exists() else None
    failures: list[str] = []
    invocations: dict[str, int] = {"natural": 0, "explicit": 0}
    for scenario in dirs:
        failures.extend(validate_scenario(scenario, main_eval_root))
        criteria = scenario / "criteria.json"
        if criteria.exists():
            data, _ = load_criteria(criteria)
            if data and isinstance(data.get("metadata"), dict):
                invocation = data["metadata"].get("invocation")
                if invocation in invocations:
                    invocations[invocation] += 1

    if main_eval_root and any(path.resolve() == main_eval_root.resolve() for path in paths if path.exists()):
        main_eval_dirs = [d for d in dirs if d.parent.resolve() == main_eval_root.resolve()]
        main_eval_invocations = {"natural": 0, "explicit": 0}
        main_eval_category_scores = {category: 0 for category in CRITERION_CATEGORIES}
        for scenario in main_eval_dirs:
            data, _ = load_criteria(scenario / "criteria.json")
            if data and isinstance(data.get("metadata"), dict):
                invocation = data["metadata"].get("invocation")
                if invocation in main_eval_invocations:
                    main_eval_invocations[invocation] += 1
            if data and isinstance(data.get("checklist"), list):
                for item in data["checklist"]:
                    if not isinstance(item, dict):
                        continue
                    category = item.get("category")
                    max_score = item.get("max_score")
                    if category in main_eval_category_scores and isinstance(max_score, int):
                        main_eval_category_scores[category] += max_score
        # One scenario cannot cover both styles; from the second scenario on, the set must.
        if len(main_eval_dirs) >= 2 and not all(main_eval_invocations.values()):
            failures.append(
                "evals: main eval set must include both natural and explicit invocation scenarios"
            )
        main_eval_total = sum(main_eval_category_scores.values())
        if main_eval_total:
            quality = main_eval_category_scores["quality"]
            safety = main_eval_category_scores["safety"]
            maintainability = main_eval_category_scores["maintainability"]
            if quality < main_eval_total * 0.8:
                failures.append(
                    "evals: main eval set should be primarily quality scoring "
                    f"({quality}/{main_eval_total})"
                )
            if safety < main_eval_total * 0.05:
                failures.append(
                    "evals: main eval set needs enough safety-check scoring for compile/behavior "
                    f"({safety}/{main_eval_total})"
                )
            if maintainability < main_eval_total * 0.05:
                failures.append(
                    "evals: main eval set needs enough maintainability scoring "
                    f"({maintainability}/{main_eval_total})"
                )
            if maintainability > main_eval_total * 0.15:
                failures.append(
                    "evals: main eval maintainability scoring should not obscure skill behavior "
                    f"({maintainability}/{main_eval_total})"
                )

    for path in paths:
        if path.is_dir():
            failures.extend(validate_numbering(path))
    failures.extend(validate_cross_suite_duplicates(dirs))
    failures.extend(validate_runtime_reference_overlap(dirs))
    failures.extend(validate_scenario_path_references())
    failures.extend(validate_runtime_references())
    failures.extend(validate_agent_docs_self_contained())

    if failures:
        for failure in failures:
            print(f"error: {failure}", file=sys.stderr)
        return 1

    print(
        f"Validated {len(dirs)} scenario(s): "
        f"{invocations['natural']} natural, {invocations['explicit']} explicit."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
