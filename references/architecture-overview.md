# Architecture Overview

## System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    DEEP AGENTS ORCHESTRATOR                   │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────────────┐ │
│  │ Middleware   │ │ Tool Router  │ │ Sub-Agent Dispatcher  │ │
│  │ Stack (7)    │ │ (11 tools)   │ │                       │ │
│  └─────────────┘ └──────────────┘ └───────────────────────┘ │
│  Model: gpt-5-mini-2025-08-07                                │
└──┬───────────────┬───────────────┬───────────────┬──────────┘
   │               │               │               │
┌──▼───┐    ┌──────▼──────┐  ┌────▼────┐   ┌─────▼──────┐
│Layer1│    │   Layer 2    │  │ Layer 3 │   │  LangFuse  │
│  PG  │    │ PG+pgvector  │  │FalkorDB │   │Observability│
│SQLAlc│    │  LlamaIndex  │  │+Graphiti│   │            │
└──────┘    └──────────────┘  └─────────┘   └────────────┘
 Structured    Semantic        Knowledge       Tracing
 Memory        Memory          Graph           & Eval
```

## Component Decisions

### Why Deep Agents (not raw LangChain or custom loop)
- Built-in middleware system for cross-cutting concerns
- Native sub-agent support for task delegation
- Skills and filesystem middleware included
- Compaction middleware for context window management
- Inspired by Claude Code architecture

### Why LlamaIndex for RAG (not LangChain loaders)
- Superior IngestionPipeline with parallel processing
- SentenceSplitter optimized for retrieval
- Contextual Retrieval strategy support (see cookbook: `contextual_retrieval.ipynb`)
- Native `PGVectorStore` with `hybrid_search=True` (vector + full-text keyword)
- Better document connector ecosystem (300+)
- Single framework for both ingestion and retrieval — no cross-framework compatibility issues

### Why 3-Layer Memory (not single vector store)
- **Layer 1 (PostgreSQL)**: Structured, human-readable, agent-editable beliefs
  - The agent's "conscious mind" - explicit facts it knows about itself and the user
  - Versioned via BlockHistory for auditability
- **Layer 2 (pgvector)**: Semantic search over unstructured content
  - Conversation history retrieval by meaning
  - Knowledge base document search
- **Layer 3 (FalkorDB + Graphiti)**: Temporal relationships
  - Entity extraction across conversations
  - Fact expiration and temporal reasoning
  - Relationship discovery between concepts

### Why FalkorDB (not Neo4j)
- Lower resource footprint (Redis protocol, port 6379)
- No authentication required for local instances
- Dedicated Graphiti `FalkorDriver` support
- GraphBLAS-based sparse matrix representation for speed

### Why LangFuse (not LangSmith)
- Open-source, self-hostable
- Native integrations with both LangChain and LlamaIndex
- Built-in evaluation framework
- PostHog integration for product analytics
- Prompt management and versioning

### Why gpt-5-mini-2025-08-07
- Optimal balance of capability and cost for tool-heavy agents
- Reliable tool calling with 11+ tool definitions
- Fast enough for real-time conversational agents

## Middleware Stack Order

The order matters. Each middleware wraps the next:

```
1. TodoListMiddleware        → Task planning and tracking
2. SubAgentMiddleware        → Delegate complex tasks to specialists
3. SkillsMiddleware          → Dynamic skill loading
4. FilesystemMiddleware      → File read/write operations
5. CompactionMiddleware      → Context window management
6. inject_memory             → Inject dynamic memory blocks into user message (@before_model)
7. summarize_if_needed       → Compress conversation if over token threshold (@before_model)
8. save_to_graph             → Write episode to Graphiti knowledge graph (@after_model)
9. rethink_memory            → Update memory blocks after summarization (@after_model)
```

Middleware 1-5 are built-in Deep Agents middleware.
Middleware 6-9 use `@before_model` / `@after_model` decorators (see `references/agent-orchestration.md`).
