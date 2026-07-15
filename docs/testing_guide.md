# Testing Skills Like Code

Most teams write a skill once, try it on one or two prompts, and never look
at it again. Then three months later the agent goes off-script on a question
nobody thought to test, and there's no way to know whether that's a new
failure or one that was always there. Skills need the same discipline as
any other piece of production logic: a test suite, a way to run it, and a
reason to re-run it on every change.

## What a Regression Suite Actually Checks

`evaluation/regression_suite.yaml` in this repo is the reference structure.
Each case is:

- a realistic **prompt** — not a synthetic edge case, a question a real user
  would actually type
- a set of **must_include** phrases — content that has to appear if the
  skill behaved correctly (a cited source, a stated guardrail, a confirmed
  definition)
- a set of **must_not_include** phrases — content that must never appear
  (destructive SQL, a named individual blamed for an incident, a fabricated
  citation)

This is intentionally *behavioral*, not exact-string matching. LLM output
wording varies between runs; what has to stay constant is whether the
required behavior happened.

## Running the Harness

```bash
cd evaluation
pip install pyyaml --break-system-packages
python skill_eval_harness.py fixtures/good_responses.json
python skill_eval_harness.py fixtures/bad_responses.json
```

The two bundled fixtures demonstrate the range: `good_responses.json` scores
100% (real transcripts that follow every skill's rules), `bad_responses.json`
scores 0% (transcripts from the anti-pattern skills in this repo). If you
change a skill's constraints, add a case to `regression_suite.yaml` before
you change anything else — that's the point at which you know what "correct"
means well enough to write it down.

## Producing a Real Transcript

The harness scores any file matching `{case_id: response_text}` — it doesn't
care how the response was generated. To score live model output instead of
a fixture:

1. Load the skill you're testing into a real session.
2. Run each case's `prompt` from `regression_suite.yaml` against it.
3. Save each response under its `case_id` in a JSON file.
4. Score that file with the harness.

## When to Add a Case

- Any time you add a guardrail to a skill — write the case that would catch
  a violation of that guardrail *before* you consider the guardrail done.
- Any time a skill misbehaves in real use — turn the failure into a
  regression case immediately, not after the fix. Otherwise you have no
  proof the fix actually worked, and no protection against the same failure
  coming back with the next edit.
- Any time two skills' descriptions might overlap — write a case with a
  prompt that's ambiguous between them and confirm only the intended skill
  fires.

## Version Control for Skills

Treat `SKILL.md` files the same as application code:

- Every change goes through review, same as a pull request for any other
  logic that touches production data or writes user-facing content.
- Tag skill versions in the `version` frontmatter field when you make a
  behavioral change, so a regression can be traced to the exact version that
  introduced it.
- Run the regression suite in CI on every skill change, not just before a
  release. A skill that silently regresses between releases is exactly the
  overlapping-guardrail failure mode `anti_patterns/overlapping_skills.md`
  describes, just spread out over time instead of over two files.
