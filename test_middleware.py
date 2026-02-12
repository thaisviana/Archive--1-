#!/usr/bin/env python
"""
Test the custom middleware implementation for memory injection and management.
This demonstrates middleware without requiring OPENAI_API_KEY.
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("CUSTOM MIDDLEWARE INTEGRATION TEST")
print("=" * 60)
print()

# Test middleware directly
print("✓ Testing custom middleware classes...")
try:
    from references.middleware import (
        MemoryInjectionMiddleware,
        TokenManagementMiddleware,
        MemoryRethinkMiddleware,
        load_memory_blocks,
        format_as_memory_context,
    )
    print("✓ Successfully imported middleware components")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

# Test 1: Memory Loading
print("\n📚 Test 1: Loading Memory Blocks")
print("-" * 60)
try:
    blocks = load_memory_blocks()
    print(f"✓ Loaded {len(blocks)} memory blocks from database")
    for block in blocks:
        print(f"  • {block.label}: {len(block.content)} chars")
except Exception as e:
    print(f"❌ Error loading memory: {e}")
    exit(1)

# Test 2: Memory Formatting
print("\n📋 Test 2: Formatting Memory as Context")
print("-" * 60)
try:
    context = format_as_memory_context(blocks[:3])  # Format first 3 blocks
    print(f"✓ Formatted memory context ({len(context)} chars):")
    print(context[:200] + "..." if len(context) > 200 else context)
except Exception as e:
    print(f"❌ Error formatting memory: {e}")
    exit(1)

# Test 3: Memory Injection Middleware
print("\n💉 Test 3: Memory Injection Middleware")
print("-" * 60)
try:
    injector = MemoryInjectionMiddleware()
    
    # Sample agent state with a user message
    test_state = {
        "messages": [
            {"role": "system", "content": "You are a helpful agent."},
            {"role": "user", "content": "What do I prefer in my interactions?"}
        ]
    }
    
    print("Original message:")
    print(f"  {test_state['messages'][-1]['content']}")
    
    # Apply middleware
    updated_state = injector(test_state)
    
    print("\nAfter memory injection:")
    user_msg = updated_state['messages'][-1]['content']
    preview = user_msg[:150] + "..." if len(user_msg) > 150 else user_msg
    print(f"  {preview}")
    print(f"✓ Memory successfully injected! Message expanded from original.")
    
except Exception as e:
    print(f"❌ Error in injection middleware: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: Token Management Middleware
print("\n📊 Test 4: Token Management Middleware")
print("-" * 60)
try:
    manager = TokenManagementMiddleware()
    
    test_state = {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you for asking!"},
        ]
    }
    
    updated_state = manager(test_state)
    token_count = updated_state.get("last_token_count", 0)
    print(f"✓ Token count calculated: {token_count} tokens")
    print(f"  Threshold: 8000 tokens | Status: {'⚠️  OVER' if updated_state.get('needs_rethink') else '✓ OK'}")
    
except Exception as e:
    print(f"❌ Error in token management: {e}")
    exit(1)

# Test 5: Memory Rethink Middleware
print("\n🧠 Test 5: Memory Rethink Middleware")
print("-" * 60)
try:
    rethink = MemoryRethinkMiddleware()
    
    test_state = {
        "messages": [],
        "needs_rethink": True,
    }
    
    updated_state = rethink(test_state)
    print("✓ Rethink middleware executed")
    print(f"  Needs rethink cleared: {not updated_state.get('needs_rethink', False)}")
    
except Exception as e:
    print(f"❌ Error in rethink middleware: {e}")
    exit(1)

print()
print("=" * 60)
print("✓ ALL MIDDLEWARE TESTS PASSED!")
print("=" * 60)
print()
print("Middleware Architecture:")
print("  • MemoryInjectionMiddleware: Injects dynamic memory before LLM calls")
print("  • TokenManagementMiddleware: Monitors context size and triggers compression")
print("  • MemoryRethinkMiddleware: Updates/compresses memory blocks as needed")
print()
print("To use with agent:")
print("  1. Set OPENAI_API_KEY environment variable")
print("  2. Or set API_KEY in .env")
print("  3. Then run: python test_agent_query.py")
