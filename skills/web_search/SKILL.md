---
name: web-search
description: Use this skill to search the web in real-time for current information, news, weather, events, and any publicly available data. Required when the agent needs up-to-date information not in its training data or knowledge base.
---

# Web Search Skill

Real-time web search capability for your agent using DuckDuckGo API (no authentication required).

## Overview

This skill provides the `search_web` tool to query the internet for current information. Use this when:
- User asks about current events, news, or weather
- Information is time-sensitive or might have changed
- Knowledge base doesn't contain required information
- User explicitly asks to "search the web" or "look up online"

## Features

- **Real-time Search**: Get live results from the web
- **Multiple Results**: Returns up to 10 results per query
- **Region Support**: Supports regional/language-specific searches (e.g., pt-br for Portuguese Brazil)
- **Error Handling**: Graceful fallback if API unavailable
- **No Authentication**: Uses free DuckDuckGo API - no keys required

## Tool Reference

### search_web

```python
search_web(
    query: str,           # What to search for
    max_results: int = 5, # How many results (1-10, default 5)
    region: str = "pt-br" # Region code (default: pt-br for Portuguese)
) -> str
```

Returns formatted search results with title, snippet, and URL for each result.

## Usage Examples

### 1. Current Weather
```
User: "Qual é o tempo em São Paulo agora?"
Agent: Uses search_web("tempo em São Paulo") → Returns current weather info
```

### 2. Breaking News
```
User: "O que está acontecendo no Brasil hoje?"
Agent: Uses search_web("notícias Brasil") → Returns latest news
```

### 3. Specific Information
```
User: "Qual é o preço do Bitcoin?"
Agent: Uses search_web("preço Bitcoin") → Returns current price
```

### 4. Custom Region
```
User: "What's trending in the US?"
Agent: Uses search_web("trending US", region="en-us") → Return US-specific results
```

## Installation

The skill requires the `ddgs` library (formerly `duckduckgo-search`):

```bash
pip install ddgs
```

Or add to your `requirements.txt`:
```
ddgs>=9.0.0
```

## Implementation Details

- **No Rate Limits**: DuckDuckGo API doesn't enforce strict rate limits for normal usage
- **Timeout**: 10 seconds per search request
- **Result Format**: Markdown-formatted output with title, snippet, and clickable links
- **Error Handling**: Returns user-friendly error messages if search fails

## Tips for Best Results

1. **Be Specific**: "weather in São Paulo" works better than just "weather"
2. **Use Natural Language**: The tool understands normal queries
3. **Include Date Context**: "news about X today" or "latest news on X"
4. **Language Matters**: Results are better when query matches region setting
   - Portuguese queries with region="pt-br"
   - English queries with region="en-us"

## Troubleshooting

### "Web search unavailable"
The `ddgs` library isn't installed. Run:
```bash
pip install ddgs
```

### Empty Results
- Try a simpler query
- Check spelling and grammar
- A different region setting might help

### Timeout
The search took too long. Try a more specific query or fewer max_results.
