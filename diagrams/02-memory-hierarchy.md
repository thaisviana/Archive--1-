# Memory Hierarchy — The 3 Memory Layers

The memory system is inspired by Letta and Zep: no single memory system is optimal for all use cases. Each layer serves a distinct purpose. Memory blocks are split by mutability: static blocks (persona, user_profile) stay in the system prompt for cache stability, while dynamic blocks (preferences, working_context, learnings) are injected into the user message.

## Layer Overview

```mermaid
flowchart TB
    subgraph AGENT[Agent]
        SYS[System Prompt (active context)]
    end

    subgraph L1[Layer 1 — Structured Memory]
        direction TB
        L1_DESC[Agents conscious mind — Explicit, editable beliefs]
        L1_DB[(PostgreSQL: MemoryBlock + BlockHistory)]
        L1_TOOLS[8 Memory Tools (CRUD + versioning)]
        L1_DESC --- L1_DB
        L1_DB --- L1_TOOLS
    end

    subgraph L2[Layer 2 — Semantic Memory]
        direction TB
        L2_DESC[Meaning-based search over unstructured content]
        L2_DB[(PostgreSQL + pgvector — Hybrid Search (RRF))]
        L2_NS[Namespaces: conversations | kb_docs]
        L2_DESC --- L2_DB
        L2_DB --- L2_NS
    end

    subgraph L3[Layer 3 — Knowledge Graph]
        direction TB
        L3_DESC[Temporal relationships between entities]
        L3_DB[(FalkorDB + Graphiti — Graph + Episodes)]
        L3_CAP[Entity extraction, fact expiration, temporal reasoning]
        L3_DESC --- L3_DB
        L3_DB --- L3_CAP
    end

    SYS -->|Static blocks (persona, profile) in system prompt — dynamic blocks in user message| L1
    AGENT -->|search_knowledge_base, search_conversation_history| L2
    AGENT -->|search_knowledge_graph| L3
    L1 -->|Static blocks cached in prompt, dynamic blocks per turn| SYS

```

## How Each Layer Maps to Agent Context Types

```mermaid
flowchart LR
    subgraph CONTEXT_TYPES[Agent Context Types]
        direction TB
        SI[System Instructions (who the agent is)]
        RC[Retrieved Context (on-demand search)]
        CH[Conversation History (semantic history)]
        LTM[Long-term Memory (persistent beliefs)]
    end

    subgraph LAYERS[Memory Layers]
        direction TB
        ML1[Layer 1: persona, preferences]
        ML2_KB[Layer 2: kb_docs namespace]
        ML2_CONV[Layer 2: conversations namespace]
        ML3[Layer 3: Graphiti temporal graph]
    end

    SI ---|injected by middleware| ML1
    RC ---|search tools| ML2_KB
    RC ---|search tools| ML3
    CH ---|search_conversation_history| ML2_CONV
    LTM ---|editable blocks| ML1
    LTM ---|temporal facts| ML3

```

## Default Memory Blocks (Layer 1)

```mermaid
flowchart TD
    subgraph BLOCKS[5 Default MemoryBlocks]
        subgraph STATIC[Static — System Prompt (cached, read-only)]
            P[persona — 2000 chars, read-only]
            UP[user_profile — 3000 chars, editable]
        end
        subgraph DYNAMIC[Dynamic — User Message (per turn, editable)]
            PR[preferences — 2000 chars]
            WC[working_context — 4000 chars]
            LE[learnings — 3000 chars]
        end
    end

    subgraph LIMITS[Block Size Management]
        THRESHOLD[At 80% of char_limit: auto-compress via rethink]
        OFFLOAD[If still over limit: offload overflow to StoreBackend]
    end

    subgraph AUDIT[Audit Trail]
        BH[(BlockHistory: Versioned snapshot of every change)]
    end

    P & UP & PR & WC & LE -->|every edit generates a record| BH
    PR & WC & LE -.->|when approaching limit| THRESHOLD
    THRESHOLD -.->|overflow content| OFFLOAD

```

## Key Decisions

- **Why 3 layers?** — No single memory system is universal. Layer 1 is the "conscious mind" (editable), Layer 2 is semantic search (passive), Layer 3 captures temporal relationships that the other layers cannot.
- **Why hybrid injection?** — Static blocks (persona, user_profile) rarely change and belong in the system prompt for KV-cache stability. Dynamic blocks (preferences, working_context, learnings) change frequently and are injected into the user message to avoid cache invalidation.
- **Why pgvector with RRF?** — Combines vector similarity with keyword search (full-text). Essential for ambiguous queries where embeddings alone or keywords alone would fail.
- **Why FalkorDB?** — Lower footprint than Neo4j, Redis protocol, no auth needed for local dev, native Graphiti support via `FalkorDriver`.
- **Why versioning (BlockHistory)?** — Audit and rollback. The agent edits its own memory; without history, mistakes would be irreversible.
- **Why char_limit per block?** — Unbounded blocks would eventually consume the entire context window. Fixed limits force the agent to be concise and trigger automatic compression at 80%.
- **Why read-only blocks?** — Some blocks (like persona) define identity and should never be modified by the agent at runtime. Only the builder can change them.
- **Why offload to StoreBackend?** — When a block exceeds its limit even after compression, overflow goes to Deep Agents persistent storage. The content remains searchable via Layer 2 but is not injected every turn.
