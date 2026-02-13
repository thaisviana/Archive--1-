import pytest

from references.middleware import (
    MemoryInjectionMiddleware,
    TokenManagementMiddleware,
    MemoryRethinkMiddleware,
    load_memory_blocks,
    format_as_memory_context,
)


def test_middleware_load_and_format(db_session):
    blocks = load_memory_blocks()
    assert isinstance(blocks, list)
    assert len(blocks) >= 6

    context = format_as_memory_context(blocks[:3])
    assert isinstance(context, str)


def test_memory_injection_middleware(db_session):
    injector = MemoryInjectionMiddleware()
    test_state = {
        "messages": [
            {"role": "system", "content": "You are a helpful agent."},
            {"role": "user", "content": "What do I prefer in my interactions?"},
        ]
    }
    original_user = test_state["messages"][-1]["content"]
    updated = injector(test_state)
    assert updated["messages"][-1]["content"] != original_user


def test_token_management_and_rethink():
    manager = TokenManagementMiddleware()
    state = {"messages": [{"role": "user", "content": "Hello"}]}
    updated = manager(state)
    assert isinstance(updated.get("last_token_count", 0), int)

    rethink = MemoryRethinkMiddleware()
    result = rethink({"needs_rethink": True})
    assert not result.get("needs_rethink", False)

