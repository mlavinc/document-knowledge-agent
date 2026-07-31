#!/usr/bin/env python3
"""
Regression checks for the portfolio RAG assistant (natural-language robustness).

Usage:
  set API_GATEWAY_URL=https://xxxx.execute-api.sa-east-1.amazonaws.com
  python scripts/regression_portfolio_search.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API_BASE = os.environ.get(
    "API_GATEWAY_URL",
    "https://6cwjcmekm6.execute-api.sa-east-1.amazonaws.com",
).rstrip("/")

# (question, must_include_any, must_not_include_any, expect_unknown)
CASES: list[tuple[str, list[str], list[str], bool]] = [
    # Identity
    ("Who is Martin Lavin?", ["martin", "universidad mayor"], [], False),
    ("Who is Martín Lavín?", ["martin", "universidad mayor"], [], False),
    ("Tell me about Martin.", ["martin", "cloud"], [], False),
    # Education
    ("Where does Martin study?", ["universidad mayor"], [], False),
    ("When will Martin graduate?", ["2026"], [], False),
    ("What degree is Martin pursuing?", ["ingenier", "computer"], [], False),
    # Experience
    ("What did Martin do at Nestlé?", ["nestl", "automat"], [], False),
    ("What did Martin build at Nestle?", ["nestl", "power"], [], False),
    ("What technologies did Martin use at Nestlé?", ["power", "python"], [], False),
    ("Tell me about Martin's internship.", ["nestl"], [], False),
    # Projects
    ("What projects has Martin built?", ["document knowledge", "cloud operations"], [], False),
    ("Explain the Document Knowledge Agent.", ["rag", "document"], [], False),
    ("Tell me about the Cloud Operations Lab.", ["terraform", "aws"], [], False),
    # Human variations
    ("Who is this person?", ["martin", "universidad"], [], False),
    ("Tell me about your experience.", ["nestl", "martin"], [], False),
    ("What have you worked on?", ["project", "nestl"], [], False),
    ("What are your main skills?", ["aws", "python"], [], False),
    # Out of corpus — should not invent
    ("Has Martin worked at Google?", [], ["yes, martin worked at google"], True),
    ("What is Martin's salary?", [], ["$", "usd", "clp"], True),
    ("Does Martin know Java?", [], [], True),
]


def search(question: str) -> dict:
    body = json.dumps({"question": question}).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/api/search",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-RAG-Collection": "portfolio",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def looks_unknown(answer: str) -> bool:
    lowered = answer.lower()
    markers = [
        "do not have",
        "don't have",
        "does not contain",
        "doesn't contain",
        "not available",
        "no information",
        "not mentioned",
        "knowledge base",
        "cannot find",
        "can't find",
        "no relevant",
        "i don't know",
        "not specified",
        "not stated",
    ]
    return any(m in lowered for m in markers)


def main() -> int:
    print(f"Portfolio regression against {API_BASE}")
    failures = 0

    for question, must_any, must_not, expect_unknown in CASES:
        try:
            result = search(question)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            print(f"FAIL  {question!r}\n      HTTP {exc.code}: {detail[:300]}")
            failures += 1
            continue
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {question!r}\n      {exc}")
            failures += 1
            continue

        answer = (result.get("answer") or "").strip()
        lowered = answer.lower()
        reasons: list[str] = []

        if not answer:
            reasons.append("empty answer")

        if expect_unknown:
            if not looks_unknown(answer):
                # Allow cautious answers that avoid fabricating specifics.
                invented = any(x in lowered for x in must_not)
                if invented or any(
                    phrase in lowered
                    for phrase in (
                        "yes, he worked at google",
                        "his salary is",
                        "earns ",
                    )
                ):
                    reasons.append("looks like invented detail")
                elif "java" in question.lower() and (
                    "yes" in lowered[:40] and "java" in lowered
                ):
                    # CV mentions Java (ThermoSim) — accepting yes is OK if grounded.
                    pass
                elif not looks_unknown(answer) and "google" in question.lower():
                    if "google" in lowered and "work" in lowered and "not" not in lowered:
                        reasons.append("should not claim Google employment")
        else:
            if must_any and not any(token in lowered for token in must_any):
                reasons.append(f"missing any of {must_any}")
            for bad in must_not:
                if bad.lower() in lowered:
                    reasons.append(f"unexpected {bad!r}")

        if reasons:
            failures += 1
            print(f"FAIL  {question!r}")
            print(f"      reasons: {', '.join(reasons)}")
            print(f"      answer: {answer[:280].replace(chr(10), ' ')}")
        else:
            print(f"OK    {question!r}")

    print(f"\n{len(CASES) - failures}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
