import os
import pytest
from dotenv import load_dotenv

load_dotenv()


def test_agent_query_llm(agent_no_llm, db_session):
    """Run the agent query if OPENAI_API_KEY is configured; otherwise skip."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not configured; skipping LLM integration test")

    from references.agent_assembly import run_agent

    agent = agent_no_llm
    user_query = "Qual é o role profissional de João? Busque na memória e responda em português."

    try:
        result = run_agent(agent=agent, user_input=user_query, session_id="ci_test", user_id="pytest")
    except Exception as e:
        # If network/SSL/OpenAI connection fails, skip the integration test
        import openai
        if isinstance(e, openai.APIConnectionError) or "CERTIFICATE_VERIFY_FAILED" in str(e):
            pytest.skip(f"LLM call failed due to connection error: {e}")
        raise

    # Expect a response structure with assistant messages
    assert isinstance(result, dict)
    messages = result.get("messages", [])
    assert any(m.get("role") == "assistant" for m in messages)

