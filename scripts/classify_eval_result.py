#!/usr/bin/env python3
"""Classify one hosted eval scenario into main, reference, regression, or fix-required.

The script reads Tessl `eval view --json` output and applies the repository's
suite policy. It is intentionally conservative: promote to main only when an
isolated run shows clean with-context behavior and a delta meeting the
repository main promotion floor.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_MAIN_DELTA_FLOOR = 30.0


def error(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def score(solution: dict[str, Any]) -> tuple[float, float]:
    results = solution.get("assessmentResults") or []
    earned = sum(float(item.get("score") or 0) for item in results)
    maximum = sum(float(item.get("max_score") or item.get("maxScore") or 0) for item in results)
    return earned, maximum


def normalized(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def scenario_text_from_dir(path: Path | None) -> str:
    if path is None:
        return ""
    parts: list[str] = []
    for name in ("task.md", "criteria.json", "capability.txt"):
        file_path = path / name
        if file_path.is_file():
            parts.append(file_path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def scenario_metadata_from_dir(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    sidecar_path = path / "criteria-meta.json"
    if not sidecar_path.is_file():
        return {}
    try:
        data = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        return {}
    return metadata


def is_skill_context_dependent(text: str) -> bool:
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


def find_scenario(data: dict[str, Any], query: str | None) -> dict[str, Any]:
    scenarios = data.get("data", {}).get("attributes", {}).get("scenarios", [])
    if not isinstance(scenarios, list):
        raise ValueError("run JSON does not contain data.attributes.scenarios")
    if not scenarios:
        raise ValueError("run JSON contains no scenarios")
    if query is None:
        if len(scenarios) != 1:
            raise ValueError("run contains multiple scenarios; pass --scenario")
        return scenarios[0]

    query_norm = normalized(query)
    matches = []
    for scenario in scenarios:
        title = scenario.get("shortDescription") or ""
        task = scenario.get("task") or ""
        haystack = normalized(f"{title}\n{task}")
        if query_norm in haystack:
            matches.append(scenario)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one scenario match for {query!r}, found {len(matches)}")
    return matches[0]


def classify(
    *,
    with_score: tuple[float, float] | None,
    without_score: tuple[float, float] | None,
    skill_context_dependent: bool,
    main_delta_floor: float,
) -> tuple[str, str]:
    if with_score is None:
        return "fix-required", "with-context result is missing; run with context before classifying"

    with_earned, with_max = with_score
    if with_max <= 0:
        return "fix-required", "with-context max score is zero; scoring did not finish cleanly"
    with_percent = 100 * with_earned / with_max

    if with_percent < 100:
        return (
            "fix-required",
            "with-context is below 100%; fix the skill or eval and rerun targeted before choosing a suite",
        )

    if skill_context_dependent:
        return (
            "regression",
            "skill-context-dependent recall is only fair as with-context regression coverage",
        )

    if without_score is None:
        return "reference", "without-context result is missing; run both variants before lift classification"

    without_earned, without_max = without_score
    if without_max <= 0:
        return "reference", "without-context max score is zero; baseline scoring did not finish cleanly"
    without_percent = 100 * without_earned / without_max

    if without_percent == 100:
        return "regression", "both variants scored 100%; keep as with-context safety coverage"

    delta = with_percent - without_percent
    if delta >= main_delta_floor:
        return "main", f"clean with-context result and {delta:.1f} pp delta meets main floor {main_delta_floor:.1f} pp"

    return "reference", f"clean with-context result but {delta:.1f} pp delta is below main floor {main_delta_floor:.1f} pp"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_json", type=Path, help="Path to Tessl eval view --json output")
    parser.add_argument("--scenario", help="Scenario title, directory name, or distinctive text")
    parser.add_argument(
        "--scenario-dir",
        type=Path,
        help="Local scenario directory for skill-context-dependent detection",
    )
    parser.add_argument(
        "--main-delta-floor",
        type=float,
        default=DEFAULT_MAIN_DELTA_FLOOR,
        help="Minimum percentage-point delta required for main promotion",
    )
    args = parser.parse_args()

    try:
        data = json.loads(args.run_json.read_text(encoding="utf-8"))
        scenario = find_scenario(data, args.scenario)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return error(str(exc))

    solutions = {solution.get("variant"): score(solution) for solution in scenario.get("solutions", [])}
    with_score = solutions.get("usage-spec") or solutions.get("with-context")
    without_score = solutions.get("baseline") or solutions.get("without-context")

    title = scenario.get("shortDescription") or "(untitled scenario)"
    task_text = scenario.get("task") or ""
    local_text = scenario_text_from_dir(args.scenario_dir)
    local_metadata = scenario_metadata_from_dir(args.scenario_dir)
    skill_context_dependent = (
        local_metadata.get("evidence_type") == "skill_context_dependent"
        or is_skill_context_dependent(f"{title}\n{task_text}\n{local_text}")
    )

    suite, reason = classify(
        with_score=with_score,
        without_score=without_score,
        skill_context_dependent=skill_context_dependent,
        main_delta_floor=args.main_delta_floor,
    )

    def fmt(value: tuple[float, float] | None) -> str:
        if value is None:
            return "missing"
        earned, maximum = value
        if maximum <= 0:
            return f"{earned:g}/{maximum:g}"
        return f"{earned:g}/{maximum:g} ({100 * earned / maximum:.1f}%)"

    print(f"scenario: {title}")
    print(f"with-context: {fmt(with_score)}")
    print(f"without-context: {fmt(without_score)}")
    print(f"skill-context-dependent: {'yes' if skill_context_dependent else 'no'}")
    print(f"recommended-suite: {suite}")
    print(f"reason: {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
