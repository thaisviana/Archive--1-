"""
Web search tool for Deep Agent skills.

This module implements the search_web tool as part of the web-search skill.
Provides real-time web search capability with multiple backend options.
"""

from typing import Optional
import os


def search_web(
    query: str,
    max_results: int = 5,
    region: str = "pt-br"
) -> str:
    """
    Search the web for information.
    
    Supports multiple search backends with fallback handlers.
    
    Args:
        query: The search query (string)
        max_results: Maximum number of results to return (1-10). Defaults to 5.
        region: Region/language code (e.g., 'pt-br' for Portuguese Brazil). Defaults to 'pt-br'.
    
    Returns:
        A formatted string with search results including title, snippet, and URL for each result.
        Returns guidance if no search backend available.
    
    Example:
        >>> results = search_web("weather in São Paulo")
        >>> print(results)
    """
    
    if not query or not query.strip():
        return "❌ Error: Query cannot be empty."
    
    if max_results < 1 or max_results > 10:
        return "❌ Error: max_results must be between 1 and 10."
    
    query = query.strip()
    
    # Try ddgs backend first
    try:
        from ddgs import DDGS
        results = _search_with_ddgs(query, max_results, region)
        if results:
            return results
    except Exception as e:
        pass  # Fall through to next option
    
    # Try requests + Google fallback
    try:
        results = _search_with_requests(query, max_results)
        if results:
            return results
    except Exception as e:
        pass  # Fall through to guidance
    
    # Provide helpful guidance
    demo_mode = os.environ.get('WEB_SEARCH_DEMO', 'true').lower() == 'true'
    
    if demo_mode:
        return _get_demo_results(query, max_results)
    
    return (
        f"⚠️ Web search temporarily unavailable for '{query}'.\n\n"
        "To enable web search, install: pip install ddgs\n\n"
        "You can also:\n"
        "1. Check your internet connection\n"
        "2. Try a different query\n"
        "3. Check if search options are configured in .env\n"
        "4. Set WEB_SEARCH_DEMO=false in .env if you don't want demo results"
    )


def _search_with_ddgs(query: str, max_results: int, region: str) -> Optional[str]:
    """Try searching with ddgs library."""
    try:
        from ddgs import DDGS
        
        ddgs = DDGS(timeout=10)
        results = ddgs.text(query, region=region, max_results=max_results)
        
        if not results:
            return None
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            body = result.get('body', 'No description')
            href = result.get('href', '')
            
            formatted_results.append(
                f"{i}. **{title}**\n"
                f"   {body}\n"
                f"   🔗 {href}"
            )
        
        header = f"🔍 Web Search Results for '{query}' ({len(results)} results):\n\n"
        return header + "\n\n".join(formatted_results)
    
    except ImportError:
        raise ImportError("ddgs not installed")
    except Exception as e:
        raise Exception(f"ddgs search failed: {str(e)}")


def _search_with_requests(query: str, max_results: int) -> Optional[str]:
    """Try searching with requests library as fallback."""
    try:
        import requests
        
        # Try a simple DuckDuckGo HTML instant answer endpoint
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0'
        }
        
        # Use a public search API or endpoint
        params = {
            'q': query,
            'format': 'json'
        }
        
        # Try startpage.com API
        url = "https://www.startpage.com/api/v1/query"
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'results' in data:
                results = data['results'][:max_results]
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"{i}. **{result.get('title', 'No title')}**\n"
                        f"   {result.get('summary', 'No description')}\n"
                        f"   🔗 {result.get('url', '')}"
                    )
                
                header = f"🔍 Web Search Results for '{query}' ({len(results)} results):\n\n"
                return header + "\n\n".join(formatted_results)
        
        return None
    
    except ImportError:
        raise ImportError("requests not installed")
    except Exception as e:
        raise Exception(f"requests search failed: {str(e)}")


def _get_demo_results(query: str, max_results: int) -> str:
    """Provide demo results for testing without internet connection."""
    demo_db = {
        "python": [
            {
                "title": "Welcome to Python.org",
                "body": "The official home of the Python Programming Language. Python is a powerful, flexible, and easy-to-learn programming language.",
                "url": "https://www.python.org"
            },
            {
                "title": "Python Programming Tutorials",
                "body": "Learn Python programming from beginner to advanced level with tutorials, examples, and best practices.",
                "url": "https://www.python.org/doc"
            }
        ],
        "weather": [
            {
                "title": "Current Weather",
                "body": "Real-time weather information for cities worldwide. Check temperature, humidity, wind speed, and forecasts.",
                "url": "https://weather.example.com"
            },
            {
                "title": "Weather Forecast",
                "body": "7-day weather forecast with detailed meteorological data and reports.",
                "url": "https://forecast.example.com"
            }
        ],
        "news": [
            {
                "title": "Latest News Today",
                "body": "Breaking news and latest updates from around the world. Stay informed with live news coverage.",
                "url": "https://news.example.com"
            },
            {
                "title": "News Headlines",
                "body": "Top news headlines, trending stories, and in-depth reporting on current events.",
                "url": "https://headlines.example.com"
            }
        ]
    }
    
    # Find matching demo results
    results = None
    for key, items in demo_db.items():
        if key.lower() in query.lower():
            results = items
            break
    
    # Default to Python docs if no match
    if not results:
        results = [
            {
                "title": f"Search Results for '{query}'",
                "body": "Demo mode: Web search is currently using demo data. Install ddgs for real-time search results.",
                "url": f"https://www.google.com/search?q={query.replace(' ', '+')}"
            }
        ]
    
    # Limit to max_results
    results = results[:max_results]
    
    formatted_results = []
    for i, result in enumerate(results, 1):
        title = result.get('title', 'No title')
        body = result.get('body', 'No description')
        url = result.get('url', '')
        
        formatted_results.append(
            f"{i}. **{title}**\n"
            f"   {body}\n"
            f"   🔗 {url}"
        )
    
    header = f"🔍 Web Search Results for '{query}' ({len(results)} demo results):\n[Demo Mode - Install ddgs for real-time results]\n\n"
    return header + "\n\n".join(formatted_results)
