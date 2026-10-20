#!/usr/bin/env python3
"""Validate local Tessl scenario evals.

This is a repository guardrail, not a replacement for official Tessl lint or hosted evals.
Paths on the command line are read from the current directory; everything else is read from
the repository that contains this script, so it runs from any directory.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from eval_common import (
    MAIN_SUITE,
    REFERENCE_SUITE,
    REGRESSION_SUITE,
    SUITES,
    error,
    load_criteria,
    normalized_words,
    skill_context_phrase,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CALLER_CWD = Path.cwd()
os.chdir(REPO_ROOT)

# Identifiers every task in this skill's domain is expected to share with the runtime references.
# Overlap on them is not a leak, so the runtime-reference overlap check ignores them.
DOMAIN_IDENTIFIERS = {
    # General programming words. Keep these.
    "assert",
    "class",
    "def",
    "elif",
    "else",
    "except",
    "false",
    "from",
    "import",
    "none",
    "null",
    "return",
    "self",
    "string",
    "this",
    "throw",
    "true",
    "type",
    "with",
    # Example domain: error messages. Replace these with your domain's own identifiers, such as
    # its standard library names and the words your convention requires or bans.
    "cause",
    "connectionerror",
    "error",
    "errors",
    "exception",
    "expected",
    "failed",
    "invalid",
    "logger",
    "logging",
    "message",
    "permissionerror",
    "raise",
    "runtimeerror",
    "timeouterror",
    "valueerror",
}
# Every task.md needs a sentence like "Assume Python 3.12." so both variants target the same
# version or environment.
ENVIRONMENT_PATTERN = re.compile(r"^Assume\s+\S.*$|[.!?]\s+Assume\s+\S", re.MULTILINE)
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
# A main implementation scenario needs one check that the requested file exists and one that the
# requested behavior is preserved; these words in a check's name or description mark them.
ARTIFACT_WORDS = ("artifact", "creates", "compiles", "coherent")
BEHAVIOR_WORDS = (
    "behavior",
    "preserve",
    "exact",
    "return",
    "returns",
    "raise",
    "raises",
    "exception",
    "output",
    "order",
)
# A runtime reference that shares a run of this many words with a scenario's task, capability, or
# criteria, code included, counts as overlap. Five words catch a copied phrase without flagging
# common pairs.
PHRASE_WORDS = 5
# A main task this similar to a reference or regression task (share of its eight-word runs) is a
# duplicate, so the same scenario would count twice.
DUPLICATE_TASK_SIMILARITY = 0.85
# Every scenario scores exactly these points per category, 100 in total.
CATEGORY_POINTS = {"safety": 15, "quality": 80, "maintainability": 5}
# The suites each evidence type may live in.
EVIDENCE_SUITES = {
    "ordinary_lift": {MAIN_SUITE, REFERENCE_SUITE},
    "focused_main": {MAIN_SUITE},
    "focused_reference": {REFERENCE_SUITE},
    "solved_regression": {REGRESSION_SUITE},
    "skill_context_dependent": {REGRESSION_SUITE},
}
# evals/ has its own number space; reference and regression share one, so a scenario keeps its
# number when it moves between them.
NUMBER_SPACES = ((MAIN_SUITE,), (REFERENCE_SUITE, REGRESSION_SUITE))
NUMBERING_FILE = Path(MAIN_SUITE) / "NUMBERING.md"
GAP_NOTE_PATTERN = re.compile(
    rf"^\s*[-*]?\s*`?({'|'.join(re.escape(suite) for suite in SUITES)})`?\s+`?(\d{{2,}})`?\s*:\s*\S"
)
INTERNAL_LABEL_ALLOW_PATTERNS = (
    r"\bdo not deduct\b.{0,120}\b(?:hard[- ]stop|checklist|skill)\b",
    r"\baward full credit\b.{0,120}\b(?:hard[- ]stop|checklist|skill)\b",
    r"\ballow(?:s|ed)?\b.{0,120}\b(?:hard[- ]stop|checklist|skill)\b",
    r"\bbrief(?:ly)? uses\b.{0,120}\b(?:hard[- ]stop|checklist|skill)\b",
)
# README.md is left out on purpose: it names the example scenarios that a new skill replaces.
SCENARIO_REFERENCE_FILES = (Path("AGENTS.md"), NUMBERING_FILE)
SCENARIO_REFERENCE_DIRS = (Path("docs"),)
AGENT_DOC_FORBIDDEN_EXTERNAL_HISTORY_PATTERNS = (
    re.compile(r"\bissue\s+#?\d+\b", re.IGNORECASE),
    re.compile(r"\bpr\s+#?\d+\b", re.IGNORECASE),
    re.compile(r"https://github\.com/[^)\s]+/(?:issues|pull)/\d+", re.IGNORECASE),
    re.compile(r"\b01[0-9a-f]{6}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE),
)


def detect_skill_name() -> str:
    """Return the skill under test: $SKILL_NAME, or the only folder in skills/."""
    configured = os.environ.get("SKILL_NAME", "").strip()
    if configured:
        return configured
    found = sorted(path.parent.name for path in Path("skills").glob("*/SKILL.md"))
    if len(found) == 1:
        return found[0]
    raise SystemExit(
        f"error: found {len(found)} skills under {REPO_ROOT / 'skills'}; "
        "set SKILL_NAME to the one to validate"
    )


SKILL_NAME = detect_skill_name()
SKILL_ROOT = Path("skills") / SKILL_NAME
EXPLICIT_INVOCATION_PATTERNS = (
    rf"\${re.escape(SKILL_NAME)}\b",
    rf"(?:^|\s)/{re.escape(SKILL_NAME)}\b",
    rf"\buse\s+{re.escape(SKILL_NAME)}\b",
    rf"\buse\s+the\s+{re.escape(SKILL_NAME)}\s+skill\b",
    rf"\b{re.escape(SKILL_NAME)}\s+skill\b",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def repo_path(argument: str) -> Path:
    """Resolve a command-line path against the caller's directory, relative to the repo if inside."""
    path = (CALLER_CWD / argument).resolve()
    try:
        return path.relative_to(REPO_ROOT)
    except ValueError:
        return path


