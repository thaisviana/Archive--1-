# Human-in-the-Loop Patterns

## Contents
- Core Principle — action categorization matrix (read-only → irreversible)
- Deep Agents interrupt_on — tool-level approval configuration
- Approval Flow — interrupt/resume lifecycle with approve, edit, reject
- Confidence-Based Escalation — threshold pattern (0.3–0.9)
- Escalation Patterns — graduated, proactive confirmation, audit trail
- Common Mistakes

## Core Principle

Not every agent action needs approval. Define clear boundaries:

| Action Type | Approval | Example |
|---|---|---|
| **Read-only** | Never | search_knowledge_base, view_memory_blocks |
| **Low-stakes write** | Never | insert_memory_block, rethink_memory_block |
| **High-stakes write** | Always | delete_memory_block, external API calls |
| **Financial risk** | Always | purchases, payments, billing changes, resource provisioning |
| **User/builder harm** | Always | actions that could damage reputation, leak data, or cause loss |
| **Irreversible action** | Always | sending emails, database mutations |

**Default safety rule:** When in doubt, the agent MUST request approval for any action it judges could cause financial loss or harm to the user or the agent's builder. This applies even if the action type is not explicitly listed above. Err on the side of caution — a false positive (unnecessary approval request) is always preferable to a false negative (unauthorized harmful action).

## Deep Agents interrupt_on

Configure which tools pause for human approval:

```python
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()

agent = create_deep_agent(
    model="openai:gpt-5-mini-2025-08-07",
    tools=[...],
    interrupt_on={
        "delete_memory_block": True,
        "execute_external_action": {
            "allowed_decisions": ["approve", "edit", "reject"],
        },
    },
    checkpointer=checkpointer,
)
```

## Approval Flow

```
Agent decides to call delete_memory_block("outdated_project")
        │
        ▼
    INTERRUPT
        │
        ▼
User sees: "I want to delete the 'outdated_project' memory block.
            It contains notes about a completed project.
            [Approve] [Edit] [Reject]"
        │
        ├─ Approve → Agent continues execution
        ├─ Edit    → User modifies the action, agent retries
        └─ Reject  → Agent receives rejection, adjusts approach
```

### Resuming After Approval

```python
from langgraph.types import Command

config = {"configurable": {"thread_id": session_id}}

# Initial invocation (may pause at interrupt)
result = agent.invoke(
    {"messages": [{"role": "user", "content": user_input}]},
    config=config,
)

# Check if interrupted
if result.get("interrupted"):
    # Present to user, get decision
    decision = get_user_decision(result["interrupt_info"])

    # Resume with decision
    result = agent.invoke(
        Command(resume={"decision": decision}),
        config=config,
    )
```

## Confidence-Based Escalation

For actions without hard interrupts, implement soft escalation based on agent confidence:

### Pattern: Confidence Threshold

```python
CONFIDENCE_THRESHOLDS = {
    "auto_execute": 0.9,    # Agent proceeds without asking
    "suggest_and_wait": 0.7, # Agent suggests, waits for confirmation
    "escalate": 0.5,         # Agent asks for guidance
    "refuse": 0.3,           # Agent declines to act
}
```

### Implementation in System Prompt

Add to Layer 2 (Instructions):

```
### Confidence-Based Actions

Before taking any action that modifies state:

1. Assess your confidence (0.0-1.0) in the action being correct.
2. If confidence >= 0.9: Execute and briefly explain what you did.
3. If confidence 0.7-0.9: Propose the action and ask "Should I proceed?"
4. If confidence 0.5-0.7: Explain your uncertainty and ask for guidance.
5. If confidence < 0.5: State that you're unsure and ask the user to clarify.

Always show your confidence assessment when it's below 0.9.
```

## Escalation Patterns

### Pattern 1: Graduated Escalation

```
Low confidence → Ask clarifying question
Still unsure  → Present 2-3 options with trade-offs
User chooses  → Execute and confirm
```

### Pattern 2: Proactive Confirmation

For batch operations (e.g., updating multiple memory blocks):

```
Agent: "Based on our conversation, I'd like to update 3 memory blocks:
1. user_profile: Add 'prefers bullet points'
2. working_context: Update current project to 'sentient-agent'
3. learnings: Add 'FalkorDB preferred over Neo4j'

Should I proceed with all 3, or would you like to review each one?"
```

### Pattern 3: Audit Trail

Every human-approved action should be logged:

```python
@observe(name="human-approved-action")
def execute_approved_action(action, decision, user_id):
    langfuse = get_client()

    langfuse.update_current_trace(
        metadata={
            "action": action,
            "decision": decision,
            "approved_by": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    return execute_action(action)
```

## Common Mistakes

| Mistake | Impact | Fix |
|---|---|---|
| Requiring approval for everything | User fatigue, agent feels useless | Only interrupt on high-stakes/irreversible |
| No approval for destructive actions | Accidental data loss | Always interrupt on deletes |
| Binary approve/reject | User has no way to modify | Include "edit" option |
| No explanation in interrupt | User can't make informed decision | Always include context and rationale |
| No audit trail | Can't review past decisions | Log all approved actions via LangFuse |
