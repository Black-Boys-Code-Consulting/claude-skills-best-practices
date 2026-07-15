"""Scoring + static lint logic for the Skill Test Bench.

score_case() mirrors the behavioral-check semantics of
evaluation/skill_eval_harness.py so live results stay consistent with the
CLI harness bundled in this repo. lint_skill() is new: it applies the three
anti-patterns documented in anti_patterns/ as static heuristic checks against
a skill's description and instructions, with no API call required.
"""
import re

GUARDRAIL_KEYWORDS = [
    "must not", "never ", "do not", "read-only", "only if", "explicit",
    "not allowed", "forbidden", "guardrail",
]
TRIGGER_PHRASES = ["use when", "use for", "use if"]
ACTION_KEYWORDS = [
    "database", "delete", "update", "drop", "query", "execute", "run sql",
    "write", "modify", "insert", "sql",
]
EXAMPLE_MARKERS = ["example", "reject", "good:", "bad:"]

STOPWORDS = {
    "the", "a", "an", "and", "or", "use", "when", "for", "to", "of", "in",
    "on", "that", "this", "with", "is", "are", "it", "its", "any",
}


def score_case(must_include, must_not_include, response):
    """Return (passed: bool, failures: list[str]) for one response."""
    failures = []
    response_lower = response.lower()

    for phrase in must_include or []:
        if phrase.strip() and phrase.lower() not in response_lower:
            failures.append(f'missing required content: "{phrase}"')

    for phrase in must_not_include or []:
        if phrase.strip() and phrase.lower() in response_lower:
            failures.append(f'contains forbidden content: "{phrase}"')

    return (len(failures) == 0, failures)


def recommend_for_failure(failure: str) -> str:
    if failure.startswith("missing required content"):
        return (
            "Your skill's instructions don't clearly require this in the output. "
            "Add an explicit 'Output Format' rule stating what must always be included."
        )
    return (
        "Your skill isn't stopping this behavior. Add an explicit guardrail in the "
        "instructions forbidding it, regardless of how the request is phrased."
    )


def _significant_words(s: str):
    return {w for w in re.findall(r"[a-z']+", s.lower()) if w not in STOPWORDS and len(w) > 2}


def _keyword_overlap(a: str, b: str) -> float:
    wa, wb = _significant_words(a), _significant_words(b)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


DISAMBIGUATION_MARKERS = ["not for", "not the", "no support", "different skill", "not this"]


def _has_disambiguation(text: str) -> bool:
    t = text.lower()
    return any(m in t for m in DISAMBIGUATION_MARKERS)


def lint_skill(description: str, instructions: str, compare_description: str = ""):
    """Static heuristic checks, no API call. Returns a list of check results."""
    checks = []
    text = f"{description}\n{instructions}".lower()

    has_trigger = any(p in description.lower() for p in TRIGGER_PHRASES)
    word_count = len(description.split())
    if not has_trigger or word_count < 8:
        checks.append({
            "check": "Specific description",
            "status": "fail",
            "message": (
                "The description doesn't clearly state concrete trigger words or a "
                "'use when...' clause. Claude matches skills against the description "
                "before reading the body — a vague one may never fire, or fire "
                "unpredictably."
            ),
            "anti_pattern": "vague_skill_example.md",
        })
    else:
        checks.append({
            "check": "Specific description",
            "status": "pass",
            "message": "Description names a concrete domain and trigger condition.",
            "anti_pattern": None,
        })

    touches_action = any(k in text for k in ACTION_KEYWORDS)
    has_guardrail = any(k in text for k in GUARDRAIL_KEYWORDS)
    if touches_action and not has_guardrail:
        checks.append({
            "check": "Explicit guardrails",
            "status": "fail",
            "message": (
                "This skill appears to touch data or live actions but doesn't state "
                "explicit limits (e.g. read-only, forbidden operations, row limits). "
                "Unstated constraints get filled in by the model's best guess in "
                "production."
            ),
            "anti_pattern": "underconstrained.md",
        })
    else:
        checks.append({
            "check": "Explicit guardrails",
            "status": "pass",
            "message": "Found explicit guardrail language, or this skill doesn't touch live data/actions.",
            "anti_pattern": None,
        })

    has_examples = any(m in text for m in EXAMPLE_MARKERS)
    checks.append({
        "check": "Concrete examples",
        "status": "pass" if has_examples else "fail",
        "message": (
            "Includes at least one concrete good/bad example." if has_examples else
            "No concrete example interaction found. A skill with no example is hard "
            "to test and hard to calibrate."
        ),
        "anti_pattern": None if has_examples else "docs/skill_anatomy.md",
    })

    if compare_description.strip():
        overlap = _keyword_overlap(description, compare_description)
        shared = _significant_words(description) & _significant_words(compare_description)
        disambiguated = _has_disambiguation(description) or _has_disambiguation(compare_description)
        # Raw keyword-Jaccard understates real risk: two descriptions can share
        # just one domain noun (e.g. "customer") and still be a coin flip for
        # a real user question, unless one of them explicitly rules the other
        # out. So a shared domain word with no disambiguation language is
        # treated as risk regardless of how low the overall Jaccard score is.
        is_risk = bool(shared) and not disambiguated
        checks.append({
            "check": "Overlap with compared skill",
            "status": "fail" if is_risk else "pass",
            "message": (
                f"{round(overlap * 100)}% keyword overlap"
                + (f", shared terms: {', '.join(sorted(shared))}" if shared else "")
                + ". "
                + (
                    "A real user question mentioning these shared terms could plausibly "
                    "match both skills, making which one loads a coin flip. Add explicit "
                    "'NOT for X, see other-skill' language to each description."
                    if is_risk else
                    "No shared domain terms without disambiguation language, so the two "
                    "skills should be distinguishable."
                )
            ),
            "anti_pattern": "overlapping_skills.md" if is_risk else None,
        })

    return checks
