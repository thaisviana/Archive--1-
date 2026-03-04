# web-search Skill for Deep Agents

A fully-featured web search skill for Deep Agents that provides real-time search capability.

## Quick Start

This skill is already integrated into your agent! The agent will automatically use the web search capability when it detects you need current information.

### Using in your agent

No additional code needed - the skill is loaded automatically via the `skills/` directory.

### Manual skill usage (for testing)

```python
from skills.web_search.web_search import search_web

# Real-time web search
results = search_web("Python programming", max_results=5)
print(results)

# With specific region
results = search_web("notícias Brasil", max_results=3, region="pt-br")
print(results)
```

## Dependencies

**For real-time search:**
```bash
pip install ddgs
```

**For demo mode (no internet):**
No dependencies needed - uses built-in demo data.

## How It Works

### Progressive Disclosure

When you ask your agent a question:
1. The agent reads `SKILL.md` frontmatter
2. Detects if a question requires web search
3. Loads full `SKILL.md` documentation
4. Reviews `web_search.py` for implementation
5. Uses `search_web()` tool to answer

### Search Backends

The tool tries multiple backends in order:
1. **ddgs library** - Best performance, real-time results
2. **requests + startpage API** - Fallback if ddgs unavailable
3. **Demo mode** - Returns mock data for testing (default)

### Demo Mode

By default, the skill runs in demo mode to work without internet:

```python
# Returns demo results
result = search_web("python")

# Disable demo mode
import os
os.environ['WEB_SEARCH_DEMO'] = 'false'
# Now it only works if ddgs is installed and internet is available
```

## Configuration

Set environment variables in `.env`:

```bash
# Enable/disable demo mode (default: true)
WEB_SEARCH_DEMO=true

# You can also set proxy if needed
DDGS_PROXY=http://proxy.example.com:8080
```

## Examples

### Example 1: Current Events
```
User: "What's happening in the news today?"
Agent: Uses search_web("news today") → Returns latest news
```

### Example 2: Technical Documentation
```
User: "How do I use async/await in Python?"
Agent: Uses search_web("Python async await") → Returns tutorials and docs
```

### Example 3: Weather
```
User: "What's the weather forecast for tomorrow?"
Agent: Uses search_web("weather forecast tomorrow") → Returns weather data
```

## Files in This Skill

- `SKILL.md` - Skill metadata and instructions for the agent
- `web_search.py` - Implementation of the `search_web()` tool
- `README.md` - This file

## Customization

To modify the skill:

1. **Add new search backends**: Edit `_search_with_*()` functions in `web_search.py`
2. **Extend demo database**: Add more entries to the `demo_db` dict in `_get_demo_results()`
3. **Change result format**: Modify the formatting in search functions
4. **Adjust max results**: Edit the `max_results` parameter handling

## Troubleshooting

### Web search not working
1. Check internet connection
2. Install ddgs: `pip install ddgs`
3. Set `WEB_SEARCH_DEMO=false` in `.env` if demo mode is interfering
4. Check firewall/proxy settings

### Results are inaccurate
- Try more specific queries
- Use proper grammar and spelling
- Specify region with region parameter (e.g., "pt-br", "en-us")

### Too many results
- Reduce `max_results` parameter (currently default is 5)
- Try a more specific query

## Version History

- **v1.0** (2026-03-03): Initial release with ddgs backend and demo mode
