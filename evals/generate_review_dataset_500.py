from __future__ import annotations

import json
import random
from pathlib import Path

OUTPUT_PATH = Path(__file__).with_name("review_dataset_500.json")
random.seed(42)

TASK_COUNTS = {
    "summary": 100,
    "risk_review": 120,
    "evidence_extraction": 120,
    "next_steps": 80,
    "timeline": 80,
}

DIFFICULTIES = ["easy", "medium", "hard"]
SCENARIOS = [
    "single_doc_clear",
    "multi_doc_consistent",
    "multi_doc_conflicting",
    "insufficient_evidence",
    "noisy_context",
    "ambiguous_language",
    "deadline_heavy",
    "risk_heavy",
    "obligation_heavy",
    "timeline_heavy",
]

PARTIES = [
    ("Alpha Ltd", "Beta Services Ltd"),
    ("Northstar PLC", "Cedar Analytics Ltd"),
    ("Maple Foods Ltd", "Riverstone Logistics Ltd"),
    ("Helios Energy Ltd", "Brightpath Systems Ltd"),
    ("UrbanGrid Ltd", "FieldOps Solutions Ltd"),
]

GOVERNING_LAWS = ["England and Wales", "Scotland", "Northern Ireland"]
NOTICE_PERIODS = [7, 10, 14, 21, 30, 45, 60, 90]
PAYMENT_DAYS = [7, 10, 14, 15, 21, 30, 45]
PRICE_NOTICE_DAYS = [7, 14, 30]
SERVICE_LEVELS = ["99.5%", "99.9%", "98.0%"]
START_DATES = [
    "1 January 2026",
    "15 February 2026",
    "5 March 2026",
    "22 April 2026",
    "10 May 2026",
]
EVENT_DATES = [
    "12 January 2026",
    "20 February 2026",
    "18 March 2026",
    "30 April 2026",
    "16 May 2026",
]
RISK_PATTERNS = [
    "Liability is uncapped for data loss.",
    "The provider may change pricing on {price_notice} days notice.",
    "The customer has broad indemnity obligations.",
    "Service credits are the sole remedy for downtime.",
    "Subcontracting is permitted without prior consent.",
    "Confidentiality obligations are limited to 12 months after termination.",
]
OBLIGATION_PATTERNS = [
    "Payment is due within {payment_days} days of invoice.",
    "Either party may terminate with {notice_days} days written notice.",
    "Monthly reporting must be delivered by the 5th business day of each month.",
    "The supplier must maintain service availability of {sla}.",
    "The customer must provide all required data within 3 business days of request.",
]
EVENT_PATTERNS = [
    "The agreement starts on {start_date}.",
    "A service failure was recorded on {event_date}.",
    "The counterparty raised formal concerns on {event_date}.",
    "A written notice was issued on {event_date}.",
]
EXTRA_NOISE = [
    "The parties discussed future collaboration informally.",
    "Brand guidelines may be updated from time to time.",
    "Marketing materials are subject to separate approval.",
    "Internal workshop notes were attached for context.",
]
QUESTION_MAP = {
    "summary": "Summarise these documents in plain English. Include purpose, obligations, dates, risks, and termination terms.",
    "risk_review": "Identify the main legal, contractual, and compliance risks in these documents.",
    "evidence_extraction": "Extract all dates, obligations, risks, entities, and events from these documents.",
    "next_steps": "Based on these documents, what practical next steps should be taken?",
    "timeline": "Create a chronological timeline of the key dates, notices, obligations, and events in these documents.",
}


def pick(seq):
    return random.choice(seq)


