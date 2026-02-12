"""
Custom middleware for the sentient agent using DeepAgents patterns.

DeepAgents 0.4.1 supports custom middleware through tool-based patterns.
This implementation provides memory injection, token management, and memory updates.
"""
from typing import Optional, Any, Callable
import tiktoken

from references.sqlalchemy_models import get_session, MemoryBlock


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
        print(f"Warning: Could not load memory blocks: {e}")
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
            
            if not dynamic_blocks:
                return agent_state
            
            # Format memory as context
            memory_context = format_as_memory_context(dynamic_blocks)
            
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
                    return agent_state
            
            return agent_state
            
        except Exception as e:
            print(f"Error in MemoryInjectionMiddleware: {e}")
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
                print(f"⚠️  Token count ({token_count}) exceeds threshold ({TOKEN_THRESHOLD})")
            
            return agent_state
            
        except Exception as e:
            print(f"Error in TokenManagementMiddleware: {e}")
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
            editable_blocks = load_memory_blocks(read_only=False)
            
            # Check each block for size constraints
            for block in editable_blocks:
                current_length = len(block.content)
                
                # Skip if block is not approaching its limit
                if current_length < block.char_limit * RETHINK_CHAR_RATIO:
                    continue
                
                # Log that block needs compression
                compression_ratio = current_length / block.char_limit
                print(f"⚠️  Memory block '{block.label}' is at {compression_ratio:.1%} of limit")
                
                # In production, here you would:
                # - Summarize the block content using LLM
                # - Offload overflow to storage backend
                # - Update the block with compressed content
            
            # Clear the rethinking flag
            agent_state["needs_rethink"] = False
            return agent_state
            
        except Exception as e:
            print(f"Error in MemoryRethinkMiddleware: {e}")
            return agent_state


# Middleware instances that can be used directly
inject_memory = MemoryInjectionMiddleware()
manage_tokens = TokenManagementMiddleware()
rethink_memory = MemoryRethinkMiddleware()

# For backwards compatibility
summarize_if_needed = manage_tokens
save_to_graph = lambda state, runtime: state  # Stub for knowledge graph integration

