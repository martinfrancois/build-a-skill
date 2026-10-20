#!/usr/bin/env python3
"""Recommend a suite for one hosted eval scenario: main, reference, regression, or fix-required.

Reads `tessl eval view --json` output and applies the promotion rule from evals/NUMBERING.md.
It promotes to main only when the scenario scores 100 with the skill and the delta to the run
without the skill meets the floor.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from eval_common import error, load_criteria, normalized, scenario_wording, skill_context_phrase

# The promotion rule from evals/NUMBERING.md: a delta of at least this many percentage points.
MAIN_DELTA_FLOOR = 30.0
# `tessl eval view --json` names the with-skill variant usage-spec and the control baseline.
WITH_SKILL_VARIANT = "usage-spec"
WITHOUT_SKILL_VARIANT = "baseline"

Score = tuple[float, float]


def score(solution: dict[str, Any]) -> Score:
    results = solution.get("assessmentResults") or []
    earned = sum(float(item.get("score") or 0) for item in results)
    maximum = sum(float(item.get("max_score") or 0) for item in results)
    return earned, maximum


def local_scenario(path: Path | None) -> tuple[str, dict[str, Any]]:
    """Return the task and criteria wording plus the metadata of a local scenario folder."""
    if path is None:
        return "", {}
    task = (path / "task.md").read_text(encoding="utf-8") if (path / "task.md").is_file() else ""
    criteria_file = path / "criteria.json"
    data, _ = load_criteria(criteria_file) if criteria_file.is_file() else (None, [])
    return scenario_wording(task, data), data["metadata"] if data else {}


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
    matches = [
        scenario
        for scenario in scenarios
        if query_norm in normalized(f"{scenario.get('shortDescription') or ''}\n{scenario.get('task') or ''}")
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one scenario match for {query!r}, found {len(matches)}")
    return matches[0]


def percent(value: Score) -> float | None:
    earned, maximum = value
    return 100 * earned / maximum if maximum > 0 else None


def classify(*, with_skill: Score | None, without_skill: Score | None, needs_skill_text: bool) -> tuple[str, str]:
    if with_skill is None:
        return "fix-required", "the run with the skill is missing; run it before classifying"
    with_percent = percent(with_skill)
    if with_percent is None:
        return "fix-required", "the run with the skill has a max score of zero; scoring did not finish"
    if with_percent < 100:
        return "fix-required", "below 100 with the skill; fix the skill and rerun this scenario first"
    if needs_skill_text:
        return "regression", "it needs the skill's own text, so it is only fair as with-skill regression coverage"
    if without_skill is None:
        return "reference", "the run without the skill is missing; run both variants before judging the delta"
    without_percent = percent(without_skill)
    if without_percent is None:
        return "reference", "the run without the skill has a max score of zero; scoring did not finish"
    if without_percent == 100:
        return "regression", "100 with and without the skill; keep it as regression coverage"
    delta = with_percent - without_percent
    if delta >= MAIN_DELTA_FLOOR:
        return "main", f"100 with the skill and a {delta:.1f} point delta, at or above the {MAIN_DELTA_FLOOR:.0f} point floor"
    return "reference", f"100 with the skill but a {delta:.1f} point delta, below the {MAIN_DELTA_FLOOR:.0f} point floor"


def fmt(value: Score | None) -> str:
    if value is None:
        return "missing"
    earned, maximum = value
    share = percent(value)
    return f"{earned:g}/{maximum:g}" + (f" ({share:.1f}%)" if share is not None else "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_json", type=Path, help="Path to tessl eval view --json output")
    parser.add_argument("--scenario", help="Scenario title, directory name, or distinctive text")
    parser.add_argument(
        "--scenario-dir",
        type=Path,
        help="Local scenario folder, used to tell whether the scenario needs the skill's own text",
    )
    args = parser.parse_args()

    try:
        data = json.loads(args.run_json.read_text(encoding="utf-8"))
        scenario = find_scenario(data, args.scenario)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return error(str(exc))

    solutions = {solution.get("variant"): score(solution) for solution in scenario.get("solutions", [])}
    with_skill = solutions.get(WITH_SKILL_VARIANT)
    without_skill = solutions.get(WITHOUT_SKILL_VARIANT)

    title = scenario.get("shortDescription") or "(untitled scenario)"
    local_text, local_metadata = local_scenario(args.scenario_dir)
    needs_skill_text = local_metadata.get("evidence_type") == "skill_context_dependent" or bool(
        skill_context_phrase(f"{title}\n{scenario.get('task') or ''}\n{local_text}")
    )
    suite, reason = classify(with_skill=with_skill, without_skill=without_skill, needs_skill_text=needs_skill_text)

    print(f"scenario: {title}")
    print(f"with the skill: {fmt(with_skill)}")
    print(f"without the skill: {fmt(without_skill)}")
    print(f"needs the skill's own text: {'yes' if needs_skill_text else 'no'}")
    print(f"recommended suite: {suite}")
    print(f"reason: {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
