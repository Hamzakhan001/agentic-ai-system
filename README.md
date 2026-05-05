# Agentic Legal Review Backend

Industry-grade multi-agent backend for legal document review, evidence extraction, and AI-assisted workflow automation, built with FastAPI, LangGraph, PostgreSQL, Pinecone, Phoenix, and configurable LLM providers.

The system supports document ingestion, grounded retrieval, specialised multi-agent orchestration, persisted review runs, human approval and revision workflows, offline evaluation, and trace-based observability for operational reliability.

It also includes A2A protocol integration, enabling external agents and organisational systems to interact with the backend for review execution, workflow handoff, and interoperable agent-driven automation.

## System Architecture

```mermaid
flowchart LR
    A["Client / API Consumer"] --> B["FastAPI API Layer"]
    B --> C["LangGraph Orchestrator"]

    C --> D["RouterAgent"]
    C --> E["RetrieverAgent"]
    C --> F["ResearchAgent"]
    C --> G["MemoryAgent"]
    C --> H["ExtractorAgent"]
    C --> I["DraftingAgent"]
    C --> J["CriticAgent"]
    C --> K["FinalizeAgent"]

    E --> L["Pinecone Vector Store"]
    F --> M["External Tools"]
    G --> N["Postgres Persistence"]
    B --> N
    B --> O["Phoenix Tracing"]
    B --> P["LLM Provider<br/>OpenAI / Ollama"]

    style B fill:#eef4ff,stroke:#4a6ee0,stroke-width:1.5px
    style C fill:#f5f3ff,stroke:#7c4dff,stroke-width:1.5px
    style N fill:#eefaf1,stroke:#2f9e44,stroke-width:1.5px
    style L fill:#fff8e8,stroke:#d97706,stroke-width:1.5px
    style O fill:#fff1f2,stroke:#e11d48,stroke-width:1.5px
    style P fill:#f4f4f5,stroke:#52525b,stroke-width:1.5px

```

Agent Workflow

```mermaid
flowchart TD
    A["Review Request"] --> B["RouterAgent"]
    B --> C["RetrieverAgent"]
    C --> D["ResearchAgent"]
    D --> E["MemoryAgent"]
    E --> F["ExtractorAgent"]
    F --> G{"Task Type"}

    G -->|Evidence Extraction| H["FinalizeAgent"]
    G -->|Summary / Risk Review / Next Steps / Timeline| I["DraftingAgent"]

    I --> J["CriticAgent"]
    J --> H["FinalizeAgent"]
    H --> K["Persist Review Run"]

    style A fill:#eef4ff,stroke:#4a6ee0,stroke-width:1.5px
    style F fill:#fff8e8,stroke:#d97706,stroke-width:1.5px
    style H fill:#eefaf1,stroke:#2f9e44,stroke-width:1.5px
    style K fill:#fff1f2,stroke:#e11d48,stroke-width:1.5px

```

Evaluation and Observability Loop

```mermaid
flowchart LR
    A["Benchmark Dataset"] --> B["Offline Eval Runner"]
    B --> C["Review API"]
    C --> D["Multi-Agent Workflow"]
    D --> E["Evaluation Report"]
    D --> F["Phoenix Traces"]
    E --> G["Failure Analysis"]
    F --> G
    G --> H["Prompt / Workflow / System Improvements"]

    style A fill:#eef4ff,stroke:#4a6ee0,stroke-width:1.5px
    style B fill:#f5f3ff,stroke:#7c4dff,stroke-width:1.5px
    style E fill:#eefaf1,stroke:#2f9e44,stroke-width:1.5px
    style F fill:#fff1f2,stroke:#e11d48,stroke-width:1.5px
    style H fill:#fff8e8,stroke:#d97706,stroke-width:1.5px

```
