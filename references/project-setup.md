# Project Setup Guide

When a user asks to create a new agent project using this skill, you MUST collect the following information before writing any code. Work through each section sequentially. If the user doesn't have an answer for an optional field, use the suggested default.

## Step 1: System Prompt Foundation

The system prompt defines the agent's identity, tone, and behavioral boundaries. You need a starting point.

**Ask the user:**

- Do you have a system prompt already written? If so, paste it or provide the file path.
- Do you have a folder with reference materials (brand guidelines, existing prompts, documentation) that can inspire the system prompt? If so, provide the path.
- If neither: describe in 2-3 sentences what this agent should do, who it serves, and what tone it should use.

**What you produce from this:**
- The `persona` memory block initial content
- The `user_profile` memory block structure
- The 4-layer system prompt hierarchy (see `references/prompt-patterns.md`)

## Step 2: Model & Provider

**Ask the user:**

| Question | Example | Required |
|---|---|---|
| Which LLM provider? | OpenAI, Anthropic, Google, Azure, etc. | Yes |
| Which model? | `gpt-4o-mini`, `claude-sonnet-4-5-20250514`, etc. | Yes |
| Do you have the API key configured in `.env`? | Confirm `OPENAI_API_KEY` or equivalent is set | Yes |

**Validation:**
- Verify the `.env` file exists (copy from `templates/env.example` if not)
- Confirm the API key environment variable matches the chosen provider
- Test connectivity with a minimal API call before proceeding

## Step 3: Agent Identity

**Ask the user:**

| Question | Example | Required |
|---|---|---|
| Agent name | `financial-advisor`, `support-agent`, `research-assistant` | Yes |
| Short description (1 sentence) | "AI assistant that helps customers with billing questions" | Yes |

**What you produce from this:**
- Project directory name
- `AGENTS.md` header (for Deep Agents `memory=` parameter)
- Default `persona` block phrasing

## Step 4: Memory Blocks

Memory blocks are the agent's structured, editable beliefs. Each block has metadata that controls how it behaves at runtime.

**For each block, ask the user:**

| Field | Description | Example | Required |
|---|---|---|---|
| `label` | Unique snake_case identifier | `persona` | Yes |
| `description` | When to read this block, when to update it, what belongs here | "Agent identity and personality. Update only if the user explicitly requests a persona change." | Yes |
| `initial_value` | Starting content for this block | "I am a financial advisor assistant..." | Yes |
| `char_limit` | Maximum characters allowed in this block | `2000` | Yes |
| `read_only` | Can the agent edit this block at runtime? | `true` for persona, `false` for preferences | Yes |

**Suggested defaults (propose these, let the user customize):**

| Label | Char Limit | Read-Only | Description |
|---|---|---|---|
| `persona` | 2000 | Yes | Agent identity and personality. Only changed by the builder, never by the agent at runtime. |
| `user_profile` | 3000 | No | Known facts about the user: name, role, company, communication preferences. Update when the user shares personal information. |
| `preferences` | 2000 | No | User interaction preferences: language, tone, formatting, topics of interest. Update when the user expresses a preference. |
| `working_context` | 4000 | No | Current task, project, or conversation focus. Update frequently as the user shifts topics. This is the most volatile block. |
| `learnings` | 3000 | No | Accumulated insights about what works and what doesn't for this user. Update when a pattern emerges across multiple interactions. |

**The user can add custom blocks.** Examples:
- `company_policies` (read-only, 5000 chars) — Internal rules the agent must follow
- `product_catalog` (read-only, 4000 chars) — Product information for a sales agent
- `project_notes` (editable, 3000 chars) — Notes about an ongoing project

**Important rules for memory blocks:**
- Every block MUST have a `char_limit`. There is no unlimited block.
- `read_only=true` blocks are injected into context but the agent cannot call edit tools on them.
- The `description` field is included in the system prompt so the agent knows when and how to use each block.

### Rethink Threshold

When a block reaches **80% of its `char_limit`**, the `rethink_memory` hook automatically triggers a compression pass:
1. The agent rewrites the block to be more concise while preserving essential information
2. If the block still exceeds the limit after compression, overflow content is offloaded to the filesystem (Deep Agents `StoreBackend`) where it remains searchable but is not injected into every turn
3. The offloaded content is accessible via `search_conversation_history` (Layer 2)

## Step 5: Context Window Budget

The dynamic memory blocks are injected into every user message via `inject_memory`. You need to define how much of the context window they can occupy.

**Ask the user:**

| Question | Suggested Default | Notes |
|---|---|---|
| Total character budget for all dynamic blocks combined | Sum of all editable blocks' `char_limit` values | This is the ceiling for `inject_memory` |
| What is the model's context window? | Depends on model (e.g., 128k for GPT-4o) | Needed to calculate ratios |
| Conversation history token threshold for summarization | `8000` tokens | Triggers `summarize_if_needed` |

