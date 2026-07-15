# Anti-Pattern: The Underconstrained Skill

## The Skill As Written

```
---
name: db-query
description: Query the production database to answer analytics questions.
  Use when the user asks a data question.
allowed-tools: Bash
---

# DB Query

Write and run SQL against the production database to answer the user's
question. Return the results.
```

## Why It Fails

This skill is specific enough to fire reliably — the description is fine.
The problem is everything the body *doesn't* say:

- **No statement type restriction.** "Write and run SQL" doesn't say
  read-only. Nothing stops a generated query from being an `UPDATE` or
  `DELETE` if the model decides that's what answers the question — for
  example, "clean up duplicate rows" is an analytics-adjacent request that a
  permissive skill like this will happily execute as a `DELETE`.
- **No table scope.** Without a defined join map or table allowlist, the
  model infers joins from column names alone. A `customer_id` column that
  exists in three unrelated tables gets joined based on plausible-sounding
  names, not confirmed relationships — the exact join hallucination problem
  metadata frameworks exist to prevent.
- **No row limit.** A broad question can generate a full-table scan against
  production with no ceiling, which is a performance and cost problem, not
  just a correctness one.
- **No output constraint.** Nothing says whether PII columns should be
  filtered, masked, or excluded from the response.

Each of these gaps is invisible in a demo, where the questions asked are
narrow and safe. They surface in production, where a wider range of
questions gets thrown at the skill and the model fills every unstated
constraint with its best guess — which is exactly what "underconstrained"
means: not that the skill is wrong, but that it delegates every safety
decision to the model's judgment in the moment, with no record of what was
intended.

## The Fix

Every field left unstated here is stated explicitly in
`skill_templates/data_query_skill.md`: read-only enforced in the Guardrails
section, join paths pinned to a reference file, a hard 500-row cap, and an
explicit test-account filter. None of that is more code — it's the same
amount of markdown, aimed at the actual failure modes instead of left open.

**Rule of thumb**: for any skill that touches a live system, list what it is
*not* allowed to do as explicitly as what it is for. If you can't name three
things this skill must never do, you haven't finished writing it.
