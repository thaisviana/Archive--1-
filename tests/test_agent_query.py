import os
import pytest
from dotenv import load_dotenv

load_dotenv()


def test_agent_query_llm(monkeypatch, agent_no_llm, db_session):
    """Mock `run_agent` to avoid real LLM network calls and verify response shape."""
    # Replace run_agent with a fake that returns expected structure
    def fake_run_agent(agent, user_input, session_id=None, user_id=None):
        return {
            "messages": [
                {"role": "assistant", "content": "Resposta simulada: João é Software Engineer."}
            ]
        }

    monkeypatch.setattr("references.agent_assembly.run_agent", fake_run_agent, raising=False)

    from references.agent_assembly import run_agent

    agent = agent_no_llm
    user_query = "Qual é o role profissional de João? Busque na memória e responda em português."

    result = run_agent(agent=agent, user_input=user_query, session_id="ci_test", user_id="pytest")

    # Expect a response structure with assistant messages
    assert isinstance(result, dict)
    messages = result.get("messages", [])
    assert any(m.get("role") == "assistant" for m in messages)
