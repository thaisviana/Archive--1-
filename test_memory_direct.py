
import pytest

from references.sqlalchemy_models import MemoryBlock


def test_memory_direct_query(db_session):
    """Ensure memory blocks are present and user_profile contains role."""
    session = db_session

    blocks = session.query(MemoryBlock).all()
    assert len(blocks) >= 6

    user_profile = next((b for b in blocks if b.label == "user_profile"), None)
    assert user_profile is not None

    # Role should appear in content (after ingestion test)
    assert "role" in user_profile.content.lower() or "software engineer" in user_profile.content.lower()

