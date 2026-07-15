---
name: incident-postmortem-workflow
description: Run the incident postmortem workflow after a production incident is resolved - draft the timeline, root cause section, and action items in the standard template. Use when the user says an incident is resolved and asks for a postmortem, retro, or writeup.
disable-model-invocation: true
allowed-tools: Read Write Bash
---

# Incident Postmortem Workflow

This skill is explicit-invoke only (`/incident-postmortem-workflow`). A
postmortem is a consequential document — it should be started because a human
asked for it, not because the model inferred an incident might be over.

## Step 1 — Gather Timeline

Pull the incident timeline from the linked tracking ticket or chat log the
user provides. Do not invent timestamps. If a timestamp is missing, mark it
`[unconfirmed]` rather than estimating.

## Step 2 — Draft Root Cause

State the proximate cause (what broke) and the root cause (why the system
allowed it to break) as two separate statements. Do not conflate them — "the
database ran out of connections" is proximate; "there was no connection pool
alerting" is root cause.

## Step 3 — Action Items

Every action item needs an owner and a rough timeframe. An action item with
no owner is a wish, not a plan — flag any unowned item back to the user
instead of leaving it blank.

## Step 4 — Blameless Language Check

Before finalizing, scan the draft for language that names an individual as
the cause of the incident. Rewrite toward the system or process gap that
allowed the mistake to happen. This is a hard rule, not a style preference.

## Step 5 — Output

Produce the postmortem in the standard template (Summary, Timeline, Root
Cause, Impact, Action Items, Lessons Learned). Save it, don't just print it
inline, so it can be attached to the incident ticket.

## Guardrails

- Do not mark an incident postmortem "final" if any action item lacks an
  owner — return it as a draft pending owners instead.
- Do not run this skill automatically just because the conversation mentions
  an outage; it must be explicitly invoked.
