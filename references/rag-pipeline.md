# RAG Pipeline

## Strategy: Contextual Retrieval

Standard RAG chunks lose context. Contextual Retrieval prepends each chunk with document-level context before embedding, dramatically improving retrieval accuracy.

### How It Works

1. **Load** documents via LlamaIndex connectors (`SimpleDirectoryReader`)
2. **Chunk** using SentenceSplitter (512 tokens, 50 overlap)
3. **Generate context** for each chunk using LLM (Contextual Retrieval)
4. **Prepend** generated context to each chunk
5. **Embed** contextualized chunks (`OpenAIEmbedding`)
6. **Store** in LlamaIndex `PGVectorStore` (`kb_docs` table, `hybrid_search=True`)

### Ingestion Script

See `scripts/ingest_documents.py` for the implementation stub.

```python
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore

# Vector store with hybrid search (see references/memory-system.md for full config)
vector_store = PGVectorStore.from_params(
    database="agent_memory",
    host="localhost",
    password="password",
    port=5432,
    user="user",
    table_name="kb_docs",
    embed_dim=1536,
    hybrid_search=True,
    text_search_config="portuguese",
)

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=50),
        OpenAIEmbedding(model="text-embedding-3-small"),
    ],
    vector_store=vector_store,
)

documents = SimpleDirectoryReader(input_dir="./docs").load_data()
nodes = pipeline.run(documents=documents, num_workers=4)
```

### Context Generation Prompt

For each chunk, a lightweight LLM call generates a brief context. This step runs **before** the `IngestionPipeline` — iterate over chunks, call the LLM, and prepend the context to each chunk's text.

```
<document>
{WHOLE_DOCUMENT}
</document>

Here is the chunk we want to situate within the whole document:
<chunk>
{CHUNK_CONTENT}
</chunk>

Please give a short succinct context to situate this chunk within
the overall document for the purposes of improving search retrieval.
Answer only with the succinct context and nothing else.
```

LlamaIndex has a Contextual Retrieval cookbook example — see `llama_index/docs/examples/cookbooks/contextual_retrieval.ipynb` in the LlamaIndex repository for a complete reference implementation.

### Retrieval Tool

Uses LlamaIndex's `VectorStoreIndex` with hybrid search mode. Returns raw chunks (no LLM synthesis) to avoid wasting tokens.

```python
from langchain_core.tools import tool
from llama_index.core import VectorStoreIndex

# Build index from existing vector store (no re-ingestion needed)
# index = VectorStoreIndex.from_vector_store(vector_store=kb_vector_store)
# retriever = index.as_retriever(vector_store_query_mode="hybrid", similarity_top_k=5, sparse_top_k=5)

@tool
def search_knowledge_base(query: str, top_k: int = 5) -> str:
    """Search the knowledge base for documents relevant to the query.

    Uses hybrid search (vector similarity + keyword matching) for best results.

    Args:
        query: Natural language search query
        top_k: Number of results to return (default: 5)

    Returns:
        Formatted string with relevant document chunks and their sources
    """
    # nodes = retriever.retrieve(query)
    # return "\n---\n".join(
    #     f"[{n.metadata.get('source', 'unknown')}] (score: {n.score:.3f})\n{n.text}"
    #     for n in nodes[:top_k]
    # )
    raise NotImplementedError("Configure vector store first — see references/memory-system.md")
```

See `references/memory-system.md` for `PGVectorStore` setup, Portuguese language configuration, and `QueryFusionRetriever` for advanced RRF fusion.

### Supported Document Types

LlamaIndex's SimpleDirectoryReader handles:
- PDF, DOCX, PPTX, XLSX
- Markdown, TXT, CSV
- HTML, JSON, EPUB
- Images (with multi-modal models)

### Usage

```bash
python scripts/ingest_documents.py --path /path/to/docs
python scripts/ingest_documents.py --path /path/to/single-file.pdf
```
