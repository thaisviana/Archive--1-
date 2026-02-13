import asyncio

import pytest

from references import middleware


class FakeGraphiti:
    def __init__(self, graph_driver=None):
        self.driver = graph_driver
        self.calls = []

    async def add_episode(self, **kwargs):
        # record the call arguments
        self.calls.append(kwargs)


class FakeDriver:
    def __init__(self, host=None, port=None, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password


def test_save_to_graph_with_connection_error(monkeypatch):
    """Test that save_to_graph raises when FalkorDriver connection fails."""
    def failing_driver(*args, **kwargs):
        raise ConnectionError("Cannot connect to Redis/FalkorDB")
    
    monkeypatch.setattr(middleware, "FalkorDriver", failing_driver)
    
    state = {"messages": [{"role": "user", "content": "test message"}], "turn_id": "t1", "session_id": "s1"}
    with pytest.raises(ConnectionError):
        middleware.save_to_graph(state.copy())


def test_save_to_graph_calls_graphiti(monkeypatch):
    """Test that save_to_graph calls Graphiti.add_episode with mocked driver."""
    fake_graphiti = FakeGraphiti()

    # Monkeypatch constructors used inside middleware.save_to_graph
    monkeypatch.setattr(middleware, "FalkorDriver", FakeDriver)
    monkeypatch.setattr(middleware, "Graphiti", lambda graph_driver=None: fake_graphiti)

    state = {
        "messages": [
            {"role": "system", "content": "System init"},
            {"role": "user", "content": "Qual é a minha preferência?"},
        ],
        "turn_id": "test_turn_01",
        "session_id": "user_42",
    }

    returned = middleware.save_to_graph(state.copy())

    # save_to_graph should return the original state
    assert returned == state

    # The fake_graphiti.add_episode should have been called once
    # Since save_to_graph runs the coroutine synchronously when no running loop, the call should be present
    assert len(fake_graphiti.calls) == 1
    call = fake_graphiti.calls[0]
    assert call["name"].startswith("conversation_turn_")
    assert "episode_body" in call
    assert "Qual é a minha preferência?" in call["episode_body"]
    assert call["group_id"] == "user_42"


if __name__ == "__main__":
    pytest.main(["-q", "-k", "save_to_graph"])