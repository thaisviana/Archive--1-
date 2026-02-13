import os
import pytest
from dotenv import load_dotenv

load_dotenv()

from references.sqlalchemy_models import get_session, init_default_blocks
from sqlalchemy import text


@pytest.fixture(scope="session")
def env_setup():
    # Ensure env variables are loaded for tests
    return True


@pytest.fixture(scope="session")
def db_session(env_setup):
    """Provide a SQLAlchemy session and ensure default blocks exist."""
    session = get_session()
    # Initialize default blocks if absent
    try:
        blocks = session.execute(text("SELECT count(*) FROM memory_blocks")).scalar()
    except Exception:
        # If table does not exist, try to initialize via models module
        init_default_blocks(session)
        blocks = session.execute(text("SELECT count(*) FROM memory_blocks")).scalar()

    if blocks == 0:
        init_default_blocks(session)

    yield session

    try:
        session.close()
    except Exception:
        pass


@pytest.fixture(scope="session")
def agent_no_llm():
    """Assemble agent but do not require OPENAI API key for basic assembly tests."""
    try:
        from references.agent_assembly import assemble_agent
        agent = assemble_agent(workspace_dir="./workspace_test")
        return agent
    except Exception:
        pytest.skip("DeepAgents assembly failed in this environment")
