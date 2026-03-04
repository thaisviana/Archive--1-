# Skills directory for Deep Agents

This directory contains reusable agent capabilities (skills) that extend your agent's functionality.

## Available Skills

### web-search
Real-time web search capability for current information, news, and web-based queries.
- **Location**: `skills/web_search/`
- **Tool**: `search_web(query, max_results=5, region="pt-br")`
- **See**: `skills/web_search/SKILL.md` for documentation

## How Skills Are Loaded

When you create a deep agent with:
```python
from references.agent_init import get_agent

agent = get_agent()
```

The agent automatically discovers and loads all skills in the `skills/` directory based on `SKILL.md` files.

## Creating New Skills

To add a new skill:

1. Create a folder: `skills/my-skill/`
2. Add `SKILL.md` with frontmatter metadata
3. Add `.py` files with implementations
4. Agent automatically discovers and loads it

See `web_search/SKILL.md` for the correct format.

## Deep Agents Skills Specification

Skills follow the [Deep Agents Skills Specification](https://docs.deepgents.ai/guides/skills).

Key requirements:
- `SKILL.md` file with `name` and `description` frontmatter
- Description must be ≤ 1024 characters
- File size must be < 10 MB
- Uses progressive disclosure pattern
