# Data Flow End-to-End — A Complete Turn

Complete data flow of an agent turn, from user input to final response, showing all layers involved.

## Scenario: User asks a factual question and shares a preference

```mermaid
sequenceDiagram
    participant U as User
    participant IM as inject_memory
    participant AG as Agent Core
    participant L1 as PostgreSQL
    participant L2 as pgvector (LlamaIndex)
    participant L3 as FalkorDB
    participant SG as save_to_graph
    participant LF as LangFuse

    Note over U,LF: PHASE 1 — Context Preparation (@before_model)

    U->>IM: What is the refund policy?
    IM->>L1: SELECT dynamic blocks (preferences, working_context, learnings)
    L1-->>IM: 3 dynamic blocks
    Note over IM: Static blocks (persona, profile) already in system prompt — inject dynamic blocks into user message
    IM->>AG: System prompt (cached) + user message with dynamic memory

    Note over U,LF: PHASE 2 — Reasoning + Tool Calls

    AG->>AG: Factual question — Tier 2
    AG->>L2: search_knowledge_base(refund policy)
    L2->>L2: Hybrid: vector + keyword search
    L2-->>AG: 3 relevant chunks
    AG->>LF: trace: search tool call

    AG->>AG: New preference detected
    AG->>L1: rethink_memory_block(preferences)
    L1->>L1: BlockHistory snapshot
    L1->>L1: UPDATE preferences
    L1-->>AG: Block preferences updated
    AG->>LF: trace: memory update

    Note over U,LF: PHASE 3 — Response + Persistence (@after_model)

    AG->>AG: Generate response with context
    AG-->>SG: Response in bullet points

    SG->>L3: graphiti.add_episode(turn)
    L3->>L3: Extract entities + relationships
    SG->>LF: trace: graph write

    SG-->>U: Refund policy: 30 days, 5 business days

    Note over LF: Trace available in dashboard

```

## Macro View: Where each data type lives

```mermaid
flowchart TB
    subgraph USER_DATA[User Data]
        PROFILE[Profile and Preferences]
        DOCS[Documents / KB]
        CONV[Conversations]
    end

    subgraph STORAGE[Where each data type is stored]
        subgraph PG[PostgreSQL]
            MB[memory_blocks (Layer 1) — with char_limit + read_only]
            BH[block_history (audit trail)]
            KB[kb_docs (Layer 2 — pgvector)]
            CV[conversations (Layer 2 — pgvector)]
        end
        subgraph FK[FalkorDB]
            NODES[Entity Nodes (Layer 3)]
            EDGES[Entity Edges / Facts (Layer 3)]
            EP[Episodes (Layer 3)]
        end
        subgraph DA[Deep Agents StoreBackend]
            OVERFLOW[/memory/overflow/ — offloaded block content]
        end
    end

    PROFILE -->|rethink_memory_block| MB
    MB -->|every edit| BH
    MB -.->|when block exceeds char_limit| OVERFLOW
    DOCS -->|ingest_documents.py| KB
    CONV -->|automatic embedding| CV
    CONV -->|automatic add_episode| EP
    EP -->|automatic extraction| NODES
    EP -->|automatic extraction| EDGES

```

## Infrastructure (Docker Compose)

```mermaid
flowchart LR
    subgraph DOCKER[docker-compose.yml]
        subgraph PG_SVC[postgres]
            PG_IMG[PostgreSQL 17 + pgvector extension]
            PG_PORT[Port: 5432]
            PG_DB[DB: agent_memory]
            PG_HEALTH[Healthcheck: pg_isready]
        end
        subgraph FK_SVC[falkordb]
            FK_IMG[FalkorDB (Redis protocol)]
            FK_PORT1[Port: 6379 (Redis)]
            FK_PORT2[Port: 3000 (Browser UI)]
            FK_HEALTH[Healthcheck: redis-cli ping]
        end
    end

    APP[Agent Application] -->|SQLAlchemy + LlamaIndex pgvector| PG_SVC
    APP -->|Graphiti FalkorDriver| FK_SVC

```
