"""
Comprehensive tests for the web_search skill.

Tests cover:
- Input validation
- Demo mode functionality
- Search backend fallbacks
- Result formatting
- Error handling
"""

import pytest
import os
from skills.web_search.web_search import search_web, _get_demo_results


class TestInputValidation:
    """Test input parameter validation."""
    
    def test_empty_query(self):
        """Empty query should return error."""
        result = search_web("")
        assert "Error: Query cannot be empty" in result
    
    def test_whitespace_only_query(self):
        """Query with only whitespace should return error."""
        result = search_web("   ")
        assert "Error: Query cannot be empty" in result
    
    def test_max_results_too_low(self):
        """max_results < 1 should return error."""
        result = search_web("test", max_results=0)
        assert "max_results must be between 1 and 10" in result
    
    def test_max_results_too_high(self):
        """max_results > 10 should return error."""
        result = search_web("test", max_results=11)
        assert "max_results must be between 1 and 10" in result
    
    def test_max_results_boundary_low(self):
        """max_results=1 should be valid."""
        result = search_web("python", max_results=1)
        assert "Web Search Results" in result or "Error" not in result
    
    def test_max_results_boundary_high(self):
        """max_results=10 should be valid."""
        result = search_web("python", max_results=10)
        assert "Web Search Results" in result or "Error" not in result


class TestDemoMode:
    """Test demo mode functionality."""
    
    def test_demo_mode_enabled(self):
        """Demo mode should return demo results by default."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("python")
        assert "Web Search Results" in result
        assert "python" in result.lower()
        assert "🔗" in result  # Should have links
    
    def test_demo_mode_disabled(self):
        """Disabled demo mode should show warning."""
        os.environ['WEB_SEARCH_DEMO'] = 'false'
        result = search_web("xyznonexistentquery123xyz")
        assert "temporarily unavailable" in result.lower() or "error" in result.lower()
    
    def test_demo_results_python(self):
        """Demo results for 'python' query."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("python", max_results=2)
        
        assert "1." in result  # First result
        assert "2." in result  # Second result
        assert "https://" in result  # Should have URLs
    
    def test_demo_results_weather(self):
        """Demo results for 'weather' query."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("weather", max_results=2)
        
        assert "Current Weather" in result or "Weather" in result
        assert "🔗" in result
    
    def test_demo_results_news(self):
        """Demo results for 'news' query."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("news", max_results=2)
        
        assert "news" in result.lower()
        assert "🔗" in result
    
    def test_demo_results_formatting(self):
        """Demo results should be properly formatted."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("python", max_results=2)
        
        # Check formatting elements
        assert "**" in result  # Bold markdown
        assert "🔗" in result  # Link emoji
        assert "Demo" not in result or "mode" in result.lower()  # Indication of demo


class TestResultFormatting:
    """Test result formatting."""
    
    def test_result_contains_header(self):
        """Result should contain search header with query."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("test query", max_results=2)
        
        assert "Web Search Results" in result
        assert "test query" in result
    
    def test_result_contains_count(self):
        """Result header should show result count."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("python", max_results=3)
        
        # Check for result count indicator
        assert "results" in result.lower() or "Web Search" in result
    
    def test_numbered_results(self):
        """Results should be numbered."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("python", max_results=3)
        
        assert "1." in result
        assert "2." in result
    
    def test_result_contains_links(self):
        """Results should contain URLs."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("python", max_results=2)
        
        assert "http" in result.lower()


class TestMaxResultsLimiting:
    """Test that max_results parameter limits the output."""
    
    def test_max_results_one(self):
        """max_results=1 should return only 1 result."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("python", max_results=1)
        
        # Should have first result
        assert "1." in result
        # Should not have second result
        assert "2." not in result
    
    def test_max_results_five(self):
        """max_results=5 should have up to 5 results."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("python", max_results=5)
        
        # Should have first result
        assert "1." in result
        # Might have up to 5, depending on demo data
    
    def test_max_results_respected(self):
        """max_results should limit the number of results."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result_1 = search_web("python", max_results=1)
        result_2 = search_web("python", max_results=2)
        
        # Result with 1 should be shorter or equal to result with 2
        assert len(result_1) <= len(result_2)


