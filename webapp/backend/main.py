"""Skill Test Bench — a small web app so a client can paste in their own
Claude skill, run it live against Claude, and get a pass/fail behavioral
score plus recommendations, using the same checks as evaluation/skill_eval_harness.py.

Run locally:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

Then open http://localhost:8000
"""
import json
import os
from pathlib import Path
from typing import List, Optional

from anthropic import Anthropic, APIError
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from examples import get_examples
from scoring import lint_skill, recommend_for_failure, score_case

app = FastAPI(title="Skill Test Bench")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

MODELS = {
    "sonnet": "claude-sonnet-5",
    "haiku": "claude-haiku-4-5-20251001",
    "opus": "claude-opus-4-8",
}


class TestCase(BaseModel):
    id: str
    prompt: str
    must_include: List[str] = []
    must_not_include: List[str] = []
    notes: Optional[str] = ""


class LintRequest(BaseModel):
    description: str
    instructions: str
    compare_description: Optional[str] = ""


class EvaluateRequest(BaseModel):
    description: str
    instructions: str
    test_cases: List[TestCase]
    api_key: Optional[str] = ""
    model: str = "sonnet"


@app.post("/api/lint")
def lint(req: LintRequest):
    return {"checks": lint_skill(req.description, req.instructions, req.compare_description or "")}


@app.post("/api/evaluate")
def evaluate(req: EvaluateRequest):
    """Streams newline-delimited JSON events as each test case runs, so the
    frontend can reveal results one step at a time instead of waiting for the
    whole batch. Each line is one of:
      {"type": "start", "index", "total", "id", "prompt"}
      {"type": "result", "index", "total", "passed_so_far", "id", "prompt",
       "passed", "response", "failures", "recommendations", "notes"}
      {"type": "done", "passed", "total"}
    """
    api_key = req.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            400,
            "No API key provided. Enter an Anthropic API key to run a live test "
            "(it's used only for this request and is never stored or logged).",
        )
    if not req.test_cases:
        raise HTTPException(400, "Add at least one test case before running a live test.")

    model = MODELS.get(req.model, MODELS["sonnet"])
    client = Anthropic(api_key=api_key)
    skill_text = f"{req.description}\n\n{req.instructions}".strip()
    total = len(req.test_cases)

    def run_case(case):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=1024,
                system=skill_text,
                messages=[{"role": "user", "content": case.prompt}],
            )
            response_text = "".join(
                block.text for block in resp.content if getattr(block, "type", None) == "text"
            )
        except APIError as e:
            return {
                "id": case.id,
                "prompt": case.prompt,
                "passed": False,
                "response": None,
                "failures": [f"API error: {e}"],
                "recommendations": [],
                "notes": case.notes,
            }

        ok, failures = score_case(case.must_include, case.must_not_include, response_text)
        return {
            "id": case.id,
            "prompt": case.prompt,
            "passed": ok,
            "response": response_text,
            "failures": failures,
            "recommendations": [recommend_for_failure(f) for f in failures],
            "notes": case.notes,
        }

    def generate():
        passed = 0
        for i, case in enumerate(req.test_cases, start=1):
            yield json.dumps({
                "type": "start", "index": i, "total": total,
                "id": case.id, "prompt": case.prompt,
            }) + "\n"

            result = run_case(case)
            if result["passed"]:
                passed += 1
            yield json.dumps({
                "type": "result", "index": i, "total": total, "passed_so_far": passed,
                **result,
            }) + "\n"

        yield json.dumps({"type": "done", "passed": passed, "total": total}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@app.get("/api/examples")
def examples():
    return get_examples()


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