def scenario_dirs(paths: list[Path]) -> tuple[list[Path], list[str]]:
    """Return the scenario folders under the given paths, plus notes about missing suites."""
    dirs: list[Path] = []
    notes: list[str] = []
    for path in paths:
        if path.is_file() and path.name == "criteria.json":
            dirs.append(path.parent)
        elif path.is_dir():
            if (path / "criteria.json").is_file():
                dirs.append(path)
            else:
                dirs.extend(sorted(child for child in path.iterdir() if child.is_dir()))
        elif path.name in SUITES:
            notes.append(f"{path}/ does not exist; treating it as an empty suite")
        else:
            raise FileNotFoundError(f"path not found: {path}")
    return sorted(dict.fromkeys(dirs)), notes


def text_of(item: dict[str, Any]) -> str:
    return f"{item.get('name', '')} {item.get('description', '')}".lower()


def ngrams(words: list[str], size: int) -> set[tuple[str, ...]]:
    return {tuple(words[index : index + size]) for index in range(len(words) - size + 1)}


def code_like_text(text: str) -> str:
    chunks = re.findall(r"```(?:[A-Za-z0-9_-]+)?\n(.*?)```", text, flags=re.DOTALL)
    chunks.extend(re.findall(r"`([^`\n]+)`", text))
    return "\n".join(chunks)


def task_similarity(left: str, right: str) -> float:
    left_words = normalized_words(left)
    right_words = normalized_words(right)
    if not left_words or not right_words:
        return 0.0
    if left_words == right_words:
        return 1.0
    left_grams = ngrams(left_words, 8)
    right_grams = ngrams(right_words, 8)
    if not left_grams or not right_grams:
        return 0.0
    return len(left_grams & right_grams) / min(len(left_grams), len(right_grams))


def domain_identifiers(text: str) -> set[str]:
    identifiers = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", code_like_text(text)))
    return {
        identifier
        for identifier in identifiers
        if identifier.lower() not in DOMAIN_IDENTIFIERS
        and len(identifier) >= 4
        and not (identifier.isupper() and len(identifier) <= 6)
    }


def api_markers(text: str) -> set[str]:
    return set(re.findall(r"\b[A-Z][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+\b", text))


def scenario_full_text(scenario: Path, data: dict[str, Any] | None) -> str:
    """Return the task, capability, and criteria wording of a scenario, code included."""
    parts = [read_text(scenario / "task.md"), read_text(scenario / "capability.txt")]
    if data:
        parts.append(str(data.get("context", "")))
        parts.extend(text_of(item) for item in data.get("checklist") or [] if isinstance(item, dict))
    return "\n".join(parts)


def format_category_points() -> str:
    return ", ".join(f"{points} {category}" for category, points in CATEGORY_POINTS.items())


