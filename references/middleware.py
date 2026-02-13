"""
Custom middleware for the sentient agent using DeepAgents patterns.

DeepAgents 0.4.1 supports custom middleware through tool-based patterns.
This implementation provides memory injection, token management, and memory updates.
"""
from typing import Optional, Any, Callable
import tiktoken
import os
import asyncio
import uuid
import logging

from references.sqlalchemy_models import get_session, MemoryBlock
from references.sqlalchemy_models import BlockHistory

logger = logging.getLogger(__name__)

from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver

# Require OpenAI client to be present
import openai

# Constants
TOKEN_THRESHOLD = 8000
RETHINK_CHAR_RATIO = 0.8
N_TURN_THRESHOLD = 5


def count_tokens(messages: list[dict] | list[Any]) -> int:
    """Count tokens in a message list using tiktoken."""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:
        encoding = tiktoken.encoding_for_model("gpt-4")
    
    total = 0
    for msg in messages:
        content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
        total += len(encoding.encode(str(content)))
    return total


def load_memory_blocks(labels: Optional[list[str]] = None, read_only: Optional[bool] = None) -> list[MemoryBlock]:
    """Load memory blocks from the database."""
    try:
        session = get_session()
        query = session.query(MemoryBlock)
        
        if labels:
            query = query.filter(MemoryBlock.label.in_(labels))
        
        if read_only is not None:
            query = query.filter(MemoryBlock.read_only == read_only)
        
        return query.all()
    except Exception as e:
        logger.warning(f"Could not load memory blocks: {e}")
        return []


def format_as_memory_context(blocks: list[MemoryBlock]) -> str:
    """Format memory blocks as a readable context string."""
    if not blocks:
        return ""
    
    formatted = ["## Agent Memory Context\n"]
    for block in blocks:
        formatted.append(f"### {block.label.replace('_', ' ').title()}")
        formatted.append(block.content)
        formatted.append("")
    
    return "\n".join(formatted)


def _format_static_memory(blocks: list[MemoryBlock]) -> str:
    """Format static blocks (system prompt style)."""
    if not blocks:
        return ""
    formatted = ["## Agent Static Memory\n"]
    for block in blocks:
        formatted.append(f"### {block.label.replace('_', ' ').title()}")
        formatted.append(block.content)
        formatted.append("")
    return "\n".join(formatted)


def _save_block_history(session, block: MemoryBlock, previous_content: str) -> None:
    try:
        hist = BlockHistory(block_id=block.id, content=previous_content)
        session.add(hist)
        session.commit()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to save BlockHistory for {block.label}: {e}")


def _offload_overflow(block_label: str, overflow: str) -> str:
    """Write overflow content to StoreBackend (filesystem) and return the path."""
    try:
        base = os.environ.get("STORE_BACKEND_PATH", "./store_backend")
        os.makedirs(base, exist_ok=True)
        subdir = os.path.join(base, block_label)
        os.makedirs(subdir, exist_ok=True)
        fname = f"overflow_{uuid.uuid4().hex}.txt"
        path = os.path.join(subdir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(overflow)
        return path
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to offload overflow for {block_label}: {e}")
        return ""


def _summarize_text(text: str, target_chars: int = 1000) -> str:
    """Summarize text using OpenAI ChatCompletion (expects `openai` installed and API key set)."""
    prompt = f"Resuma o texto preservando fatos importantes e reduza para ~{target_chars} caracteres:\n\n{text}"
    resp = openai.ChatCompletion.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=min(2048, int(target_chars * 2 / 4)),
        temperature=0.2,
    )
    summary = resp["choices"][0]["message"]["content"].strip()
    return summary


class MemoryInjectionMiddleware:
    """Middleware that injects dynamic memory blocks before LLM calls."""
    
    def __call__(self, agent_state: dict, runtime: Any = None) -> dict:
        """
        Inject dynamic memory blocks into the user message.
        
        This is called as a processing step before model invocation.
        """
        try:
            # Load dynamic memory blocks
            dynamic_blocks = load_memory_blocks(
                labels=["preferences", "working_context", "learnings"]
            )
            # Load static blocks (persona, user_profile) for system prompt injection
            static_blocks = load_memory_blocks(labels=["persona", "user_profile"], read_only=True)
            
            if not dynamic_blocks:
                return agent_state
            
            # Format memory as context
            memory_context = format_as_memory_context(dynamic_blocks)

            static_context = _format_static_memory(static_blocks)
            
            # Find the latest user message and prepend memory context
            messages = agent_state.get("messages", [])
            if not messages:
                return agent_state
            
            # Find last user message
            for i in range(len(messages) - 1, -1, -1):
                msg = messages[i]
                if isinstance(msg, dict) and msg.get("role") == "user":
                    # Prepend memory context
                    original_content = msg.get("content", "")
                    msg["content"] = f"{memory_context}\n\nUser Query:\n{original_content}"
                    agent_state["messages"] = messages
                    # Inject static blocks into the system prompt (if not already present)
                    if static_context:
                        injected = False
                        for j, m in enumerate(messages):
                            if isinstance(m, dict) and m.get("role") == "system":
                                if "## Agent Static Memory" not in m.get("content", ""):
                                    m["content"] = f"{static_context}\n\n" + m.get("content", "")
                                injected = True
                                break
                        if not injected:
                            # No system message found; prepend one
                            messages.insert(0, {"role": "system", "content": static_context})
                        agent_state["messages"] = messages
                    return agent_state
            
            return agent_state
            
        except Exception as e:
            logger.exception("Error in MemoryInjectionMiddleware: %s", e)
            return agent_state


