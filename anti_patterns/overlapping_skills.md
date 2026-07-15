# Anti-Pattern: Overlapping Skills

## The Skills As Written

```
---
name: customer-lookup
description: Look up customer information. Use when the user asks about a customer.
---
Query the `customers` table directly for whatever the user asks.
```

```
---
name: customer-support-query
description: Answer customer questions using the customer data warehouse. Use for customer-related questions.
---
Query `customers` joined to `support_tickets` and answer using the join map
in reference/join_map.md.
```

## Why It Fails

Both descriptions match the same class of question — "look up customer
information" and "customer-related questions" overlap almost entirely.  When
a real question like *"what's this customer's ticket history?"* comes in,
both skills are plausible matches, and which one actually loads is now a
coin flip driven by wording rather than by team intent.

This produces two failure modes, both worse than having no skill at all:

- **Inconsistent behavior on the same question asked twice.** One run uses
  the join map and metric definitions from `customer-support-query`; the next
  run loads `customer-lookup` and queries `customers` directly with no join
  discipline at all. Same question, two different answers, and no way to
  predict which one you'll get.
- **Silent guardrail bypass.** If `customer-lookup` has none of the row
  limits or test-account filters that `customer-support-query` enforces, the
  system behaves as if the guardrail didn't exist roughly half the time —
  which is far more dangerous than a guardrail that's visibly absent,
  because it *looks* like it's being enforced.

## The Fix

Merge into one skill with one clear boundary, or make the boundary between
them non-overlapping and explicit in both descriptions:

```
description: Look up raw customer record fields (name, plan, signup date)
  with no support-ticket context. Use for account-detail lookups only —
  NOT for support-history or ticket questions, see customer-support-query.
```

```
description: Answer questions that require joining customer records to
  support tickets (ticket history, open issues, escalations). Use for
  support-context questions — NOT for plain account-detail lookups, see
  customer-lookup.
```

**Rule of thumb**: if you can construct a real user sentence that would
plausibly match two of your skills' descriptions, that's the bug — not a
detail to fix later.
