#!/usr/bin/env python
"""
Alternative test script to query João's role from memory without deepagents.
This demonstrates how the agent would access memory to answer questions.
"""
import os
from dotenv import load_dotenv
from references.sqlalchemy_models import get_session, MemoryBlock
from references.memory_tools import view_memory_blocks

# Load environment variables from .env
load_dotenv()

def answer_question_from_memory(question: str) -> str:
    """
    Simulate agent behavior: search memory blocks to answer a question.
    """
    session = get_session()
    
    print("=" * 60)
    print("AGENT MEMORY QUERY SIMULATION")
    print("=" * 60)
    print()
    
    # Display the question
    print(f"User Question: {question}")
    print()
    
    
    # Retrieve all memory blocks
    blocks = session.query(MemoryBlock).all()
    
    # Search for content related to "role" or "profissional"
    relevant_blocks = []
    for block in blocks:
        if "role" in block.label.lower() or "profissional" in block.content.lower() or "role" in block.content.lower():
            relevant_blocks.append(block)
    
    if not relevant_blocks:
        # If no direct match, show user_profile as it likely has role info
        user_profile = session.query(MemoryBlock).filter_by(label="user_profile").first()
        if user_profile:
            relevant_blocks.append(user_profile)
    
    # Display searched blocks
    for block in relevant_blocks:
        print(f"Memory Block: {block.label}")
        print(f"   Content:\n{block.content}")
    
    
    # Extract João's role from memory
    user_profile_block = session.query(MemoryBlock).filter_by(label="user_profile").first()
    if user_profile_block and "João" in user_profile_block.content:
        print(f"✓ Found João in user_profile block")
        print(f"✓ Extracted role information from memory")
        
        # Parse the role from content
        content_lines = user_profile_block.content.split('\n')
        for line in content_lines:
            if "role" in line.lower():
                return(f"✓ Role field: {line}")
        
        return "User information found but could not extract specific role."
    else:
        return "Informação sobre João não encontrada na memória."

def main():
    """Run the memory query simulation."""
    # Question from the user
    question = "Qual é o role profissional de João? Busque na memória do usuário."
    
    # Get answer from memory
    answer = answer_question_from_memory(question)
    
    print()
    print("=" * 60)
    print("Agent Response:")
    print("=" * 60)
    print(answer)
    print()
    
    # Show memory statistics
    session = get_session()
    blocks = session.query(MemoryBlock).all()
    print("-" * 60)
    print(f"Total memory blocks accessed: {len(blocks)}")
    for block in blocks:
        if block.history:
            print(f"   • {block.label}: {len(block.history)} version(s)")

if __name__ == "__main__":
    main()
