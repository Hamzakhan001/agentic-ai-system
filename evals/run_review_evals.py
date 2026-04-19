from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


DEFAULT_DATASET = "review_dataset.json"
DEFAULT_OUTPUT = "review_eval_report.json"
API_URL = "http://127.0.0.1:8000/api/v1/review"


@dataclass
class EvalResult:
    case_id: str
    passed: bool
    task_type_expected: strπ
    task_type_actual: str
    task_type_match: bool
    expected_phrase_coverage: float
    forbidden_phrase_violations: list[str]
    expected_fact_type_coverage: float
    sources_present: bool
    notes: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--task-type", default=None)
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--timeout", type=float, default=300.0)
    return parser.parse_args()


def load_dataset(dataset_name: str) -> list[dict[str, Any]]:
    path = Path(__file__).with_name(dataset_name)
    return json.loads(path.read_text())


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


def filter_cases(cases: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    filtered = cases

    if args.task_type:
        filtered = [case for case in filtered if case["task_type"] == args.task_type]

    if args.sample and args.limit is not None:
        filtered = random.sample(filtered, min(args.limit, len(filtered)))
        return filtered

    if args.offset:
        filtered = filtered[args.offset :]

    if args.limit is not None:
        filtered = filtered[: args.limit]

    return filtered


def main() -> None:
    args = parse_args()
    dataset = load_dataset(args.dataset)
    dataset = filter_cases(dataset, args)

    if not dataset:
        print("No cases selected.")
        return

    results: list[dict[str, Any]] = []

    with httpx.Client(timeout=args.timeout) as client:
        for idx, case in enumerate(dataset, start=1):
            print(f"[{idx}/{len(dataset)}] Running case: {case['id']}")

            payload = {
                "question": case["question"],
                "task_type": case["task_type"],
                "documents": case["documents"],
                "top_k": case.get("top_k", 3),
            }

            response = client.post(
                API_URL,
                json=payload,
                headers={"X-Eval-Mode": "true"},
            )

            if response.status_code >= 400:
                results.append(
                    {
                        "case_id": case["id"],
                        "passed": False,
                        "error": f"HTTP {response.status_code}",
                        "error_body": response.text,
                    }
                )
                continue

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
    passed = sum(1 for item in results if item.get("passed", False))
    http_errors = sum(1 for item in results if "error" in item)
    scored_cases = sum(1 for item in results if "task_type_match" in item)

    summary = {
        "dataset": args.dataset,
        "offset": args.offset,
        "cases_run": total,
        "passed_cases": passed,
        "http_error_cases": http_errors,
        "scored_cases": scored_cases,
        "pass_rate": passed / total if total else 0.0,
        "task_type_accuracy": sum(1 for item in results if item.get("task_type_match", False)) / total if total else 0.0,
        "avg_phrase_coverage": sum(item.get("expected_phrase_coverage", 0.0) for item in results) / total if total else 0.0,
        "avg_fact_type_coverage": sum(item.get("expected_fact_type_coverage", 0.0) for item in results) / total if total else 0.0,
    }

    report = {
        "summary": summary,
        "results": results,
    }

    output_path = Path(__file__).with_name(args.output)
    output_path.write_text(json.dumps(report, indent=2))

    print("\nSummary:")
    print(json.dumps(summary, indent=2))
    print(f"\nSaved report to: {output_path}")


if __name__ == "__main__":
    main()
