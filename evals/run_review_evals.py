from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


DATASET_PATH = Path(__file__).with_name("review_dataset_500.json")
API_URL = "http://127.0.0.1:8000/api/v1/review"
REPORT_PATH = Path(__file__).with_name("review_eval_report.json")


@dataclass
class EvalResult:
    case_id: str
    passed: bool
    task_type_expected: str
    task_type_actual: str
    task_type_match: bool
    expected_phrase_coverage: float
    forbidden_phrase_violations: list[str]
    expected_fact_type_coverage: float
    sources_present: bool
    notes: list[str]


def load_dataset() -> list[dict[str, Any]]:
    return json.loads(DATASET_PATH.read_text())


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def phrase_coverage(answer: str, expected_phrases: list[str]) -> tuple[float, list[str]]:
    if not expected_phrases:
        return 1.0, []

    answer_norm = normalize(answer)
    matched = [phrase for phrase in expected_phrases if normalize(phrase) in answer_norm]
    coverage = len(matched) / len(expected_phrases)
    return coverage, matched


def forbidden_violations(answer: str, forbidden_phrases: list[str]) -> list[str]:
    answer_norm = normalize(answer)
    return [phrase for phrase in forbidden_phrases if normalize(phrase) in answer_norm]


def fact_type_coverage(extracted_facts: list[dict[str, Any]], expected_fact_types: list[str]) -> tuple[float, list[str]]:
    if not expected_fact_types:
        return 1.0, []

    actual_types = {fact.get("type", "") for fact in extracted_facts}
    matched = [fact_type for fact_type in expected_fact_types if fact_type in actual_types]
    coverage = len(matched) / len(expected_fact_types)
    return coverage, matched


def score_case(case: dict[str, Any], response: dict[str, Any]) -> EvalResult:
    final_answer = response.get("final_answer", "")
    extracted_facts = response.get("extracted_facts", [])
    sources = response.get("sources", [])
    actual_task_type = response.get("task_type", "")

    phrase_score, matched_phrases = phrase_coverage(final_answer, case.get("expected_phrases", []))
    fact_score, matched_fact_types = fact_type_coverage(extracted_facts, case.get("expected_fact_types", []))
    violations = forbidden_violations(final_answer, case.get("forbidden_phrases", []))
    task_type_match = actual_task_type == case["task_type"]
    sources_present = len(sources) > 0

    notes: list[str] = []
    notes.append(f"matched_phrases={matched_phrases}")
    notes.append(f"matched_fact_types={matched_fact_types}")

    passed = (
        task_type_match
        and phrase_score >= 0.5
        and fact_score >= 0.5
        and not violations
        and sources_present
    )

    return EvalResult(
        case_id=case["id"],
        passed=passed,
        task_type_expected=case["task_type"],
        task_type_actual=actual_task_type,
        task_type_match=task_type_match,
        expected_phrase_coverage=phrase_score,
        forbidden_phrase_violations=violations,
        expected_fact_type_coverage=fact_score,
        sources_present=sources_present,
        notes=notes,
    )


def main() -> None:
    dataset = load_dataset()
    results: list[dict[str, Any]] = []

    with httpx.Client(timeout=90.0) as client:
        for case in dataset:
            payload = {
                "question": case["question"],
                "task_type": case["task_type"],
                "documents": case["documents"],
                "top_k": case.get("top_k", 3),
            }

            response = client.post(API_URL, json=payload)
            response.raise_for_status()
            review_output = response.json()

            eval_result = score_case(case, review_output)
            results.append(
                {
                    "case_id": eval_result.case_id,
                    "passed": eval_result.passed,
                    "task_type_expected": eval_result.task_type_expected,
                    "task_type_actual": eval_result.task_type_actual,
                    "task_type_match": eval_result.task_type_match,
                    "expected_phrase_coverage": eval_result.expected_phrase_coverage,
                    "forbidden_phrase_violations": eval_result.forbidden_phrase_violations,
                    "expected_fact_type_coverage": eval_result.expected_fact_type_coverage,
                    "sources_present": eval_result.sources_present,
                    "notes": eval_result.notes,
                    "raw_response": review_output,
                }
            )

    total = len(results)
    passed = sum(1 for item in results if item["passed"])

    summary = {
        "total_cases": total,
        "passed_cases": passed,
        "pass_rate": passed / total if total else 0.0,
        "task_type_accuracy": sum(1 for item in results if item["task_type_match"]) / total if total else 0.0,
        "avg_phrase_coverage": sum(item["expected_phrase_coverage"] for item in results) / total if total else 0.0,
        "avg_fact_type_coverage": sum(item["expected_fact_type_coverage"] for item in results) / total if total else 0.0,
    }

    report = {
        "summary": summary,
        "results": results,
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"\nSaved report to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