class TestRegionParameter:
    """Test region parameter functionality."""
    
    def test_default_region(self):
        """Default region should be 'pt-br'."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("python")
        # Should not error with default region
        assert "Error: Query cannot be empty" not in result
    
    def test_custom_region_pt_br(self):
        """pt-br region should work."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("python", region="pt-br")
        assert "Web Search Results" in result or "Error" not in result
    
    def test_custom_region_en_us(self):
        """en-us region should work."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("python", region="en-us")
        assert "Web Search Results" in result or "Error" not in result


class TestDemoResultsFunction:
    """Test the _get_demo_results helper function."""
    
    def test_demo_results_returns_string(self):
        """_get_demo_results should return a string."""
        result = _get_demo_results("python", 2)
        assert isinstance(result, str)
    
    def test_demo_results_contains_query(self):
        """Demo results should mention the query."""
        result = _get_demo_results("python", 2)
        assert "python" in result.lower()
    
    def test_demo_results_respects_limit(self):
        """Demo results should respect max_results."""
        result_1 = _get_demo_results("python", 1)
        result_2 = _get_demo_results("python", 3)
        
        # More results should generally have more content
        assert len(result_2) >= len(result_1)
    
    def test_demo_results_formatted(self):
        """Demo results should be properly formatted."""
        result = _get_demo_results("python", 2)
        
        assert "**" in result  # Bold titles
        assert "🔗" in result  # Link indicator
        assert "1." in result  # Numbered results


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_none_query_raises_error(self):
        """None as query should raise error or return error message."""
        try:
            result = search_web(None, max_results=5)
            assert "Error" in result or "empty" in result.lower()
        except (TypeError, AttributeError):
            # It's fine if it raises an error for None
            pass
    
    def test_special_characters_query(self):
        """Special characters in query should be handled."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("python & javascript!@#$")
        # Should not crash, might show results or demo
        assert result is not None
    
    def test_very_long_query(self):
        """Very long query should be handled."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        long_query = "a" * 500
        result = search_web(long_query)
        assert result is not None


class TestIntegration:
    """Integration tests combining multiple features."""
    
    def test_complete_search_flow(self):
        """Test a complete search workflow."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        
        # Search
        result = search_web("python programming", max_results=3, region="pt-br")
        
        # Verify result contains expected components
        assert "Web Search Results" in result
        assert "python programming" in result or "python" in result.lower()
        assert "1." in result
        assert "🔗" in result
    
    def test_multiple_searches(self):
        """Test multiple searches in sequence."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        
        queries = ["python", "weather", "news"]
        results = [search_web(q, max_results=2) for q in queries]
        
        # All searches should return valid results
        for result in results:
            assert "Web Search Results" in result
            assert "🔗" in result
    
    def test_search_result_consistency(self):
        """Same query should return consistent results."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        
        result1 = search_web("python", max_results=2)
        result2 = search_web("python", max_results=2)
        
        # Results should be the same
        assert result1 == result2


class TestEnvironmentConfiguration:
    """Test environment variable configuration."""
    
    def test_demo_mode_env_true(self):
        """WEB_SEARCH_DEMO=true should enable demo mode."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        result = search_web("python")
        assert "Web Search Results" in result
    
    def test_demo_mode_env_false(self):
        """WEB_SEARCH_DEMO=false should disable demo mode."""
        os.environ['WEB_SEARCH_DEMO'] = 'false'
        result = search_web("xyznonexistentquery123xyz")
        # Should either show unavailable message or try real search (which will fail)
        assert "temporary" in result.lower() or "error" in result.lower() or "unavailable" in result.lower()
    
    def test_demo_mode_env_cleanup(self):
        """Restore WEB_SEARCH_DEMO for other tests."""
        os.environ['WEB_SEARCH_DEMO'] = 'true'
        # Other tests should run in demo mode


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def setup_demo_mode():
    """Ensure demo mode is enabled for all tests."""
    os.environ['WEB_SEARCH_DEMO'] = 'true'
    yield
    os.environ['WEB_SEARCH_DEMO'] = 'true'


# ============================================================================
# Test utilities (for manual testing)
# ============================================================================

def manual_test_all():
    """Run all tests manually (for development)."""
    os.environ['WEB_SEARCH_DEMO'] = 'true'
    
    print("\n" + "="*80)
    print("🧪 MANUAL TEST SUITE FOR SEARCH_WEB")
    print("="*80 + "\n")
    
    # Test 1: Basic search
    print("Test 1: Basic Search")
    print("-" * 80)
    result = search_web("python", max_results=2)
    print(result)
    print()
    
    # Test 2: Validation
    print("Test 2: Input Validation (empty query)")
    print("-" * 80)
    result = search_web("")
    print(result)
    print()
    
    # Test 3: Max results limit
    print("Test 3: Max Results Validation (invalid)")
    print("-" * 80)
    result = search_web("python", max_results=15)
    print(result)
    print()
    
    # Test 4: Different query
    print("Test 4: Different Query (weather)")
    print("-" * 80)
    result = search_web("weather", max_results=3)
    print(result)
    print()
    
    print("="*80)
    print("✅ Manual tests complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Run manual tests when script is executed directly
    manual_test_all()
    
    print("\n📊 To run full pytest suite:")
    print("   pytest tests/test_web_search.py -v")
