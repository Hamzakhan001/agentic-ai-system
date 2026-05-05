# Agentic Legal Review Backend

Industry-grade multi-agent backend for legal document review, evidence extraction, and AI-assisted workflow automation, built with FastAPI, LangGraph, PostgreSQL, Pinecone, Phoenix, and configurable LLM providers.

Designed for real-world AI delivery rather than notebook demos, the system supports document ingestion, evidence retrieval, specialised agent orchestration, persisted review runs, human approval and revision workflows, offline evaluation, and trace-based observability for operational reliability.

It also includes A2A protocol integration, enabling external agents and organisational systems to interact with the backend for review execution, workflow handoff, and interoperable agent-driven automation.

## System Architecture

<!-- Keep the existing System Architecture graph / Mermaid block here -->

## Agent Workflow

<!-- Keep the existing Agent Workflow graph / Mermaid block here -->

## Evaluation and Observability Loop

<!-- Keep the existing Evaluation and Observability Loop graph / Mermaid block here -->

## Overview

This backend is designed as an industry-grade foundation for agentic AI applications in legal and document-heavy workflows.

It combines:
- multi-agent orchestration with LangGraph
- retrieval over ingested documents and Pinecone
- A2A protocol integration for external agent interoperability
- Postgres-backed run persistence and revision lineage
- API-based human approval and revision workflows
- Phoenix tracing for observability and debugging
- offline evaluation for regression-style benchmarking

The focus is on building reliable, inspectable, and extensible AI systems that can move from prototype to operational deployment.

## Core Capabilities

- Multi-agent review orchestration
- Document ingestion and vector retrieval
- Task routing across multiple review types
- Fact extraction, drafting, critique, and finalization
- External tool integration for supplementary context
- Persistent review run storage in Postgres
- Human approval and revision support
- Offline evaluation harness for benchmark testing
- Trace-based debugging and latency visibility
- A2A protocol support for external agent and system integration

## Supported Review Tasks

The backend supports:
- document summarisation
- legal / contractual risk review
- evidence extraction
- practical next-step recommendations
- timeline generation

## Request Lifecycle

1. A review request is submitted through the API.
2. The request is routed through a LangGraph-based multi-agent workflow.
3. Relevant evidence is retrieved from inline documents or Pinecone.
4. Optional external context is gathered through research tools.
5. Memory is loaded from persisted case context where available.
6. Facts are extracted from source evidence.
7. A draft answer is generated when appropriate.
8. The answer is critiqued and finalised.
9. The run is persisted in Postgres.
10. Human reviewers can approve or request revisions.
11. External agent and organisational workflows can interact through A2A-compatible integration paths.

## Persistence Model

The backend persists review lifecycle data such as:
- question
- task type
- status
- extracted facts
- draft answer
- critique output
- final answer
- sources
- external context
- reviewer notes
- revision lineage

This enables:
- run history
- auditability
- human review
- evaluation analysis
- trace correlation

## Tech Stack

### Backend
- Python
- FastAPI
- LangGraph
- SQLModel
- PostgreSQL

### Retrieval and Storage
- Pinecone
- document chunking and embeddings
- Postgres-backed review state
- lightweight durable memory

### LLM / AI
- OpenAI
- Ollama
- Anthropic-compatible workflows
- external tools
- multi-agent orchestration
- A2A protocol integration

### Evaluation and Observability
- Phoenix
- offline evaluation runner
- trace-based failure and latency analysis
- structured debugging and review lineage

## API Endpoints

Main endpoints include:
- `POST /api/v1/ingest/text`
- `POST /api/v1/ingest/file`
- `POST /api/v1/review`
- `GET /api/v1/review-runs`
- `GET /api/v1/review-runs/{run_id}`
- `POST /api/v1/review-runs/{run_id}/approve`
- `POST /api/v1/review-runs/{run_id}/revise`

## Running Locally

### Install dependencies
```bash
uv sync