def validate_scenario(scenario: Path) -> list[str]:
    failures: list[str] = []
    suite = scenario.parent.name
    task_file = scenario / "task.md"
    criteria_file = scenario / "criteria.json"
    capability_file = scenario / "capability.txt"

    for required in (task_file, criteria_file, capability_file):
        if not required.is_file():
            failures.append(f"{scenario}: missing {required.name}")
    if capability_file.is_file() and not read_text(capability_file).strip():
        failures.append(f"{capability_file}: capability must be non-empty")
    if not criteria_file.is_file():
        return failures

    data, load_failures = load_criteria(criteria_file)
    failures.extend(load_failures)
    if data is None:
        return failures

    if data.get("type") != "weighted_checklist":
        failures.append(f"{criteria_file}: type must be weighted_checklist")
    context = data.get("context")
    if suite != MAIN_SUITE and isinstance(context, str) and context.startswith("Main eval"):
        failures.append(
            f"{criteria_file}: context starts with 'Main eval' but the scenario is in {suite}/; "
            "start it with 'Reference coverage' or 'Regression coverage'"
        )

    checklist = data.get("checklist")
    if not isinstance(checklist, list) or not checklist:
        failures.append(f"{criteria_file}: checklist must be a non-empty array")
        checklist = []

    names: set[str] = set()
    artifact_score = 0
    behavior_score = 0
    category_scores = {category: 0 for category in CATEGORY_POINTS}
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
        if category is not None and category not in CATEGORY_POINTS:
            failures.append(
                f"{criteria_file}: checklist item {index} has unsupported category {category!r}; "
                f"use one of {sorted(CATEGORY_POINTS)}"
            )
        if category in category_scores:
            category_scores[category] += max_score
        haystack = text_of(item)
        if any(word in haystack for word in ARTIFACT_WORDS):
            artifact_score += max_score
        if any(word in haystack for word in BEHAVIOR_WORDS):
            behavior_score += max_score

    for category, points in CATEGORY_POINTS.items():
        if category_scores[category] != points:
            failures.append(
                f"{criteria_file}: {category} checks total {category_scores[category]} points; "
                f"every scenario needs exactly {points} ({format_category_points()})"
            )

    task_text = read_text(task_file)
    metadata = data["metadata"]
    invocation = metadata.get("invocation")
    task_type = metadata.get("task_type")
    evidence_type = metadata.get("evidence_type")
    if invocation not in {"natural", "explicit"}:
        failures.append(f"{criteria_file}: metadata.invocation must be natural or explicit")
    if task_type not in {"implementation", "cleanup", "review"}:
        failures.append(f"{criteria_file}: metadata.task_type must be implementation, cleanup, or review")
    if evidence_type is None and suite == REGRESSION_SUITE:
        failures.append(
            f"{criteria_file}: regression scenarios must set metadata.evidence_type to "
            "solved_regression or skill_context_dependent"
        )
    elif evidence_type is not None and evidence_type not in EVIDENCE_SUITES:
        failures.append(
            f"{criteria_file}: metadata.evidence_type must be one of {sorted(EVIDENCE_SUITES)}"
        )
    elif evidence_type is not None and suite not in EVIDENCE_SUITES[evidence_type]:
        allowed = " or ".join(f"{name}/" for name in sorted(EVIDENCE_SUITES[evidence_type]))
        failures.append(
            f"{criteria_file}: metadata.evidence_type={evidence_type} must live in {allowed}"
        )

    phrase = skill_context_phrase(f"{task_text}\n{json.dumps(data, sort_keys=True)}")
    if phrase and evidence_type != "skill_context_dependent":
        failures.append(
            f"{criteria_file}: the phrase {phrase!r} says the scenario needs the skill's own text. "
            "Reword it if the scenario does not, or set metadata.evidence_type to "
            "skill_context_dependent and move the scenario to evals-regression/"
        )
    if evidence_type != "skill_context_dependent" and task_type == "review":
        for index, item in enumerate(checklist, start=1):
            if isinstance(item, dict) and any(
                re.search(pattern, text_of(item)) for pattern in INTERNAL_LABEL_ALLOW_PATTERNS
            ):
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
    names_skill = any(re.search(pattern, task_text, re.IGNORECASE) for pattern in EXPLICIT_INVOCATION_PATTERNS)
    if invocation == "natural" and names_skill:
        failures.append(f"{task_file}: natural scenario explicitly invokes the skill")
    if invocation == "explicit" and not names_skill:
        failures.append(f"{criteria_file}: explicit scenario task does not invoke the skill")

    if suite == MAIN_SUITE and task_type == "implementation":
        if artifact_score <= 0:
            failures.append(
                f"{criteria_file}: main implementation scenario needs a check that the requested "
                f"file is created; name or describe it with one of {list(ARTIFACT_WORDS)}"
            )
        if behavior_score <= 0:
            failures.append(
                f"{criteria_file}: main implementation scenario needs a behavior check; name or "
                f"describe it with one of {list(BEHAVIOR_WORDS)}"
            )
    return failures


