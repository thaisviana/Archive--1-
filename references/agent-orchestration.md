# Agent Orchestration

## Contents
- Deep Agents Setup — installation, assembly, running
- Custom Middleware — inject_memory, summarize_if_needed, save_to_graph, rethink_memory (@before_model / @after_model)
- Sub-Agent Configuration

## Deep Agents Setup

### Installation

```bash
pip install deepagents
```

### Assembly

See `agent_assembly.py` for the full implementation.

```python
from deepagents import create_deep_agent
from deepagents.middleware import (
    TodoListMiddleware,
    SubAgentMiddleware,
    SkillsMiddleware,
    FilesystemMiddleware,
    CompactionMiddleware,
)
from langgraph.checkpoint.memory import MemorySaver

agent = create_deep_agent(
    model="openai:gpt-5-mini-2025-08-07",
    system_prompt=SYSTEM_PROMPT,
    tools=[
        insert_memory_block,
        replace_memory_content,
        rethink_memory_block,
        finish_memory_edits,
        create_memory_block,
        delete_memory_block,
        rename_memory_block,
        view_memory_blocks,
        search_knowledge_base,
        search_conversation_history,
        search_knowledge_graph,
    ],
    middleware=[
        TodoListMiddleware(),
        SubAgentMiddleware(
            default_model="openai:gpt-5-mini-2025-08-07",
            general_purpose_agent=True,
        ),
        SkillsMiddleware(),
        FilesystemMiddleware(),
        CompactionMiddleware(),
        inject_memory,           # @before_model
        summarize_if_needed,     # @before_model
        save_to_graph,           # @after_model
        rethink_memory,          # @after_model
    ],
    memory=["./AGENTS.md"],
    backend=FilesystemBackend(root_dir="./workspace"),
    checkpointer=MemorySaver(),
)
```

### Running the Agent

```python
config = {"configurable": {"thread_id": session_id}}

result = agent.invoke(
    {"messages": [{"role": "user", "content": user_input}]},
    config={
        **config,
        "callbacks": [langfuse_handler],
    },
)
```

## Custom Middleware

Deep Agents middleware supports lifecycle hooks via the `@before_model` and `@after_model` decorators from LangChain. These run before/after every LLM call and can modify agent state.

**Reference docs:**
- Deep Agents customization: https://docs.langchain.com/oss/python/deepagents/customization
- Deep Agents middleware: https://docs.langchain.com/oss/python/deepagents/middleware
- LangChain short-term memory (`@before_model` / `@after_model`): https://docs.langchain.com/oss/python/langchain/short-term-memory#before-model
- `AgentMiddleware` class (tool-based middleware): `from langchain.agents.middleware import AgentMiddleware`

**Two middleware patterns available:**

| Pattern | Use Case | Interface |
|---|---|---|
| `@before_model` / `@after_model` decorators | Lifecycle hooks (intercept before/after LLM calls) | `(state: AgentState, runtime: Runtime) -> dict \| None` |
| `class MyMiddleware(AgentMiddleware)` with `tools` attribute | Adding tools to the agent | `tools = [tool_a, tool_b]` |

### inject_memory (before_model)

Injects memory blocks into the user message before each LLM call. Static blocks (`persona`, `user_profile`) live in the system prompt at build time; dynamic blocks (`preferences`, `working_context`, `learnings`) are injected here.

```python
from langchain.agents import before_model
from langchain.agents.types import AgentState, Runtime

@before_model
def inject_memory(state: AgentState, runtime: Runtime) -> dict | None:
    dynamic_blocks = load_memory_blocks(labels=["preferences", "working_context", "learnings"])
    formatted = format_as_memory_context(dynamic_blocks)
    messages = state["messages"]
    # Prepend memory context to the latest user message
    last_user_msg = next(m for m in reversed(messages) if m["role"] == "user")
    last_user_msg["content"] = f"{formatted}\n\n{last_user_msg['content']}"
    return {"messages": messages}
```

### save_to_graph (after_model)

Writes each conversation turn to the knowledge graph after the LLM responds.

