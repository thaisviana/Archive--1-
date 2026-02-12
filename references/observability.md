# Observability with LangFuse

## Contents
- Setup — installation, environment variables, initialization
- Integration Points — Deep Agents, LlamaIndex, @observe decorator, full turn wrapping
- Evaluation — scoring, LLM-as-Judge
- Flushing

## Setup

### Installation

```bash
pip install langfuse openinference-instrumentation-llama-index
```

### Environment Variables

```bash
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com  # Or self-hosted URL
```

### Initialization

```python
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler

Langfuse(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
)

langfuse = get_client()
langfuse_handler = CallbackHandler()
```

## Integration Points

### 1. Deep Agents / LangChain (CallbackHandler)

Pass the handler to every agent invocation:

```python
result = agent.invoke(
    {"messages": [...]},
    config={
        "callbacks": [langfuse_handler],
        "metadata": {
            "langfuse_user_id": user_id,
            "langfuse_session_id": session_id,
            "langfuse_tags": ["sentient-agent", "v1"],
        },
    },
)
```

### 2. LlamaIndex RAG Pipeline (OpenInference Instrumentor)

Initialize once at startup:

```python
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

LlamaIndexInstrumentor().instrument()
```

All LlamaIndex operations (ingestion, retrieval, LLM calls) are automatically traced.

### 3. Custom Operations (@observe decorator)

For memory operations, Graphiti calls, and custom logic:

```python
from langfuse import observe, get_client, propagate_attributes

@observe()
def process_memory_update(block_label: str, content: str):
    langfuse = get_client()

    with propagate_attributes(
        user_id=current_user_id,
        session_id=current_session_id,
        tags=["memory-update"],
    ):
        result = update_memory_block(block_label, content)

        langfuse.update_current_trace(
            input={"block": block_label, "content": content},
            output={"success": True},
        )

    return result
```

### 4. Wrapping Full Agent Turn

```python
@observe(name="agent-turn")
def handle_user_message(user_id: str, session_id: str, message: str):
    langfuse = get_client()

    with propagate_attributes(user_id=user_id, session_id=session_id):
        langfuse_handler = CallbackHandler()

        result = agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config={
                "configurable": {"thread_id": session_id},
                "callbacks": [langfuse_handler],
            },
        )

        langfuse.update_current_trace(
            input={"message": message},
            output={"response": result["messages"][-1]["content"]},
        )

    return result
```

## Evaluation

### Score Agent Responses

```python
langfuse.create_score(
    trace_id=langfuse_handler.last_trace_id,
    name="user-feedback",
    value=1,  # thumbs up
    data_type="NUMERIC",
    comment="Helpful response",
)
```

### LLM-as-Judge

Use LangFuse evaluators to automatically score responses:
- Relevance (does the answer address the question?)
- Faithfulness (is the answer grounded in retrieved context?)
- Helpfulness (was the response useful?)

## Flushing

For short-lived scripts:

```python
langfuse = get_client()
langfuse.flush()  # Ensure all events are sent
langfuse.shutdown()  # Clean shutdown
```