def validate_cross_suite_duplicates(dirs: list[Path]) -> list[str]:
    failures: list[str] = []
    main = [scenario for scenario in dirs if scenario.parent.name == MAIN_SUITE]
    others = [scenario for scenario in dirs if scenario.parent.name in (REFERENCE_SUITE, REGRESSION_SUITE)]
    for main_scenario in main:
        main_task = read_text(main_scenario / "task.md")
        for other in others:
            similarity = task_similarity(main_task, read_text(other / "task.md"))
            if similarity >= DUPLICATE_TASK_SIMILARITY:
                failures.append(
                    f"{main_scenario}: task.md is too similar to {other} "
                    f"({similarity:.2f} of its eight-word runs match); delete or rewrite one of them"
                )
    return failures


def validate_runtime_reference_overlap(dirs: list[Path]) -> list[str]:
    failures: list[str] = []
    references_root = SKILL_ROOT / "references"
    runtime_text = "\n".join(read_text(path) for path in sorted(references_root.glob("*.md")))
    if not runtime_text:
        return failures
    runtime_identifiers = domain_identifiers(runtime_text)
    runtime_phrases = ngrams(normalized_words(runtime_text), PHRASE_WORDS)
    runtime_api_markers = api_markers(runtime_text)

    for scenario in dirs:
        suite = scenario.parent.name
        task_text = read_text(scenario / "task.md")
        if suite not in SUITES or not task_text:
            continue
        criteria_file = scenario / "criteria.json"
        data, _ = load_criteria(criteria_file) if criteria_file.is_file() else (None, [])
        metadata = data["metadata"] if data else {}

        shared_identifiers = sorted(domain_identifiers(task_text) & runtime_identifiers)
        scenario_phrases = ngrams(normalized_words(scenario_full_text(scenario, data)), PHRASE_WORDS)
        shared_phrases = sorted(" ".join(gram) for gram in scenario_phrases & runtime_phrases)
        shared_api_markers = sorted(api_markers(task_text) & runtime_api_markers)
        has_overlap = (
            len(shared_identifiers) >= 4
            or bool(shared_phrases)
            or (bool(shared_api_markers) and len(shared_identifiers) >= 2)
        )
        if not has_overlap:
            continue

        evidence_type = metadata.get("evidence_type")
        rationale = metadata.get("runtime_reference_overlap_rationale")
        has_rationale = isinstance(rationale, str) and bool(rationale.strip())
        details = (
            f"shared identifiers: {', '.join(shared_identifiers[:12]) or '(none)'}; "
            f"shared API markers: {', '.join(shared_api_markers[:12]) or '(none)'}; "
            f"shared phrases: {'; '.join(shared_phrases[:6]) or '(none)'}"
        )
        focused = {MAIN_SUITE: "focused_main", REFERENCE_SUITE: "focused_reference"}.get(suite)
        if suite == REGRESSION_SUITE:
            if evidence_type not in EVIDENCE_SUITES or REGRESSION_SUITE not in EVIDENCE_SUITES[evidence_type]:
                failures.append(
                    f"{scenario}: regression task overlaps runtime references ({details}); "
                    "classify it as solved_regression or skill_context_dependent"
                )
        elif evidence_type != focused:
            failures.append(
                f"{scenario}: task, capability, or criteria overlap the runtime references "
                f"({details}); move the reference example to another domain, or set "
                f"metadata.evidence_type={focused} with a runtime_reference_overlap_rationale"
            )
        elif not has_rationale:
            failures.append(
                f"{criteria_file}: {focused} scenario with runtime-reference overlap must set "
                "metadata.runtime_reference_overlap_rationale"
            )
    return failures


def validate_scenario_path_references() -> list[str]:
    failures: list[str] = []
    files = [path for path in SCENARIO_REFERENCE_FILES if path.exists()]
    for directory in SCENARIO_REFERENCE_DIRS:
        if directory.exists():
            files.extend(sorted(directory.rglob("*.md")))

    suites = "|".join(re.escape(suite) for suite in SUITES)
    pattern = re.compile(rf"`?((?:{suites})/[A-Za-z0-9_.\-/]+)`?")
    for path in files:
        for match in pattern.finditer(read_text(path)):
            candidate = match.group(1).rstrip(".,);:")
            if "*" not in candidate and not Path(candidate).exists():
                failures.append(f"{path}: stale scenario path reference {candidate!r}")
    return failures


