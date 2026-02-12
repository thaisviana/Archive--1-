# Memory System

## Contents
- Context Model — how the 3 layers map to agent context types
- Layer 1: Structured Memory (PostgreSQL) — schema, default blocks, 8 memory tools
- Layer 2: Semantic Memory (PostgreSQL + pgvector) — hybrid search, language config, namespaces
- Layer 3: Knowledge Graph (FalkorDB + Graphiti) — setup, episodes, fact triples, search

## Context Model

The 3 memory layers map to the standard agent context types:

| Context Type | Layer | Placement | Role |
|---|---|---|---|
| **System instructions** | Layer 1 (`persona`, `user_profile`) | System prompt (static, cached) | Identity and profile — rarely change |
| **Dynamic memory** | Layer 1 (`preferences`, `working_context`, `learnings`) | User message (dynamic) | Frequently changing blocks injected per turn |
| **Retrieved context** | Layer 2 (pgvector) + Layer 3 (Graphiti) | Tool results | Search results from tools |
| **Conversation history** | Layer 2 (`conversations` namespace) | Tool results | Semantic search over past conversations |
| **Long-term memory** | Layer 1 (editable blocks) + Layer 3 (temporal graph) | Both | Persistent beliefs and relationships |

## Layer 1: Structured Memory (PostgreSQL)

The agent's "conscious mind". Stores explicit, editable beliefs organized in labeled blocks.

### Schema

See `sqlalchemy_models.py` for full implementation.

```python
from datetime import datetime, timezone

class MemoryBlock(Base):
    __tablename__ = 'memory_blocks'
    id = Column(Integer, primary_key=True)
    label = Column(String, unique=True, nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=False, default="")
    char_limit = Column(Integer, nullable=False, default=2000)
    read_only = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    history = relationship("BlockHistory", back_populates="block")

class BlockHistory(Base):
    __tablename__ = 'block_history'
    id = Column(Integer, primary_key=True)
    block_id = Column(Integer, ForeignKey('memory_blocks.id'))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    block = relationship("MemoryBlock", back_populates="history")
```

### Default Memory Blocks

Every sentient agent starts with these blocks. Customize via `references/project-setup.md` during onboarding.

| Block Label | Placement | Char Limit | Read-Only | Description |
|---|---|---|---|---|
| `persona` | System prompt (static) | 2000 | Yes | Agent identity and personality. Only changed by the builder. |
| `user_profile` | System prompt (static) | 3000 | No | Known facts about the user: name, role, preferences. Update when user shares personal info. |
| `preferences` | User message (dynamic) | 2000 | No | Interaction preferences: language, tone, formatting. Update when user expresses a preference. |
| `working_context` | User message (dynamic) | 4000 | No | Current task/project focus. Most volatile block — update frequently as topics shift. |
| `learnings` | User message (dynamic) | 3000 | No | Accumulated insights about what works for this user. Update when patterns emerge. |

### Block Size Management

Every block has a `char_limit`. When a block reaches **80% of its limit**, the `rethink_memory` hook triggers automatic compression:

1. **Compress** — The agent rewrites the block to be more concise, preserving essential information
2. **Offload** — If the block still exceeds its limit after compression, overflow content is offloaded to the filesystem (Deep Agents `StoreBackend`) where it remains searchable via Layer 2 but is not injected into every turn
3. **Read-only enforcement** — Blocks with `read_only=true` cannot be edited by the agent via memory tools. They are injected into context but only the builder can change them.

### Memory Tools (8 tools)

See `memory_tools.py` for implementation stubs.

| Tool | Purpose |
|---|---|
| `insert_memory_block` | Insert text at specific line in a block |
| `replace_memory_content` | Replace string in a block |
| `rethink_memory_block` | Rewrite entire block content |
| `finish_memory_edits` | Signal completion of batch edits |
| `create_memory_block` | Create new labeled block |
| `delete_memory_block` | Remove a block |
| `rename_memory_block` | Change block label |
| `view_memory_blocks` | View all blocks or specific block |

## Layer 2: Semantic Memory (PostgreSQL + pgvector)

Stores embeddings for hybrid search (vector similarity + full-text keyword) across two tables. Uses **LlamaIndex** `PGVectorStore` with native `hybrid_search` support for both ingestion and retrieval.

### Configuration

```python
from sqlalchemy import make_url
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding

DATABASE_URL = os.environ["DATABASE_URL"]
url = make_url(DATABASE_URL)

kb_vector_store = PGVectorStore.from_params(
    database=url.database,
    host=url.host,
    password=url.password,
    port=url.port,
    user=url.username,
    table_name="kb_docs",
    embed_dim=1536,
    hybrid_search=True,
    text_search_config="portuguese",
    hnsw_kwargs={
        "hnsw_m": 16,
        "hnsw_ef_construction": 64,
        "hnsw_ef_search": 40,
        "hnsw_dist_method": "vector_cosine_ops",
    },
)

conversations_vector_store = PGVectorStore.from_params(
    database=url.database,
    host=url.host,
    password=url.password,
    port=url.port,
    user=url.username,
    table_name="conversations",
    embed_dim=1536,
    hybrid_search=True,
    text_search_config="portuguese",
    hnsw_kwargs={
        "hnsw_m": 16,
        "hnsw_ef_construction": 64,
        "hnsw_ef_search": 40,
        "hnsw_dist_method": "vector_cosine_ops",
    },
)
```