def build_doc(
    party_a: str,
    party_b: str,
    scenario: str,
    idx: int,
    primary: bool = True,
) -> dict:
    start_date = pick(START_DATES)
    event_date = pick(EVENT_DATES)
    notice_days = pick(NOTICE_PERIODS)
    payment_days = pick(PAYMENT_DAYS)
    price_notice = pick(PRICE_NOTICE_DAYS)
    sla = pick(SERVICE_LEVELS)
    law = pick(GOVERNING_LAWS)

    risk_sentences = [
        pick(RISK_PATTERNS).format(price_notice=price_notice),
        pick(RISK_PATTERNS).format(price_notice=price_notice),
    ]
    obligation_sentences = [
        pick(OBLIGATION_PATTERNS).format(payment_days=payment_days, notice_days=notice_days, sla=sla),
        pick(OBLIGATION_PATTERNS).format(payment_days=payment_days, notice_days=notice_days, sla=sla),
    ]
    event_sentences = [
        pick(EVENT_PATTERNS).format(start_date=start_date, event_date=event_date),
        pick(EVENT_PATTERNS).format(start_date=start_date, event_date=event_date),
    ]

    clauses = [
        f"This agreement is between {party_a} and {party_b}.",
        event_sentences[0],
        obligation_sentences[0],
        risk_sentences[0],
        f"The governing law is {law}.",
    ]

    if scenario in {"multi_doc_conflicting", "ambiguous_language"} and not primary:
        clauses.append(
            f"Either party may terminate with {max(7, notice_days - 7)} days written notice."
        )
    else:
        clauses.append(f"Either party may terminate with {notice_days} days written notice.")

    if scenario == "insufficient_evidence":
        clauses = [
            f"This document references a commercial arrangement between {party_a} and {party_b}.",
            "Some operational terms are described at a high level.",
            "Detailed liability, termination, and payment clauses are not included here.",
        ]

    if scenario == "noisy_context":
        clauses.extend(random.sample(EXTRA_NOISE, k=2))

    if scenario == "deadline_heavy":
        clauses.extend(
            [
                f"Payment is due within {payment_days} days of invoice.",
                f"The provider may change pricing on {price_notice} days notice.",
                f"A written notice was issued on {event_date}.",
            ]
        )

    if scenario == "timeline_heavy":
        clauses.extend(
            [
                f"The agreement starts on {start_date}.",
                f"A service failure was recorded on {event_date}.",
                f"The counterparty raised formal concerns on {pick(EVENT_DATES)}.",
            ]
        )

    if scenario == "risk_heavy":
        clauses.extend(
            [
                "Liability is uncapped for confidentiality breaches.",
                "Subcontracting is permitted without prior consent.",
                "Service credits are the sole remedy for downtime.",
            ]
        )

    if scenario == "obligation_heavy":
        clauses.extend(
            [
                f"The customer must provide all required data within 3 business days of request.",
                f"The supplier must maintain service availability of {sla}.",
                f"Monthly reporting must be delivered by the 5th business day of each month.",
            ]
        )

    title = f"{'Primary' if primary else 'Supplemental'} Agreement {idx}"
    return {
        "id": f"doc-{idx}-{'p' if primary else 's'}",
        "title": title,
        "text": " ".join(clauses),
        "metadata": {
            "scenario": scenario,
            "primary": primary,
        },
    }


def expected_fact_types_for_task(task: str) -> list[str]:
    if task == "summary":
        return ["date", "obligation", "risk"]
    if task == "risk_review":
        return ["risk", "obligation"]
    if task == "evidence_extraction":
        return ["date", "obligation", "risk", "entity", "event"]
    if task == "next_steps":
        return ["obligation", "risk", "event"]
    if task == "timeline":
        return ["date", "event", "obligation"]
    return ["date", "obligation", "risk"]


def expected_phrases_for_task(task: str, docs: list[dict], scenario: str) -> list[str]:
    text = " ".join(doc["text"] for doc in docs).lower()
    phrases = []

    candidates = [
        "written notice",
        "payment is due",
        "liability is uncapped",
        "governing law",
        "service failure",
        "pricing on",
        "service availability",
        "monthly reporting",
        "counterparty raised formal concerns",
    ]

    for phrase in candidates:
        if phrase in text:
            phrases.append(phrase)

    if task == "next_steps":
        phrases.extend(["review", "confirm", "assess"])
    if task == "risk_review":
        phrases.extend(["risk", "liability"])
    if task == "timeline":
        phrases.extend(["agreement starts", "notice", "recorded"])
    if scenario == "insufficient_evidence":
        phrases = ["insufficient evidence"]

    # keep signal high, not huge
    return list(dict.fromkeys(phrases[:5]))


def forbidden_phrases_for_scenario(scenario: str) -> list[str]:
    base = ["employment law", "tax advice", "patent infringement"]
    if scenario == "insufficient_evidence":
        base.extend(["clearly states", "definitively requires"])
    return base


def build_case(task: str, index: int) -> dict:
    scenario = SCENARIOS[index % len(SCENARIOS)]
    difficulty = DIFFICULTIES[index % len(DIFFICULTIES)]
    party_a, party_b = PARTIES[index % len(PARTIES)]

    docs = [build_doc(party_a, party_b, scenario, index, primary=True)]
    if scenario in {"multi_doc_consistent", "multi_doc_conflicting", "noisy_context"}:
        docs.append(build_doc(party_a, party_b, scenario, index, primary=False))

    question = QUESTION_MAP[task]
    if scenario == "insufficient_evidence":
        question = f"{question} If information is missing, say so clearly."
    if scenario == "multi_doc_conflicting":
        question = f"{question} If the documents conflict, identify the conflict."
    if difficulty == "hard":
        question += " Be precise and avoid unsupported claims."

    return {
        "id": f"{task}_{index:03d}",
        "task_type": task,
        "difficulty": difficulty,
        "scenario": scenario,
        "question": question,
        "documents": docs,
        "top_k": 4 if len(docs) > 1 else 3,
        "expected_phrases": expected_phrases_for_task(task, docs, scenario),
        "forbidden_phrases": forbidden_phrases_for_scenario(scenario),
        "expected_fact_types": expected_fact_types_for_task(task),
    }


def build_dataset() -> list[dict]:
    dataset = []
    for task, count in TASK_COUNTS.items():
        for i in range(1, count + 1):
            dataset.append(build_case(task, i))
    return dataset


def main() -> None:
    dataset = build_dataset()
    OUTPUT_PATH.write_text(json.dumps(dataset, indent=2))
    print(f"Generated {len(dataset)} cases")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
