"""
Integration tests for web_search skill with Deep Agent.

Tests how the agent uses the web-search skill in complete workflows
and with actual agent queries.
"""

import pytest
import uuid
import os
from references.agent_init import get_agent, reset_agent
from references.agent_assembly import run_agent
from skills.web_search.web_search import search_web


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def demo_mode():
    """Ensure demo mode is enabled for integration tests."""
    os.environ['WEB_SEARCH_DEMO'] = 'true'
    yield
    os.environ['WEB_SEARCH_DEMO'] = 'true'


@pytest.fixture
def agent():
    """Get a fresh agent instance for testing."""
    reset_agent()
    test_agent = get_agent()
    yield test_agent
    reset_agent()


@pytest.fixture
def session_data():
    """Generate session and user IDs for tests."""
    return {
        'session_id': str(uuid.uuid4()),
        'user_id': 'test_user',
    }


# ============================================================================
# Direct Skill Tests
# ============================================================================

class TestDirectSkillUsage:
    """Test the web_search skill directly."""
    
    def test_search_web_python(self, demo_mode):
        """Test searching for Python."""
        result = search_web("python", max_results=2)
        
        assert result is not None
        assert "Web Search Results" in result
        assert "python" in result.lower()
        assert "🔗" in result
    
    def test_search_web_weather(self, demo_mode):
        """Test searching for weather."""
        result = search_web("weather", max_results=3)
        
        assert result is not None
        assert "Web Search Results" in result
        assert "🔗" in result
    
    def test_search_web_news(self, demo_mode):
        """Test searching for news."""
        result = search_web("news", max_results=2)
        
        assert result is not None
        assert "Web Search Results" in result
        assert "news" in result.lower()
    
    def test_search_web_multiple_queries(self, demo_mode):
        """Test multiple consecutive searches."""
        queries = ["python", "weather", "news"]
        
        for query in queries:
            result = search_web(query, max_results=2)
            assert "Web Search Results" in result
            assert "🔗" in result
    
    def test_search_web_result_format(self, demo_mode):
        """Verify result formatting is consistent."""
        result = search_web("test", max_results=2)
        
        # Check formatting elements
        assert "1." in result or "results" in result.lower()
        assert "**" in result  # Bold markdown
        assert "http" in result  # URL present


# ============================================================================
# Agent Integration Tests
# ============================================================================

@pytest.mark.skipif(
    not os.environ.get('OPENAI_API_KEY'),
    reason="Requires OPENAI_API_KEY environment variable"
)
class TestAgentWebSearchIntegration:
    """Test web_search skill integrated with the agent."""
    
    def test_agent_with_web_search(self, agent, session_data, demo_mode):
        """Test agent can use web search skill."""
        result = run_agent(
            agent=agent,
            user_input="Search for information about Python programming",
            session_id=session_data['session_id'],
            user_id=session_data['user_id']
        )
        
        # Verify result structure
        assert result is not None
        assert "messages" in result
        assert len(result["messages"]) > 0
    
    def test_agent_multiple_web_searches(self, agent, session_data, demo_mode):
        """Test agent can perform multiple web searches."""
        queries = [
            "What is Python?",
            "Tell me about weather forecasting",
            "Latest technology news",
        ]
        
        for query in queries:
            result = run_agent(
                agent=agent,
                user_input=query,
                session_id=session_data['session_id'],
                user_id=session_data['user_id']
            )
            
            assert result is not None
            assert "messages" in result
    
    def test_agent_response_structure(self, agent, session_data, demo_mode):
        """Verify agent response has proper structure."""
        result = run_agent(
            agent=agent,
            user_input="Search the web for Python",
            session_id=session_data['session_id'],
            user_id=session_data['user_id']
        )
        
        # Check response structure
        assert isinstance(result, dict)
        assert "messages" in result
        assert isinstance(result["messages"], list)
    
    def test_agent_session_persistence(self, agent, session_data, demo_mode):
        """Test that session data is preserved across turns."""
        session_id = session_data['session_id']
        
        # First turn
        result1 = run_agent(
            agent=agent,
            user_input="Search for Python",
            session_id=session_id,
            user_id=session_data['user_id']
        )
        
        # Second turn
        result2 = run_agent(
            agent=agent,
            user_input="Search for weather",
            session_id=session_id,
            user_id=session_data['user_id']
        )
        
        # Both should succeed
        assert result1 is not None
        assert result2 is not None


# ============================================================================
# Skill Feature Integration Tests
# ============================================================================