```python
from langchain.agents import after_model

@after_model
async def save_to_graph(state: AgentState, runtime: Runtime) -> dict | None:
    # Write episode to Graphiti knowledge graph (async — Graphiti client is async)
    # await graphiti.add_episode(
    #     name=f"turn_{turn_id}",
    #     episode_body=state["messages"][-1]["content"],
    #     source="message",
    #     group_id=thread_id,
    # )
    return None
```

### summarize_if_needed (before_model)

Checks token count before each LLM call. If the conversation exceeds the threshold, summarizes and replaces older messages.

```python
@before_model
def summarize_if_needed(state: AgentState, runtime: Runtime) -> dict | None:
    TOKEN_THRESHOLD = 8000
    messages = state["messages"]
    if count_tokens(messages) <= TOKEN_THRESHOLD:
        return None
    # Summarize older messages, keep system prompt + last 4 messages
    # summary = summarize_messages(messages[1:-4])
    # return {
    #     "messages": [messages[0], summary_msg, *messages[-4:]],
    #     "just_summarized": True,
    # }
    return None
```

### rethink_memory (after_model)

Reviews memory blocks for updates and enforces size limits. Triggers on three conditions.

```python
RETHINK_CHAR_RATIO = 0.8  # Trigger compression at 80% of char_limit

@after_model
def rethink_memory(state: AgentState, runtime: Runtime) -> dict | None:
    # Run if: (a) summarization just happened, OR
    #          (b) dynamic memory tokens > 70% of context budget, OR
    #          (c) N turns since last rethink
    should_rethink = (
        state.get("just_summarized")
        or dynamic_tokens_exceed_threshold(state, ratio=0.7)
        or turns_since_last_rethink(state) >= N_TURN_THRESHOLD
    )
    if not should_rethink:
        return None

    editable_blocks = load_memory_blocks(read_only=False)
    for block in editable_blocks:
        # Step 1: Check if block is approaching its char_limit
        if len(block.content) < block.char_limit * RETHINK_CHAR_RATIO:
            continue

        # Step 2: Compress — rewrite the block to be more concise
        # compressed = llm_compress(block.content, target_chars=block.char_limit * 0.6)
        # rethink_memory_block(label=block.label, new_content=compressed)

        # Step 3: If still over limit after compression, offload overflow
        # if len(compressed) > block.char_limit:
        #     overflow = compressed[block.char_limit:]
        #     offload_to_store(runtime, path=f"/memory/overflow/{block.label}", content=overflow)
        #     rethink_memory_block(label=block.label, new_content=compressed[:block.char_limit])
        pass

    # Also compare recent conversation with current blocks
    # and update blocks that contain outdated information
    # trigger_memory_rethink(summary=state["latest_summary"], blocks=editable_blocks)
    return None
```

**Offload mechanism:** When a block exceeds its `char_limit` even after compression, the overflow is written to the Deep Agents `StoreBackend` at `/memory/overflow/{label}`. This content remains searchable via Layer 2 (`search_conversation_history`) but is no longer injected into every turn. See `references/project-setup.md` Step 4 for configuration.

### Assembly with middleware

```python
agent = create_deep_agent(
    model=DEFAULT_MODEL,
    tools=[...],
    middleware=[
        TodoListMiddleware(),
        SubAgentMiddleware(default_model=DEFAULT_MODEL, general_purpose_agent=True),
        SkillsMiddleware(),
        FilesystemMiddleware(),
        CompactionMiddleware(),
        inject_memory,           # @before_model: inject dynamic memory blocks
        summarize_if_needed,     # @before_model: compress if over token threshold
        save_to_graph,           # @after_model: write to Graphiti
        rethink_memory,          # @after_model: update memory blocks post-summarization
    ],
    checkpointer=MemorySaver(),
)
```

## Sub-Agent Configuration

```python
research_subagent = {
    "name": "research-agent",
    "description": "Deep research on complex topics with web search",
    "system_prompt": "You are an expert researcher. Search thoroughly and provide comprehensive summaries.",
    "tools": [search_knowledge_base, search_knowledge_graph],
    "model": "openai:gpt-5-mini-2025-08-07",
}
```
