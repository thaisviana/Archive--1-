import pytest


def test_deepagents_assemble(agent_no_llm):
    """Assemble agent and ensure basic attributes exist."""
    agent = agent_no_llm
    assert agent is not None
    assert hasattr(agent, "invoke") or hasattr(agent, "run")

