#!/usr/bin/env python
"""Pytest version of memory ingestion test."""
import pytest

from references.sqlalchemy_models import MemoryBlock
from references.memory_tools import (
    create_memory_block,
    replace_memory_content,
    view_memory_blocks,
)


def test_memory_ingestion(db_session):
    """Ensure default blocks exist and sample data can be ingested."""
    session = db_session

    # Basic expectation: default blocks present
    blocks = session.query(MemoryBlock).all()
    assert len(blocks) >= 6

    # Replace user_profile content
    res = replace_memory_content.func(
        label="user_profile",
        old_str="No user information yet.",
        new_str="Name: João Silva\nRole: Software Engineer\nCompany: Tech Startup XYZ",
    )
    assert res is not None

    # Create custom block
    created = create_memory_block.func(
        label="py_test_project_timeline",
        content="Project Start Date: 2026-02-01\nMilestone: TEST",
    )
    assert created is not None

    # View memory blocks via tool
    view = view_memory_blocks.func()
    assert isinstance(view, str)

