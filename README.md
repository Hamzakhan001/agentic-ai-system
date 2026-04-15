# Agentic AI Complete Legal System

A production-style agentic document review and case preparation system.

## Phase 1 MVP

The first version focuses on a single end-to-end review flow:

1. Intake and task classification
2. Evidence retrieval over provided documents
3. Structured fact extraction
4. Draft generation
5. Critique / self-review
6. Final reviewed output with sources

## Tech Stack

- FastAPI
- LangGraph
- OpenAI
- Pydantic
- Structlog

## Run

```bash
uv sync
uv run uvicorn app.main:app --reload
```

## First endpoint

- `POST /api/v1/review`

This accepts a question plus a list of documents and returns:
- task type
- extracted facts
- draft answer
- critique
- final answer
- sources

## Next Milestones

- Persistent document ingestion
- Vector search
- Review run history
- Human-in-the-loop approval
- Evaluation harness
- Observability and traces
