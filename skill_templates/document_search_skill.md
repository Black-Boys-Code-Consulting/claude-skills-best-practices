---
name: document-search-skill
description: Search and cite internal knowledge-base documents (policies, runbooks, past incident reports) to answer questions. Use when the user asks what a policy says, how a process works, or references a past incident, and the answer should come from stored documents rather than general knowledge.
allowed-tools: Read Grep
---

# Document Search Skill

## Scope

Retrieval over the internal knowledge base only. This skill does not answer
from general knowledge and does not answer questions about live system state
(that's a different skill) — only what is written in the indexed documents.

## Retrieval Process

1. Extract 2-4 distinctive keywords from the question — not the whole
   question, and not generic words like "policy" or "process."
2. Search the index for those keywords. If the first search returns nothing
   useful, reformulate with different terms before giving up.
3. Read the matching document(s) in full before answering. Do not answer from
   a snippet or filename alone.
4. If more than one document addresses the question and they disagree, surface
   both and say so rather than picking one silently.

## Citation Rule

Every claim in the answer must trace to a specific document. State which
document supports which claim. If no document supports part of the answer,
say that part is unconfirmed rather than filling the gap from general
knowledge.

## Guardrails

- If no document matches the question after two reformulated searches, say
  so plainly. Do not answer from training data and imply it came from the
  knowledge base.
- Do not paraphrase a document so closely that it reads as a copy — summarize
  in your own words and point to the source for exact wording.
- Documents marked `status: deprecated` in their metadata should be flagged
  as superseded, not cited as current policy.

## Output Format

Lead with the answer. Follow with a short "Sources" list naming the
documents used. If the question spans multiple documents, note where they
agree and where they don't.

## Examples

**Good**: "What's our policy on expense approval over $5,000?" → search
`expense`, `approval`, retrieve the finance policy doc, cite it directly.

**Reject**: "What's our vacation policy?" when no vacation-policy document
exists in the index → say the knowledge base doesn't have this, rather than
answering from general assumptions about typical vacation policies.
