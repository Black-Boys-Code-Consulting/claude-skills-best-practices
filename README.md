# claude-skills-best-practices

**Write skills that actually hold up in production.**

Most teams write a skill once, try it on a couple of prompts, and never test
it again. This repo is the opposite of that: a set of well-formed skill
templates, a matching set of anti-patterns showing exactly how skills fail
and why, and an evaluation harness that scores skill behavior instead of
leaving quality as a subjective judgment call.

Paired article: *"Skills Best Practices: Writing AI Instructions That
Actually Hold Up in Production"* — the article covers the anatomy of a
well-formed skill and why vague or overlapping skills produce unpredictable
agents; this repo is the runnable version of that argument.

## Structure

```
/skill_templates          Three well-formed, production-ready skill examples
  data_query_skill.md        - read-only warehouse Q&A with join/metric discipline
  document_search_skill.md   - citation-only retrieval, no fabricated sourcing
  workflow_skill.md          - explicit-invoke multi-step task (incident postmortems)

/anti_patterns             What a bad skill looks like, and why it fails
  vague_skill_example.md     - a description with nothing to match on
  overlapping_skills.md      - two skills that silently compete for the same question
  underconstrained.md        - a skill with no stated guardrails

/evaluation                 Skill quality, made measurable
  skill_eval_harness.py      - scores a transcript against the regression suite
  regression_suite.yaml      - behavioral checks paired to real prompts
  fixtures/
    good_responses.json      - passes 7/7
    bad_responses.json       - fails 7/7, one failure per anti-pattern

/docs
  skill_anatomy.md           - scope, constraints, examples, guardrails
  testing_guide.md           - how and when to test a skill like code
```

## The Differentiator

The `anti_patterns/` directory is the core teaching asset. Generic
"best practices" lists are easy to nod along with and forget. Seeing the
exact vague description that never fires, the exact overlapping pair that
produces a coin-flip answer, and the exact underconstrained skill that lets
a "clean up duplicates" request turn into a `DELETE` — each annotated with
*why* it fails — is what actually changes how the next skill gets written.

The `skill_eval_harness.py` + `regression_suite.yaml` pair makes the second
half of the argument concrete: skill quality isn't a vibe, it's testable.
Clone the repo and run both fixtures — the good transcript passes every
check, the bad transcript (built from the same three anti-patterns) fails
every check, for exactly the reasons documented alongside each anti-pattern.

## Quickstart

```bash
git clone <this-repo>
cd claude-skills-best-practices/evaluation
pip install pyyaml --break-system-packages
python skill_eval_harness.py fixtures/good_responses.json
python skill_eval_harness.py fixtures/bad_responses.json
```

No API key required — the harness scores any transcript file shaped like
`{case_id: response_text}`, whether that came from a real model session or,
as in the bundled fixtures, from hand-written examples of correct and
broken skill behavior.

## Related

- `ai-agent-token-manager` — Month 1's repo, on the cost side of agent
  design. The budget enforcer and anomaly detector there follow the same
  command-vs-skill distinction covered in the Month 1 article: deterministic
  guardrails as explicit rules, judgment calls as discoverable context.

---

At Black Boys Code Consulting, we specialize in the engineering and
architectural rigor required to make AI functional for the enterprise.

We don't just build pipelines; we build the context-rich environments that
allow AI agents to reason, plan, and deliver value.

[blackboyscodeconsulting.com](https://blackboyscodeconsulting.com)
