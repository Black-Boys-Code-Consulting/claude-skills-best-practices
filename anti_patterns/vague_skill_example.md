# Anti-Pattern: The Vague Skill

## The Skill As Written

```
---
name: helper
description: Helps with data stuff
---

# Helper

Help the user with whatever they need related to data. Use good judgment
and be helpful.
```

## Why It Fails

**The description never fires.** Claude decides whether to use a skill based
on matching the user's request against the `description` field before it
ever reads the body. "Helps with data stuff" doesn't contain a single word a
real question would match against — no table names, no task type, no trigger
phrase. In practice this skill sits unused, and the team that wrote it
concludes "skills don't work" when the real problem is the description gave
the model nothing to match on.

**The body gives no operational instruction.** Even in the rare case this
skill does load, "use good judgment and be helpful" is not an instruction —
it's the default behavior Claude already has without the skill. A skill that
doesn't narrow behavior below the model's defaults isn't doing anything; it's
just tokens sitting in context.

**There's no way to test whether it "works."** Because it has no concrete
rules, there's no observable output to check it against. A skill you can't
evaluate is a skill you can't improve.

## The Fix

Compare against `skill_templates/data_query_skill.md`: the description names
the exact domain (`sales data warehouse`) and lists trigger words a real
question would contain (`revenue`, `customers`, `orders`). The body gives
concrete, checkable rules (confirm join path, confirm metric definition,
500-row limit) instead of a general instruction to "be helpful."

**Rule of thumb**: if you can't picture the exact user sentence that should
trigger this skill, the description isn't specific enough yet.
