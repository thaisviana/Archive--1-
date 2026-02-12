#!/usr/bin/env python
"""
Test script to run the agent and query about João's role from memory.
Uses the actual DeepAgents agent with memory tools and LLM.
"""
import os
from dotenv import load_dotenv
from references.agent_assembly import assemble_agent, run_agent

# Load environment variables from .env
load_dotenv()

def main():
    """Run agent with memory query."""
    print("=" * 60)
    print("AGENT MEMORY QUERY WITH LLM")
    print("=" * 60)
    print()
    
    # Assemble the agent with full memory tools
    print("🤖 Assembling agent with memory tools...")
    agent = assemble_agent(workspace_dir="./workspace")
    print("✓ Agent assembled\n")
    
    # Run agent with a question about João's role
    user_query = "Qual é o role profissional de João? Busque na memória e responda em português."
    print(f"👤 User query: {user_query}")
    print("-" * 60)
    
    try:
        result = run_agent(
            agent=agent,
            user_input=user_query,
            session_id="test_session_001",
            user_id="test_user"
        )
        
        print("\n🤖 Agent Response:")
        print("-" * 60)
        
        # Extract and display the response
        if "messages" in result:
            for msg in result["messages"]:
                if msg.get("role") == "assistant":
                    content = msg.get("content", "")
                    print(content)
        else:
            print(result)
            
        print()
        print("=" * 60)
        print("✓ Agent query completed successfully!")
        print("=" * 60)
            
    except Exception as e:
        print(f"❌ Error running agent: {e}")
        print("\nTroubleshooting:")
        print("• Ensure Postgres container is running: docker ps | grep postgres")
        print("• Ensure OPENAI_API_KEY is set in .env")
        print("• Ensure memory blocks are initialized")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
