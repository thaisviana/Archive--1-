# Architecture Overview

High-level view of the Sentient Agent architecture showing how all layers connect.

```mermaid
flowchart TB
    UI[User Interface]

    subgraph ORCH[Deep Agents Orchestrator]
        direction TB
        MW[Middleware Stack (8 layers)]
        TR[Tool Router (11 tools)]
        SA[Sub-Agent Dispatcher]
        MODEL[LLM (configurable)]
    end

    subgraph MEMORY[3-Layer Memory System]
        direction LR
        subgraph L1[Layer 1: Structured]
            PG[PostgreSQL: MemoryBlocks]
        end
        subgraph L2[Layer 2: Semantic]
            PGV[PostgreSQL + pgvector — Hybrid Search (RRF)]
        end
        subgraph L3[Layer 3: Knowledge Graph]
            FK[FalkorDB + Graphiti — Temporal Graph]
        end
    end

    subgraph RAG[RAG Pipeline]
        LI[LlamaIndex: Contextual Retrieval]
    end

    subgraph OBS[Observability]
        LF[LangFuse: Tracing + Eval]
    end

    UI -->|user input| ORCH
    ORCH -->|8 memory tools| L1
    ORCH -->|search_knowledge_base, search_conversation_history| L2
    ORCH -->|search_knowledge_graph| L3
    LI -->|ingest, embed, store| PGV
    ORCH -.->|traces| LF
    LI -.->|traces| LF
    L1 -.->|@observe| LF
    ORCH -->|response| UI

```

## Key Decisions

| Decision | Choice | Rejected Alternative | Reason |
|---|---|---|---|
| Orchestration | Deep Agents | Raw LangChain | Native middleware, sub-agents, compaction |
| RAG | LlamaIndex | LangChain Loaders | Superior IngestionPipeline, 300+ connectors |
| Graph DB | FalkorDB | Neo4j | Lower footprint, Redis protocol, Graphiti support |
| Observability | LangFuse | LangSmith | Open-source, self-hostable, built-in evaluation |
| Model | Configurable LLM | — | Supports any model with tool-calling capability |