### Hybrid Search

LlamaIndex's `PGVectorStore` with `hybrid_search=True` combines pgvector similarity with PostgreSQL `tsvector` keyword search. Query using `vector_store_query_mode="hybrid"`:

```python
from llama_index.core import VectorStoreIndex

index = VectorStoreIndex.from_vector_store(vector_store=kb_vector_store)

# Simple hybrid retrieval (returns raw chunks, no LLM synthesis)
retriever = index.as_retriever(
    vector_store_query_mode="hybrid",
    similarity_top_k=5,
    sparse_top_k=5,
)
nodes = retriever.retrieve("política de reembolso")
```

For more control over fusion, use `QueryFusionRetriever`:

```python
from llama_index.core.retrievers import QueryFusionRetriever

vector_retriever = index.as_retriever(vector_store_query_mode="default", similarity_top_k=5)
text_retriever = index.as_retriever(vector_store_query_mode="sparse", similarity_top_k=5)

retriever = QueryFusionRetriever(
    [vector_retriever, text_retriever],
    similarity_top_k=5,
    num_queries=1,
    mode="reciprocal_rerank",
)
```

### Language Configuration for Portuguese

The `text_search_config` parameter controls PostgreSQL full-text search behavior: stemming, stop words, and tokenization.

| `text_search_config` Value | Behavior |
|---|---|
| `"portuguese"` | Portuguese stemming + stop words (built-in) |
| `"english"` | English stemming + stop words |
| `"simple"` | No stemming, no stop words (multilingual fallback) |
| `"pt_unaccent"` | Custom config with accent-insensitive search (see below) |

**For Portuguese content, always use `"portuguese"`** — it handles stemming ("computadores" → "comput"), removes Portuguese stop words ("de", "que", "em", "um"), and normalizes verb conjugations.

### Accent-Insensitive Search (Recommended for pt-BR)

Brazilian Portuguese users often search without accents ("coracao" instead of "coração"). To handle this, create a custom text search configuration with `unaccent`:

```sql
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TEXT SEARCH CONFIGURATION pt_unaccent (COPY = portuguese);

ALTER TEXT SEARCH CONFIGURATION pt_unaccent
    ALTER MAPPING FOR hword, hword_part, word
    WITH unaccent, portuguese_stem;
```

Then use `text_search_config="pt_unaccent"` in `PGVectorStore.from_params()`. This enables:
- "São Paulo" matches "sao paulo"
- "coração" matches "coracao"
- "José" matches "jose"

Add these SQL statements to your database initialization script or run them after `docker-compose up`.

### Tables

| Table | Content | Use Case |
|---|---|---|
| `conversations` | Conversation history embeddings | "What did we discuss about X?" |
| `kb_docs` | Knowledge base document chunks | "Find docs about Y" |

### Search Tools

| Tool | Table | Purpose |
|---|---|---|
| `search_conversation_history` | `conversations` | Semantic search over past conversations |
| `search_knowledge_base` | `kb_docs` | Search ingested documents |

## Layer 3: Knowledge Graph (FalkorDB + Graphiti)

Temporal knowledge graph that automatically extracts entities and relationships.

### Setup

```bash
pip install graphiti-core[falkordb]
```

```python
from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver

falkor_driver = FalkorDriver(
    host=os.environ.get('FALKORDB_HOST', 'localhost'),
    port=os.environ.get('FALKORDB_PORT', '6379'),
    username=os.environ.get('FALKORDB_USERNAME', None),
    password=os.environ.get('FALKORDB_PASSWORD', None),
)

graphiti = Graphiti(graph_driver=falkor_driver)
```

### Automatic Episode Ingestion

The `inject_memory` middleware (`@before_model`) uses hybrid injection: static blocks (`persona`, `user_profile`) are placed in the system prompt at build time (rarely change, KV-cache friendly), while dynamic blocks (`preferences`, `working_context`, `learnings`) are injected into the user message before each turn. This ensures the system prompt is fully cacheable across turns. See `references/agent-orchestration.md` for the implementation pattern.

After every conversation turn, the `save_to_graph` middleware (`@after_model`) calls:

```python
await graphiti.add_episode(
    name=f"conversation_turn_{turn_id}",
    episode_body=conversation_content,
    source="message",
    group_id=session_id,
    source_description="agent conversation",
)
```

### Manual Fact Triples

For explicit relationship creation:

```python
from graphiti_core.nodes import EntityNode
from graphiti_core.edges import EntityEdge

source = EntityNode(uuid=src_uuid, name="Lucas", group_id=group)
target = EntityNode(uuid=tgt_uuid, name="FalkorDB", group_id=group)
edge = EntityEdge(
    group_id=group,
    source_node_uuid=src_uuid,
    target_node_uuid=tgt_uuid,
    created_at=datetime.now(),
    name="PREFERS",
    fact="Lucas prefers FalkorDB over Neo4j for graph databases",
)
await graphiti.add_triplet(source, edge, target)
```

### Search Tool

| Tool | Purpose |
|---|---|
| `search_knowledge_graph` | Semantic + graph-based search over entities and facts |

### Graph Namespacing

Use `group_id` to isolate data per user/session/domain:

```python
await graphiti.add_episode(
    ...,
    group_id="user_lucas",  # Namespace per user
)
```
