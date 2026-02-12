#!/usr/bin/env python
"""
Test script to demonstrate memory ingestion for the agent memory system.
"""
import os
from dotenv import load_dotenv
from references.sqlalchemy_models import init_default_blocks, get_session, MemoryBlock
from references.memory_tools import (
    create_memory_block,
    replace_memory_content,
    view_memory_blocks,
)

# Load environment variables from .env
load_dotenv()

def main():
    """Initialize memory blocks and ingest test data."""
    session = get_session()
    
    print("=" * 60)
    print("AGENT MEMORY INGESTION TEST")
    print("=" * 60)
    print()
    
    # Step 1: Initialize default blocks (persona, user_profile, preferences, etc.)
    print("📝 Step 1: Initializing default memory blocks...")
    init_default_blocks(session)
    print("✓ Default blocks initialized\n")
    
    # Step 2: View all memory blocks
    print("📖 Step 2: Viewing all memory blocks...")
    result = view_memory_blocks.func()  # Using the tool function directly
    print(result)
    print()
    
    # Step 3: Ingest sample user data
    print("💾 Step 3: Ingesting sample user data...")
    
    # Update user_profile with sample data
    update_user = replace_memory_content.func(
        label="user_profile",
        old_str="No user information yet.",
        new_str="Name: João Silva\nRole: Software Engineer\nCompany: Tech Startup XYZ\nLanguage: Portuguese (PT-BR)\nPrefers: Email over chat for long-form discussions"
    )
    print(f"→ {update_user}\n")
    
    # Update preferences with sample data
    update_prefs = replace_memory_content.func(
        label="preferences",
        old_str="No preferences recorded yet.",
        new_str="Language: Portuguese (PT-BR)\nTone: Professional but friendly\nFormatting: Use bullet points for lists, code blocks for examples\nTopics: AI, Python, Cloud Architecture, Team Management"
    )
    print(f"→ {update_prefs}\n")
    
    # Update working_context with current project
    update_context = replace_memory_content.func(
        label="working_context",
        old_str="No active project context.",
        new_str="Current Project: Agent Memory System (LLM Agent with persistent memory)\nObjective: Build a flexible memory management system with version control\nPhase: Database setup and memory block initialization\nNext Step: Implement memory retrieval and reasoning pipeline"
    )
    print(f"→ {update_context}\n")
    
    # Create a custom memory block for project-specific data
    print("💾 Step 4: Creating custom memory block...")
    custom_block = create_memory_block.func(
        label="project_timeline",
        content="Project Start Date: 2026-02-01\nMilestone 1: Memory system foundation - COMPLETED\nMilestone 2: RAG pipeline integration - IN PROGRESS\nMilestone 3: Deployment and monitoring - TODO"
    )
    print(f"→ {custom_block}\n")
    
    # Step 5: View all blocks again to see ingested data
    print("=" * 60)
    print("📖 Step 5: Final memory state (all blocks with ingested data):")
    print("=" * 60)
    result = view_memory_blocks.func()
    print(result)
    print()
    
    # Step 6: Show database statistics
    print("=" * 60)
    print("📊 Database Statistics:")
    print("=" * 60)
    block_count = session.query(MemoryBlock).count()
    print(f"Total memory blocks: {block_count}")
    for block in session.query(MemoryBlock).all():
        char_count = len(block.content)
        history_count = len(block.history)
        print(f"  • {block.label}: {char_count} chars, {history_count} history entries")

if __name__ == "__main__":
    main()