def validate_runtime_references() -> list[str]:
    failures: list[str] = []
    for path in sorted((SKILL_ROOT / "references").glob("*.md")):
        text = read_text(path).lower()
        for marker in ANSWER_KEY_MARKERS:
            if marker.lower() in text:
                failures.append(f"{path}: runtime reference contains answer-key marker {marker!r}")
    return failures


def validate_agent_docs_self_contained() -> list[str]:
    failures: list[str] = []
    for path in sorted(Path("docs/agents").glob("*.md")):
        text = read_text(path)
        for pattern in AGENT_DOC_FORBIDDEN_EXTERNAL_HISTORY_PATTERNS:
            match = pattern.search(text)
            if match:
                failures.append(
                    f"{path}: docs/agents must be self-contained; remove external history "
                    f"reference {match.group(0)!r}"
                )
    return failures


def suite_numbers(suite: str) -> dict[int, str]:
    numbers: dict[int, str] = {}
    root = Path(suite)
    for scenario in sorted(child for child in root.iterdir() if child.is_dir()) if root.is_dir() else []:
        match = re.match(r"^(\d+)-", scenario.name)
        if match:
            numbers.setdefault(int(match.group(1)), f"{suite}/{scenario.name}")
    return numbers


def gap_notes() -> tuple[set[tuple[str, int]], list[str]]:
    """Read the '## Gaps' section of NUMBERING.md as (suite, number) pairs."""
    notes: set[tuple[str, int]] = set()
    failures: list[str] = []
    section = re.search(r"^## Gaps\n(.*?)(?=^## |\Z)", read_text(NUMBERING_FILE), re.MULTILINE | re.DOTALL)
    for line in section.group(1).splitlines() if section else []:
        if not line.strip() or line.strip() == "None yet.":
            continue
        match = GAP_NOTE_PATTERN.match(line)
        if match:
            notes.add((match.group(1), int(match.group(2))))
        else:
            failures.append(
                f"{NUMBERING_FILE}: gap note {line.strip()!r} must look like "
                f"'- {REFERENCE_SUITE} 03: deleted because the main suite covers it'"
            )
    return notes, failures


def validate_numbering() -> list[str]:
    """Check the numbering rule in evals/NUMBERING.md for all suites."""
    notes, failures = gap_notes()
    used: set[tuple[str, int]] = set()
    for space in NUMBER_SPACES:
        numbers: dict[int, str] = {}
        for suite in space:
            for number, name in suite_numbers(suite).items():
                used.add((suite, number))
                if number in numbers:
                    failures.append(f"number {number:02d} is used twice: {numbers[number]}, {name}")
                numbers.setdefault(number, name)
        for number in sorted(set(range(1, max(numbers, default=0) + 1)) - set(numbers)):
            if not any((suite, number) in notes for suite in space):
                failures.append(
                    f"{' and '.join(space)}: number {number:02d} is missing; add a line under "
                    f"'## Gaps' in {NUMBERING_FILE} such as '- {space[0]} {number:02d}: deleted, "
                    "<reason>', naming the suite the scenario left"
                )
    for suite, number in sorted(notes & used):
        failures.append(
            f"{NUMBERING_FILE}: gap note for {suite} {number:02d}, but that number is in use; "
            "remove the note"
        )
    return failures


def main() -> int:
    paths = [repo_path(argument) for argument in sys.argv[1:]] or [Path(suite) for suite in SUITES]
    try:
        dirs, notes = scenario_dirs(paths)
    except FileNotFoundError as exc:
        return error(str(exc))
    for note in notes:
        print(f"note: {note}", file=sys.stderr)
    if not dirs:
        return error(
            f"no scenario folders in {', '.join(str(path) for path in paths)}; add one with "
            "task.md, capability.txt, criteria.json, and criteria-meta.json (README step 4)"
        )

    failures: list[str] = []
    invocations = {"natural": 0, "explicit": 0}
    for scenario in dirs:
        failures.extend(validate_scenario(scenario))
        data, _ = load_criteria(scenario / "criteria.json") if (scenario / "criteria.json").is_file() else (None, [])
        invocation = data["metadata"].get("invocation") if data else None
        if invocation in invocations:
            invocations[invocation] += 1

    failures.extend(validate_numbering())
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