**How to calculate:**
- Sum all `char_limit` values for blocks with `read_only=false` → this is the dynamic injection ceiling
- Sum all `char_limit` values for blocks with `read_only=true` → this is the static system prompt size
- Dynamic ceiling + static size + conversation history must fit within the model's context window
- Leave at least 40% of the context window for conversation history and tool results

**Example budget:**

```
Model: gpt-4o-mini (128k context)
Static blocks:  persona (2000) + company_policies (5000) = 7000 chars (~1750 tokens)
Dynamic blocks: user_profile (3000) + preferences (2000) + working_context (4000) + learnings (3000) = 12000 chars (~3000 tokens)
Conversation history threshold: 8000 tokens
Tool results: ~2000 tokens per turn
Available for conversation: 128k - 1750 - 3000 - 2000 = ~121k tokens
```

## Step 6: Knowledge Base (RAG)

**Ask the user:**

| Question | Example | Required |
|---|---|---|
| Do you have a directory of documents to ingest? | `./docs/`, `./knowledge-base/` | Optional |
| What formats? | PDF, Markdown, TXT, HTML | If yes above |
| What language are the documents in? | Portuguese, English, mixed | Yes (affects `text_search_config`) |
| Ingestion method preference | Contextual Retrieval (recommended) or standard chunking | Yes |

**Ingestion method options:**

| Method | Pros | Cons |
|---|---|---|
| **Contextual Retrieval** (recommended) | Higher accuracy — each chunk gets document-level context prepended before embedding | Slower ingestion, extra LLM call per chunk |
| **Standard Chunking** | Fast ingestion, no extra LLM cost | Lower retrieval accuracy for ambiguous chunks |

**Language configuration:**

| Document Language | `text_search_config` | Notes |
|---|---|---|
| Portuguese (BR) | `"pt_unaccent"` (custom) or `"portuguese"` | Requires `unaccent` extension for accent-insensitive search |
| English | `"english"` | Built-in PostgreSQL config |
| Mixed / Other | `"simple"` | No stemming, works with any language |

See `references/rag-pipeline.md` for the ingestion script and `references/memory-system.md` for the custom `pt_unaccent` configuration.

## Step 7: Knowledge Graph Ontology (Graphiti)

Graphiti automatically extracts entities and relationships, but a domain-specific ontology dramatically improves extraction quality. These questions help define what the graph should capture.

**Ask the user:**

### Entity Types

What are the main "things" in this agent's domain?

| Question | Example (financial advisor) | Example (support agent) |
|---|---|---|
| What entities does the agent deal with? | Clients, Portfolios, Assets, Markets | Users, Tickets, Products, Features |
| What attributes matter for each entity? | Client: risk_profile, investment_horizon | User: plan_tier, account_age |
| Are there entities that change over time? | Asset prices, portfolio allocations | Ticket status, feature availability |

### Relationship Types

How do these entities relate to each other?

| Question | Example (financial advisor) | Example (support agent) |
|---|---|---|
| What are the key relationships? | Client OWNS Portfolio, Portfolio CONTAINS Asset | User REPORTED Ticket, Ticket AFFECTS Product |
| Do relationships have temporal properties? | "Client held Asset X from Jan to Mar" | "User was on Pro plan until last month" |
| Are there preference relationships? | "Client prefers conservative investments" | "User prefers email over chat" |

### Fact Patterns

What kind of facts should the graph remember?

| Question | Example |
|---|---|
| What user statements should become facts? | "I'm risk-averse", "My budget is $50k", "I don't like Feature X" |
| What agent observations should become facts? | "User asks about refunds frequently", "User prefers detailed explanations" |
| What temporal facts matter? | "User changed plan on 2025-01-15", "Policy updated in Q3" |

**What you produce from this:**
- A `group_id` naming convention (e.g., `user_{user_id}`, `org_{org_id}`)
- Custom entity types for Graphiti's `EntityNode`
- Custom relationship types for `EntityEdge`
- Instructions for the system prompt on what to extract (added to the `persona` or a dedicated `ontology_instructions` block)

## Summary Checklist

After collecting all information, confirm with the user:

```
Project Setup Summary:
- [ ] Agent: {name} — {description}
- [ ] Model: {provider}:{model} (API key confirmed in .env)
- [ ] System prompt: {source — file path, folder, or written}
- [ ] Memory blocks: {N} blocks, {sum of char_limits} total characters
      Static (system prompt): {list of read-only blocks}
      Dynamic (per turn):     {list of editable blocks}
- [ ] Context budget: {dynamic ceiling} chars dynamic, {threshold} tokens history
- [ ] Knowledge base: {path or "none"}, method: {contextual retrieval | standard}
- [ ] Document language: {language} → text_search_config: {config}
- [ ] Graphiti ontology: {N} entity types, {N} relationship types
```

Once confirmed, proceed with the Implementation Checklist in `SKILL.md`.
