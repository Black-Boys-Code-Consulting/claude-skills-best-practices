# Skill Test Bench

A small web app version of this repo's evaluation harness. A client pastes in
their own Claude skill (description + instructions), adds a few test prompts,
and gets back:

- A **static lint** (no API key needed) that checks the skill text itself
  against the three anti-patterns in `../anti_patterns/` — vague description,
  missing guardrails, missing examples, and (optionally) overlap with a
  second skill's description.
- A **live test**: the app calls the Claude API with the client's skill
  loaded as the system prompt, runs each test prompt, and scores the real
  response using the same pass/fail logic as `../evaluation/skill_eval_harness.py`
  (`must_include` / `must_not_include` phrase checks) — plus a plain-language
  recommendation for each failure.

The "load an example" buttons on the page pull live from this repo's own
`skill_templates/`, `evaluation/regression_suite.yaml`, and `anti_patterns/`,
so the demo always matches the actual bundled assets.

## Run locally

```bash
cd webapp/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000. Paste in an Anthropic API key in the UI to run a
live test (or set `ANTHROPIC_API_KEY` in the backend's environment if you
want a hosted demo that doesn't require visitors to bring their own key —
see the cost note below).

## API key handling

- The frontend has a password field for an Anthropic API key. It's sent only
  in the body of the `/api/evaluate` request, used once to call the Claude
  API, and never written to disk or logged.
- If the request omits a key, the backend falls back to the server's
  `ANTHROPIC_API_KEY` environment variable, if set. Only enable that on a
  hosted demo if you're comfortable covering the API cost of anyone who uses
  it — there's no rate limiting or usage cap built in.

## Deploying

This is a plain FastAPI app serving a static frontend — deploy it anywhere
that runs a Python process (Render, Railway, Fly.io, a VPS behind
`gunicorn -k uvicorn.workers.UvicornWorker`, etc.). No database, no build
step for the frontend.

A `render.yaml` blueprint is included at the repo root for Render: New +
→ Blueprint → point it at this repo. It deploys `webapp/backend` as a free
web service with no `ANTHROPIC_API_KEY` set, so every visitor brings their
own key for the live test — the hosted instance never bears anyone's API
cost.

## Files

```
backend/
  main.py         FastAPI app: /api/lint, /api/evaluate, /api/examples, serves frontend/
  scoring.py       score_case() (ported from evaluation/skill_eval_harness.py) + lint_skill()
  examples.py      loads good examples from ../../skill_templates + regression_suite.yaml,
                    bad examples transcribed from ../../anti_patterns
  requirements.txt
frontend/
  index.html
  app.js
  style.css
```
