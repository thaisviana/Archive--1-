#!/usr/bin/env python
"""
Test that deepagents agent can be assembled with Python 3.12
(Note: Requires OPENAI_API_KEY for actual LLM calls)
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("DEEPAGENTS ASSEMBLY TEST")
print("=" * 60)
print()

# Test 1: Import deepagents
print("✓ Testing deepagents imports...")
try:
    from references.agent_assembly import assemble_agent, run_agent
    print("✓ Successfully imported agent_assembly module")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

# Test 2: Check if OPENAI_API_KEY is set
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("⚠️  OPENAI_API_KEY not set — agent will need it for LLM calls")
else:
    print("✓ OPENAI_API_KEY is configured")

# Test 3: Try to assemble the agent
print("\n✓ Attempting to assemble agent with full middleware...")
try:
    agent = assemble_agent(workspace_dir="./workspace")
    print("✓ Agent successfully assembled!")
    print(f"  Agent type: {type(agent)}")
    print(f"  Agent has invoke method: {hasattr(agent, 'invoke')}")
except Exception as e:
    print(f"❌ Error assembling agent: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("=" * 60)
print("✓ DEEPAGENTS IS READY!")
print("=" * 60)
print()
print("Next steps:")
print("1. Set OPENAI_API_KEY in .env to use with GPT models")
print("2. Run: python test_agent_query.py")
print("   or with env: set -a && source .env && set +a && python test_agent_query.py")