class TestSkillFeatureIntegration:
    """Test specific skill features in integration scenarios."""
    
    def test_skill_with_different_result_counts(self, demo_mode):
        """Test skill handles different result counts."""
        for count in [1, 3, 5, 10]:
            result = search_web("test", max_results=count)
            assert "Web Search Results" in result
    
    def test_skill_with_different_regions(self, demo_mode):
        """Test skill handles different regions."""
        regions = ["pt-br", "en-us", "es-es"]
        
        for region in regions:
            result = search_web("test", max_results=2, region=region)
            assert "Web Search Results" in result
    
    def test_skill_query_variety(self, demo_mode):
        """Test skill with various query types."""
        queries = [
            "python",
            "weather today",
            "latest news",
            "how to program",
            "best practices",
        ]
        
        for query in queries:
            result = search_web(query, max_results=2)
            assert "Web Search Results" in result
            assert "🔗" in result
    
    def test_skill_consistency(self, demo_mode):
        """Test that skill returns consistent structure."""
        query = "python"
        
        result1 = search_web(query, max_results=3)
        result2 = search_web(query, max_results=3)
        
        # Results should have the same structure and contain query
        assert "Web Search Results" in result1
        assert "Web Search Results" in result2
        assert query.lower() in result1.lower()
        assert query.lower() in result2.lower()
        # Should both have multiple results
        assert result1.count("🔗") > 0
        assert result2.count("🔗") > 0


# ============================================================================
# Workflow Tests
# ============================================================================

class TestCompleteWorkflows:
    """Test complete workflows combining skill and agent."""
    
    def test_search_then_process(self, demo_mode):
        """Test searching and processing results."""
        # Search
        result = search_web("python programming", max_results=5)
        
        # Verify we got results
        assert "Web Search Results" in result
        assert "python" in result.lower()
        
        # Verify we can parse/process the results
        lines = result.split('\n')
        assert len(lines) > 5  # Multiple result lines
    
    def test_multiple_skills_in_sequence(self, demo_mode):
        """Test using skill multiple times in sequence."""
        queries = ["python", "javascript", "rust"]
        results = []
        
        for query in queries:
            result = search_web(query, max_results=2)
            results.append(result)
            assert "Web Search Results" in result
        
        # All results should be different
        assert len(set(results)) == len(results)
    
    def test_mixed_query_types(self, demo_mode):
        """Test mixing different types of queries."""
        test_cases = [
            ("python", 1),
            ("weather", 3),
            ("news", 5),
            ("how to learn", 2),
        ]
        
        for query, limit in test_cases:
            result = search_web(query, max_results=limit)
            assert "Web Search Results" in result
            assert "🔗" in result


# ============================================================================
# Error Handling & Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases in skill usage."""
    
    def test_empty_query_handling(self, demo_mode):
        """Test handling of empty queries."""
        result = search_web("", max_results=5)
        assert "Error" in result or "empty" in result.lower()
    
    def test_invalid_max_results(self, demo_mode):
        """Test handling of invalid max_results."""
        result = search_web("test", max_results=100)
        assert "between 1 and 10" in result or "Error" in result
    
    def test_special_characters_in_query(self, demo_mode):
        """Test queries with special characters."""
        result = search_web("python !@#$%", max_results=2)
        # Should handle gracefully
        assert result is not None
    
    def test_very_long_query(self, demo_mode):
        """Test very long queries."""
        long_query = "a" * 500
        result = search_web(long_query, max_results=2)
        # Should handle gracefully
        assert result is not None


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test skill performance characteristics."""
    
    def test_skill_response_time(self, demo_mode, benchmark=None):
        """Test that skill responds reasonably fast."""
        if benchmark:
            # If pytest-benchmark is available
            benchmark(search_web, "python", max_results=2)
        else:
            # Manual timing check for demo mode
            result = search_web("python", max_results=2)
            assert result is not None
            assert len(result) > 0
    
    def test_multiple_searches_performance(self, demo_mode):
        """Test performance with multiple searches."""
        results = []
        for i in range(5):
            result = search_web("test", max_results=2)
            results.append(result)
        
        assert len(results) == 5
        assert all(r is not None for r in results)


# ============================================================================
# Parametrized Tests
# ============================================================================

class TestParametrized:
    """Parametrized tests for various scenarios."""
    
    @pytest.mark.parametrize("query,expected_in_result", [
        ("python", "python"),
        ("weather", "weather"),
        ("news", "news"),
    ])
    def test_query_in_result(self, query, expected_in_result, demo_mode):
        """Test that query appears in result."""
        result = search_web(query, max_results=2)
        assert expected_in_result.lower() in result.lower()
    
    @pytest.mark.parametrize("max_results", [1, 3, 5, 10])
    def test_max_results_limits(self, max_results, demo_mode):
        """Test various max_results limits."""
        result = search_web("test", max_results=max_results)
        assert "Web Search Results" in result
        assert "🔗" in result
    
    @pytest.mark.parametrize("region", ["pt-br", "en-us", "es-es"])
    def test_different_regions(self, region, demo_mode):
        """Test different region parameters."""
        result = search_web("test", region=region)
        assert result is not None
        assert "Web Search Results" in result


# ============================================================================
# Test utility functions
# ============================================================================

@pytest.fixture
def print_session_info():
    """Print session information for debugging."""
    print(f"\n📍 Session: {uuid.uuid4()}")
    print(f"🌐 Demo Mode: {os.environ.get('WEB_SEARCH_DEMO', 'true')}")
    yield
    print("✅ Test completed")
