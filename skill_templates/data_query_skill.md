---
name: data-query-skill
description: Answer business questions against the sales data warehouse using approved join paths and metric definitions. Use when the user asks about revenue, customers, orders, or any question that requires querying the warehouse rather than reading a document.
allowed-tools: Read Grep Bash
---

# Data Query Skill

## Scope

This skill answers natural-language business questions against the `sales_dw`
warehouse. It does not apply to questions about other systems, and it does not
apply to requests to modify data — read-only queries only.

## Before Writing Any Query

1. Read `reference/join_map.md` to confirm the join path between the tables
   the question requires. Never join two tables without a confirmed path.
2. Read `reference/metric_glossary.md` to confirm the definition of any
   business term in the question (e.g. "active customer", "net revenue").
   If a term in the question is not in the glossary, ask the user to clarify
   rather than guessing a definition.
3. Confirm the grain of the question (per day? per customer? per order?)
   before writing the query. Mismatched grain is the most common source of
   silently wrong answers.

## Query Rules

- Always filter `is_test_account = false` on any query touching `customers`
  or `orders`, unless the user explicitly asks about test accounts.
- Always use the column names in `reference/join_map.md`, not inferred names.
  Column names in this warehouse do not always match their business meaning
  (see `revenue_gross` vs `revenue_net` in the glossary).
- Row limit: return at most 500 rows in a single query. If the answer
  requires more, aggregate instead of returning raw rows.

## Output Format

State the answer first, in one sentence. Then show the query used. Then note
any assumption made (date range, definition of an ambiguous term, grain).

## Guardrails

- If the requested table is not in `reference/join_map.md`, say so and stop.
  Do not guess a schema.
- If a question could reasonably resolve to two different metric definitions,
  state both and ask which one the user means before proceeding.
- Never write, update, or delete statements. This skill is read-only.

## Examples

**Good**: "How many active customers did we have in Q1?" → confirm "active
customer" against the glossary, confirm the join path from `customers` to
`orders`, then query.

**Reject**: "Show me the customers table" with no question attached → ask
what business question the user is trying to answer; this skill answers
questions, it does not dump tables.
