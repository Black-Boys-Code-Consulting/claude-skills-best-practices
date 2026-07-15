# Anatomy of a Well-Formed Skill

A skill is a folder with a `SKILL.md` file at minimum. The file has two
parts: YAML frontmatter, and a markdown body. Both matter, and they matter
for different reasons.

## Frontmatter

Only `description` is functionally load-bearing for discovery — it's what
Claude matches against the user's request to decide whether this skill is
relevant *before* it ever reads the body. `name` should match the parent
folder name. Everything else is optional, but three fields are worth using
deliberately:

- `allowed-tools` — pre-approves a narrow set of tools instead of leaving
  tool access as broad as the environment allows. Use this on any skill that
  touches something consequential.
- `disable-model-invocation` — forces manual invocation via `/skill-name`
  instead of letting Claude decide when to run it. Use this for anything
  with real consequences (see `workflow_skill.md` — you don't want a
  postmortem auto-triggering because an outage was mentioned in passing).
- `context: fork` — runs the skill in an isolated subagent so its work
  doesn't pollute the main conversation. Useful for verbose, self-contained
  tasks; not useful for a skill that's meant to inform the ongoing
  conversation, since the fork doesn't see conversation history.

**Write the description like a trigger, not a summary.** "Helps with data
stuff" tells Claude nothing to match against. "Answer business questions
against the sales data warehouse... Use when the user asks about revenue,
customers, orders..." gives Claude concrete phrases from real questions to
match. See `anti_patterns/vague_skill_example.md` for what happens when this
is skipped.

## Body: Scope, Constraints, Examples, Guardrails

A well-formed skill body has four load-bearing sections, in this rough order:

1. **Scope** — what this skill is for, and just as important, what it is
   explicitly *not* for. A skill with no stated boundary invites use on
   questions it was never designed to handle.
2. **Constraints** — the concrete, checkable rules the skill must follow.
   "Use good judgment" is not a constraint; "row limit: 500" is. If a rule
   can't be checked against an actual output, it isn't doing anything (see
   `anti_patterns/underconstrained.md`).
3. **Examples** — at least one example of correct behavior and one example
   of a request that should be declined or redirected. Examples resolve
   ambiguity that prose alone leaves open.
4. **Guardrails** — an explicit list of what the skill must never do. For
   any skill touching a live system, name at least three forbidden actions
   outright, not just implied ones.

## Progressive Disclosure

Keep the main `SKILL.md` file lean — every line loads into context and stays
there for the rest of the conversation once the skill fires, so it's a
recurring token cost, not a one-time one. If a skill needs supporting
material — a join map, a style guide, a long reference table — put it in a
separate file and reference it from the main body. Claude reads supporting
files on demand rather than loading everything upfront.

## Checklist Before Shipping a Skill

- [ ] Description contains words a real user question would actually contain
- [ ] Scope states what the skill is *not* for
- [ ] Every rule in Constraints is checkable against an actual output
- [ ] At least one "reject" example, not just "accept" examples
- [ ] At least three explicit guardrails for anything touching a live system
- [ ] No overlapping description with another skill in the same deployment
- [ ] A regression suite case exists for every guardrail (see `testing_guide.md`)