class TokenManagementMiddleware:
    """Middleware that monitors token count and marks state for memory rethinking."""
    
    def __call__(self, agent_state: dict, runtime: Any = None) -> dict:
        """
        Check token count. If exceeds threshold, mark for summarization/compression.
        """
        try:
            messages = agent_state.get("messages", [])
            token_count = count_tokens(messages)
            
            # Store token count in state for monitoring
            agent_state["last_token_count"] = token_count
            
            # If over threshold, mark for rethinking
            if token_count > TOKEN_THRESHOLD:
                agent_state["needs_rethink"] = True
                logger.warning("⚠️  Token count (%d) exceeds threshold (%d)", token_count, TOKEN_THRESHOLD)
            
            return agent_state
            
        except Exception as e:
            logger.exception("Error in TokenManagementMiddleware: %s", e)
            return agent_state


class MemoryRethinkMiddleware:
    """Middleware that updates memory blocks after LLM responses."""
    
    def __call__(self, agent_state: dict, runtime: Any = None) -> dict:
        """
        Review and update memory blocks if rethinking was triggered.
        """
        try:
            # Check if rethinking was triggered
            if not agent_state.get("needs_rethink"):
                return agent_state
            
            # Load editable memory blocks
            session = get_session()
            editable_blocks = session.query(MemoryBlock).filter(MemoryBlock.read_only == False).all()

            # Check each block for size constraints and handle compression/offload
            for block in editable_blocks:
                try:
                    current_length = len(block.content or "")
                    # Skip if block is not approaching its limit
                    if current_length < block.char_limit * RETHINK_CHAR_RATIO:
                        continue

                    compression_ratio = current_length / block.char_limit
                    logging.getLogger(__name__).info(
                        f"Memory block '{block.label}' at {compression_ratio:.1%} of limit ({current_length}/{block.char_limit})"
                    )

                    # Save previous content to history
                    previous = block.content
                    _save_block_history(session, block, previous)

                    # Attempt to summarize/compress
                    target_chars = int(block.char_limit * 0.6)
                    compressed = _summarize_text(previous, target_chars=target_chars)

                    # If still too large, offload overflow
                    if len(compressed) > block.char_limit:
                        overflow = compressed[block.char_limit :]
                        path = _offload_overflow(block.label, overflow)
                        compressed = compressed[: block.char_limit]
                        logging.getLogger(__name__).info(f"Offloaded overflow for {block.label} to {path}")

                    # Update block content and commit
                    block.content = compressed
                    session.add(block)
                    session.commit()
                except Exception as inner_e:
                    logging.getLogger(__name__).warning(f"Error processing block {block.label}: {inner_e}")
            
            # Clear the rethinking flag
            agent_state["needs_rethink"] = False
            return agent_state
            
        except Exception as e:
            logger.exception("Error in MemoryRethinkMiddleware: %s", e)
            return agent_state


# Middleware instances that can be used directly
inject_memory = MemoryInjectionMiddleware()
manage_tokens = TokenManagementMiddleware()
rethink_memory = MemoryRethinkMiddleware()

# For backwards compatibility
summarize_if_needed = manage_tokens


def _build_conversation_content(messages: list[dict]) -> str:
    parts = []
    for m in messages:
        if isinstance(m, dict):
            role = m.get("role", "unknown")
            content = m.get("content", "")
            parts.append(f"[{role}] {content}")
        else:
            # fallback for non-dict message objects
            try:
                content = getattr(m, "content", str(m))
            except Exception:
                content = str(m)
            parts.append(content)
    return "\n\n".join(parts)


def save_to_graph(state: dict, runtime: Any = None) -> dict:
    """Persist the conversation turn to Graphiti/FalkorDB.

    Requires `graphiti-core` and a reachable FalkorDB instance.
    """
    # Prepare connection
    host = os.environ.get("FALKORDB_HOST", "localhost")
    port = int(os.environ.get("FALKORDB_PORT", 6379))
    username = os.environ.get("FALKORDB_USERNAME", None)
    password = os.environ.get("FALKORDB_PASSWORD", None)

    driver = FalkorDriver(host=host, port=port, username=username, password=password)
    graphiti = Graphiti(graph_driver=driver)

    # Build episode payload
    messages = state.get("messages", [])
    conversation_content = _build_conversation_content(messages)
    turn_id = state.get("turn_id") or str(uuid.uuid4())
    session_id = state.get("session_id") or state.get("session") or "default_session"

    async def _add_episode():
        await graphiti.add_episode(
            name=f"conversation_turn_{turn_id}",
            episode_body=conversation_content,
            source="message",
            group_id=session_id,
            source_description="agent conversation",
        )

    # If an event loop is running, schedule the coroutine, otherwise run it
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_add_episode())
        else:
            loop.run_until_complete(_add_episode())
    except RuntimeError:
        # No running loop; use asyncio.run
        asyncio.run(_add_episode())

    return state

