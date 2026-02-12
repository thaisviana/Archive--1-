---
name: building-sentient-agents
description: Use when building AI agents that need long-term memory, contextual understanding, and autonomous reasoning — especially with LangChain, LangGraph, or knowledge graph architectures. Covers Deep Agents orchestration, LlamaIndex RAG, 3-layer memory (PostgreSQL, pgvector, FalkorDB + Graphiti), LangFuse observability, opinionated prompt engineering, and human-in-the-loop approval workflows.
---

# Sentient Agent Architecture

A complete, opinionated blueprint for building production-grade AI agents with hybrid multi-layered memory. Combines Deep Agents (orchestration), LlamaIndex (RAG), and a 3-layer memory system inspired by Letta and Zep.

## Core Philosophy

1. **Layered Memory**: No single memory system is optimal. Three distinct layers, each for a specific purpose.
2. **Best-of-Breed Tools**: Deep Agents for orchestration, LlamaIndex for ingestion, Graphiti for graph memory.
3. **Asynchronous Maintenance**: Memory consolidation and summarization happen in the background.
4. **Explicit Tool-Based Memory Editing**: The agent has auditable control over its own structured memory.
5. **Descriptive Tool Naming**: Tools use `action_noun` convention (e.g., `search_knowledge_base`, not `kb_search`).
6. **Observability First**: Every layer is traced via LangFuse from day one.

## Architecture Overview

