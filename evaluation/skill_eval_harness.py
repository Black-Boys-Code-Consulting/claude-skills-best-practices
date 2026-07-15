#!/usr/bin/env python3
"""
skill_eval_harness.py

Scores a set of skill responses against evaluation/regression_suite.yaml.

This does NOT call an LLM by default — it's a pure scoring harness that
checks a transcript (a JSON file mapping case id -> response text) against
the behavioral checks defined in the regression suite. That keeps it
runnable with no API key, so anyone can clone this repo and see the
scoring model work immediately, using the two bundled fixtures:

    fixtures/good_responses.json   -> responses from correctly-built skills
    fixtures/bad_responses.json    -> responses from the anti-pattern skills

Usage:
    python skill_eval_harness.py fixtures/good_responses.json
    python skill_eval_harness.py fixtures/bad_responses.json
    python skill_eval_harness.py fixtures/good_responses.json --verbose

Optional live mode: if you want to score real model output instead of a
fixture, generate a transcript JSON in the same {case_id: response_text}
shape (e.g. by calling the Claude API with the skill loaded and the case's
`prompt`) and pass that file in instead. The harness itself has no
dependency on how the transcript was produced.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml. Install with:")
    print("    pip install pyyaml --break-system-packages")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent
SUITE_PATH = REPO_ROOT / "regression_suite.yaml"


def load_suite(path: Path):
    with open(path, "r") as f:
        cases = yaml.safe_load(f)
    if not cases:
        raise ValueError(f"No cases found in {path}")
    return cases


def load_transcript(path: Path):
    with open(path, "r") as f:
        return json.load(f)


def score_case(case: dict, response: str):
    """Return (passed: bool, failures: list[str]) for one case."""
    failures = []
    response_lower = response.lower()

    for phrase in case.get("must_include") or []:
        if phrase.lower() not in response_lower:
            failures.append(f'missing required content: "{phrase}"')

    for phrase in case.get("must_not_include") or []:
        if phrase.lower() in response_lower:
            failures.append(f'contains forbidden content: "{phrase}"')

    return (len(failures) == 0, failures)


def run(transcript_path: Path, verbose: bool = False):
    cases = load_suite(SUITE_PATH)
    transcript = load_transcript(transcript_path)

    total = 0
    passed = 0
    by_skill = {}

    for case in cases:
        case_id = case["id"]
        skill = case.get("skill", "unknown")
        by_skill.setdefault(skill, {"total": 0, "passed": 0})

        if case_id not in transcript:
            print(f"[SKIP] {case_id}: no response found in transcript")
            continue

        total += 1
        by_skill[skill]["total"] += 1

        ok, failures = score_case(case, transcript[case_id])
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
            by_skill[skill]["passed"] += 1

        print(f"[{status}] {case_id}  ({skill})")
        if verbose or not ok:
            print(f"        prompt: {case['prompt']!r}")
            for f in failures:
                print(f"        - {f}")
            if case.get("notes"):
                print(f"        note: {case['notes'].strip()}")

    print()
    print("=" * 60)
    print(f"Overall: {passed}/{total} passed ({0 if total == 0 else round(100 * passed / total)}%)")
    print()
    print("By skill:")
    for skill, stats in by_skill.items():
        t, p = stats["total"], stats["passed"]
        pct = 0 if t == 0 else round(100 * p / t)
        print(f"  {skill}: {p}/{t} ({pct}%)")

    return 0 if passed == total else 1


def main():
    parser = argparse.ArgumentParser(description="Score a skill response transcript against the regression suite.")
    parser.add_argument("transcript", type=Path, help="Path to a JSON file mapping case id -> response text")
    parser.add_argument("--verbose", action="store_true", help="Show details for passing cases too")
    args = parser.parse_args()

    sys.exit(run(args.transcript, verbose=args.verbose))


if __name__ == "__main__":
    main()
