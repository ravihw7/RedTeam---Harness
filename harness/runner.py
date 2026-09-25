"""
Orchestrates a full run:
  1. Load a YAML test suite into the DB (idempotent - won't duplicate test cases)
  2. Send each test case's prompt to the target model
  3. Score the response (rule-based or LLM judge)
  4. Save everything to the DB so the dashboard can show it
"""

from datetime import datetime, timezone

import yaml

from harness.db import get_session, init_db
from harness.judge import llm_judge, rule_based_refusal_check
from harness.models import Category, Result, Run, TestCase
from harness.target import call_target_model


def load_suite(path: str, session) -> None:
    with open(path) as f:
        data = yaml.safe_load(f)

    for cat in data["categories"]:
        category = session.query(Category).filter_by(name=cat["name"]).first()
        if not category:
            category = Category(name=cat["name"], description=cat.get("description", ""))
            session.add(category)
            session.flush()

        for tc in cat["test_cases"]:
            exists = (
                session.query(TestCase)
                .filter_by(prompt=tc["prompt"], category_id=category.id)
                .first()
            )
            if not exists:
                session.add(
                    TestCase(
                        category_id=category.id,
                        prompt=tc["prompt"],
                        expected_behavior=tc["expected_behavior"],
                        severity=tc.get("severity", "medium"),
                        notes=tc.get("notes", ""),
                    )
                )
    session.commit()


def run_suite(
    suite_path: str,
    target_model: str,
    judge_model: str,
    use_llm_judge: bool = True,
    verbose: bool = True,
) -> int:
    init_db()
    session = get_session()
    load_suite(suite_path, session)

    run = Run(model_name=target_model, started_at=datetime.now(timezone.utc))
    session.add(run)
    session.flush()

    test_cases = session.query(TestCase).all()

    for tc in test_cases:
        response_text, latency_ms = call_target_model(tc.prompt, model=target_model)

        if use_llm_judge:
            passed, rationale = llm_judge(
                tc.prompt, tc.expected_behavior, response_text, judge_model=judge_model
            )
        else:
            refused = rule_based_refusal_check(response_text)
            passed = refused if tc.expected_behavior == "refuse" else not refused
            rationale = "rule-based keyword match (no LLM judge used)"

        session.add(
            Result(
                run_id=run.id,
                test_case_id=tc.id,
                response_text=response_text,
                passed=passed,
                judge_rationale=rationale,
                latency_ms=latency_ms,
            )
        )

        if verbose:
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] {tc.category.name} #{tc.id}: {tc.prompt[:60]}...")

    run.finished_at = datetime.now(timezone.utc)
    session.commit()
    run_id = run.id
    session.close()
    return run_id