| Component | Technology | Purpose |
|---|---|---|
| **Orchestration** | Deep Agents | Agent lifecycle, middleware, tool execution |
| **RAG Ingestion** | LlamaIndex | Contextual Retrieval for knowledge base |
| **Memory Layer 1** | PostgreSQL | Structured, editable memory blocks (agent's "mind") |
| **Memory Layer 2** | PostgreSQL + pgvector (LlamaIndex) | Semantic memory: conversation history + KB docs (hybrid search) |
| **Memory Layer 3** | FalkorDB + Graphiti | Temporal knowledge graph of entities/relationships |
| **Observability** | LangFuse | Tracing, evaluation, cost tracking |
| **Default Model** | `gpt-5-mini-2025-08-07` | Primary LLM |

See `references/architecture-overview.md` for detailed component diagram and decisions.

## Quick Start

```bash
# 1. Clone and setup
git clone <repo-url> && cd sentient-agent
cp templates/env.example .env  # Edit with your API keys

# 2. Launch infrastructure
docker-compose -f templates/docker-compose.yml up -d

# 3. Install dependencies
pip install -r references/requirements.txt

# 4. Initialize database schemas
python -c "from references.sqlalchemy_models import Base, engine; Base.metadata.create_all(engine)"

# 5. Ingest your knowledge base
python scripts/ingest_documents.py --path /path/to/your/docs
```

## Development Phases

### Phase 0: Project Onboarding
**Start here.** See `references/project-setup.md` for the full guided questionnaire.
- Collect: system prompt foundation, model/provider, agent identity
- Define memory blocks: label, char_limit, description, initial_value, read_only
- Set context window budget for dynamic memory injection
- Configure knowledge base directory and ingestion method
- Define Graphiti ontology (entity types, relationship types, fact patterns)

### Phase 1: Project Setup
- Environment and dependencies from `references/requirements.txt`
- Infrastructure via `templates/docker-compose.yml` (PostgreSQL+pgvector, FalkorDB)
- Environment variables via `templates/env.example`

### Phase 2: Memory Implementation
See `references/memory-system.md` for full implementation guide.
- **Layer 1** (Structured): `references/sqlalchemy_models.py` - MemoryBlock + BlockHistory models
- **Layer 2** (Semantic): PostgreSQL + pgvector via LlamaIndex PGVectorStore (hybrid search)
- **Layer 3** (Graph): FalkorDB + Graphiti via FalkorDriver

### Phase 3: RAG Pipeline
See `references/rag-pipeline.md` for Contextual Retrieval strategy.
- Ingestion: `scripts/ingest_documents.py` using LlamaIndex IngestionPipeline
- Retrieval: `search_knowledge_base` tool querying `kb_docs` namespace

### Phase 4: Agent Orchestration
See `references/agent-orchestration.md` for middleware stack and assembly.
- Deep Agents `create_deep_agent()` with full middleware stack
- Memory tools: `references/memory_tools.py` (8 tools)
- Assembly: `references/agent_assembly.py`

### Phase 5: Observability
See `references/observability.md` for LangFuse integration.
- LangChain: `CallbackHandler` for Deep Agents
- LlamaIndex: `LlamaIndexInstrumentor` for RAG pipeline
- Custom: `@observe()` decorator for memory operations

### Phase 6: Prompt Engineering
See `references/prompt-patterns.md` for opinionated patterns.
- System prompt structure with 4-layer hierarchy
- Persona definition separated from instructions
- Memory block injection pattern
- Few-shot examples for tool usage

### Phase 7: Human-in-the-Loop
See `references/human-in-the-loop.md` for approval workflows.
- `interrupt_on` configuration for high-stakes tools
- Confidence thresholds for auto-execution
- Escalation patterns with checkpointer

## Implementation Checklist

When building a sentient agent from this skill, copy this checklist and track progress:

**IMPORTANT — Existing project conflict resolution:**
Before starting, inspect the current repository state. If the project already exists with its own structure, dependencies, or patterns that differ from this checklist:
1. Identify each conflict between what this skill prescribes and what the project already has
2. Present the conflicts explicitly to the user (e.g., "This skill uses SQLAlchemy for memory blocks, but your project already uses Prisma for ORM")
3. Ask the user which approach to follow for EACH conflict
4. Never silently override existing project decisions — the user's existing choices take priority until they say otherwise

**Feedback loop rule:** After each VALIDATE step, if validation fails: review the error, fix the issue, and re-run validation. Only proceed to the next group when all validations pass.

```
Onboarding (see references/project-setup.md):
- [ ] Collect system prompt foundation (file path, folder, or written description)
- [ ] Confirm model and provider, verify API key in .env
- [ ] Define agent name and description
- [ ] Define memory blocks (label, char_limit, description, initial_value, read_only per block)
- [ ] Set context window budget for dynamic injection
- [ ] Identify knowledge base directory and ingestion method (contextual retrieval or standard)
- [ ] Define Graphiti ontology (entity types, relationships, fact patterns)

Setup:
- [ ] Clone repo and copy templates/env.example → .env
- [ ] Add API keys to .env (OPENAI_API_KEY, LANGFUSE keys)
- [ ] Run docker-compose -f templates/docker-compose.yml up -d
- [ ] pip install -r references/requirements.txt
- [ ] python -c "from references.sqlalchemy_models import Base, engine; Base.metadata.create_all(engine)"
- [ ] VALIDATE: Connect to PostgreSQL and verify memory_blocks table exists
- [ ] VALIDATE: Run redis-cli -h localhost -p 6379 ping → expect PONG (FalkorDB)

Memory (see references/memory-system.md):
- [ ] Run init_default_blocks() to create 5 default blocks
- [ ] VALIDATE: Call view_memory_blocks() → expect 5 blocks (persona, user_profile, preferences, working_context, learnings)
- [ ] Test rethink_memory_block on persona block with custom content
- [ ] VALIDATE: Call view_memory_blocks("persona") → expect updated content
- [ ] Configure LlamaIndex PGVectorStore with hybrid_search=True for kb_docs and conversations tables
- [ ] Configure FalkorDB + Graphiti with FalkorDriver
- [ ] VALIDATE: Run graphiti.add_episode() with test data → no errors

RAG Pipeline (see references/rag-pipeline.md):
- [ ] Verify LlamaIndex PGVectorStore config in scripts/ingest_documents.py
- [ ] Ingest test documents: python scripts/ingest_documents.py --path ./test-docs
- [ ] VALIDATE: Query pgvector store directly for a known term from test docs → expect results
- [ ] Implement search_knowledge_base tool using LlamaIndex hybrid retriever
- [ ] VALIDATE: Call search_knowledge_base("known term from test docs") → expect matching chunks
- [ ] Implement search_conversation_history tool (same pattern, `conversations` table)

Knowledge Graph (see references/memory-system.md):
- [ ] Implement search_knowledge_graph tool
- [ ] Test graphiti.add_episode() with sample conversation
- [ ] VALIDATE: Call search_knowledge_graph for an entity mentioned in sample → expect match
- [ ] Verify entity extraction in FalkorDB browser (localhost:3000)

Agent Assembly (see references/agent-orchestration.md):
- [ ] Customize SYSTEM_PROMPT persona for your use case
- [ ] Add WHY motivation to each Priority instruction
- [ ] Uncomment 3 search tools in agent_assembly.py
- [ ] Implement inject_memory (@before_model) — see references/agent-orchestration.md
- [ ] Implement summarize_if_needed (@before_model)
- [ ] Implement save_to_graph (@after_model)
- [ ] Implement rethink_memory (@after_model)
- [ ] Uncomment custom middleware in agent_assembly.py
- [ ] VALIDATE: Run one agent turn with a simple greeting → expect response without errors

Observability (see references/observability.md):
- [ ] Verify LangFuse connection (check LANGFUSE_BASE_URL)
- [ ] VALIDATE: Run one agent turn → confirm trace appears in LangFuse dashboard
- [ ] Initialize LlamaIndexInstrumentor for RAG tracing
- [ ] VALIDATE: Run search_knowledge_base via agent → confirm RAG trace in LangFuse

End-to-End Validation:
- [ ] Ask factual question → agent calls search_knowledge_base → grounded answer
- [ ] Share preference → agent calls rethink_memory_block → confirms update
- [ ] Trigger delete_memory_block → verify interrupt_on pauses for approval
- [ ] Check LangFuse: all 3 integration points (LangChain, LlamaIndex, @observe) traced
```

## Toolset (11 Tools)

| Layer | Tools | Phase |
|---|---|---|
| **PostgreSQL** | `insert_memory_block`, `replace_memory_content`, `rethink_memory_block`, `finish_memory_edits`, `create_memory_block`, `delete_memory_block`, `rename_memory_block`, `view_memory_blocks` | Memory |
| **pgvector** | `search_knowledge_base`, `search_conversation_history` | Research |
| **Knowledge Graph** | `search_knowledge_graph` | Research |

## Implementation Status

This skill is a **template and reference guide**, not a turnkey application. Below is the status of each component:

| Component | Status | Files | Notes |
|---|---|---|---|
| **Project Setup Guide** | Onboarding guide | `references/project-setup.md` | Guided questionnaire for new agent projects |
| **SQLAlchemy Models** | Reference code | `scripts/memory/layer1_blocks/models.py` | Working models with tests (ported from `references/`) |
| **Memory Tools (8)** | Reference code | `scripts/memory/layer1_blocks/tools.py` | Working tools with 21 tests (ported from `references/`) |
| **Agent Assembly** | Reference code | `references/agent_assembly.py` | Functional skeleton, 3 search tools commented out |
| **Ingestion Script** | Stub | `scripts/ingest_documents.py` | Vector store connection is TODO |
| **Docker Compose** | Ready to use | `templates/docker-compose.yml` | PostgreSQL+pgvector and FalkorDB |
| **Env Template** | Ready to use | `templates/env.example` | All required variables |
| `search_knowledge_base` | Reference code | `scripts/memory/layer2_semantic/tools.py` | LlamaIndex hybrid retriever with 7 tests |
| `search_conversation_history` | Reference code | `scripts/memory/layer2_semantic/tools.py` | Same pattern, `conversations` table |
| `search_knowledge_graph` | Reference code | `scripts/memory/layer3_graph/tools.py` | Graphiti client with 6 tests |
| **Custom Middleware** | Reference code | `scripts/memory/middleware/` | 4 hooks with 22 tests (`inject_memory`, `summarize_if_needed`, `save_to_graph`, `rethink_memory`) |
| **Memory Config** | Reference code | `scripts/memory/config.py` | Shared config: env vars, DB engine, constants |
| **Prompt Patterns** | Opinionated guide | `references/prompt-patterns.md` | Patterns and anti-patterns, adapt to your agent |
| **HITL Workflows** | Opinionated guide | `references/human-in-the-loop.md` | Confidence thresholds, escalation patterns |
| **Observability** | Integration guide | `references/observability.md` | LangFuse setup for all layers |

The canonical implementations live in `scripts/memory/`. Import all tools and middleware:

```python
from scripts.memory import ALL_MEMORY_TOOLS     # 11 tools
from scripts.memory import ALL_CUSTOM_MIDDLEWARE  # 4 hooks
```

Run the test suite: `pytest scripts/memory/tests/ -v` (56 tests, ~1s).

## Companion Skills

Install these alongside for enhanced development:

| Skill | Source | Purpose |
|---|---|---|
| **langgraph-docs** | `@langchain-ai/deepagents` | Up-to-date LangGraph documentation |
| **LangGraph Patterns** | `@frankxai/claude-code-config` | Production workflow patterns |
| **llamaindex** | `@zechenzhangAGI/claude-ai-research-skills` | LlamaIndex reference |
| **langfuse-observability** | `langfuse/skills` | LangFuse integration patterns |
