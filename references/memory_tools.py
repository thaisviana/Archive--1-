from langchain_core.tools import tool
from references.sqlalchemy_models import MemoryBlock, BlockHistory, get_session


def _check_writable(block):
    """Return error string if block is read-only, None otherwise."""
    if block.read_only:
        return f"Error: Memory block '{block.label}' is read-only and cannot be edited at runtime."
    return None


@tool
def insert_memory_block(label: str, new_str: str, insert_line: int) -> str:
    """Insert a string into a memory block at a specific line number.

    Args:
        label: The label of the memory block to modify
        new_str: The text to insert
        insert_line: The line number to insert at (1-indexed)

    Returns:
        Confirmation message with the updated block content
    """
    session = get_session()
    block = session.query(MemoryBlock).filter_by(label=label).first()
    if not block:
        return f"Error: Memory block '{label}' not found."
    if err := _check_writable(block):
        return err

    session.add(BlockHistory(block_id=block.id, content=block.content))
    lines = block.content.split("\n")
    lines.insert(max(0, insert_line - 1), new_str)
    block.content = "\n".join(lines)
    session.commit()
    return f"Inserted text at line {insert_line} in '{label}'. Current content:\n{block.content}"


@tool
def replace_memory_content(label: str, old_str: str, new_str: str) -> str:
    """Replace a specific string in a memory block.

    Args:
        label: The label of the memory block to modify
        old_str: The exact text to find and replace
        new_str: The replacement text

    Returns:
        Confirmation message with the updated block content
    """
    session = get_session()
    block = session.query(MemoryBlock).filter_by(label=label).first()
    if not block:
        return f"Error: Memory block '{label}' not found."
    if err := _check_writable(block):
        return err
    if old_str not in block.content:
        return f"Error: '{old_str}' not found in block '{label}'."

    session.add(BlockHistory(block_id=block.id, content=block.content))
    block.content = block.content.replace(old_str, new_str, 1)
    session.commit()
    return f"Replaced text in '{label}'. Current content:\n{block.content}"


@tool
def rethink_memory_block(label: str, new_content: str) -> str:
    """Rewrite the entire content of a memory block. Use when the block needs a complete overhaul.

    Args:
        label: The label of the memory block to rewrite
        new_content: The new complete content for the block

    Returns:
        Confirmation message with the new block content
    """
    session = get_session()
    block = session.query(MemoryBlock).filter_by(label=label).first()
    if not block:
        return f"Error: Memory block '{label}' not found."
    if err := _check_writable(block):
        return err

    session.add(BlockHistory(block_id=block.id, content=block.content))
    block.content = new_content
    session.commit()
    return f"Rewrote block '{label}'. New content:\n{block.content}"


@tool
def finish_memory_edits() -> str:
    """Signal that a batch of memory edits is complete. Call this after making multiple memory changes.

    Returns:
        Confirmation that memory edits are finalized
    """
    return "Memory edits finalized. All changes have been persisted with version history."


@tool
def create_memory_block(label: str, content: str) -> str:
    """Create a new labeled memory block. Use for entirely new topics.

    Args:
        label: A unique, descriptive label for the new block (snake_case)
        content: The initial content of the block

    Returns:
        Confirmation message with the new block details
    """
    session = get_session()
    existing = session.query(MemoryBlock).filter_by(label=label).first()
    if existing:
        return f"Error: Memory block '{label}' already exists. Use rethink_memory_block to update it."

    block = MemoryBlock(label=label, content=content)
    session.add(block)
    session.commit()
    return f"Created new memory block '{label}' with content:\n{content}"


@tool
def delete_memory_block(label: str) -> str:
    """Delete a memory block permanently. This action requires human approval.

    Args:
        label: The label of the memory block to delete

    Returns:
        Confirmation of deletion
    """
    session = get_session()
    block = session.query(MemoryBlock).filter_by(label=label).first()
    if not block:
        return f"Error: Memory block '{label}' not found."
    if err := _check_writable(block):
        return err

    session.delete(block)
    session.commit()
    return f"Deleted memory block '{label}' and all its history."


@tool
def rename_memory_block(old_label: str, new_label: str) -> str:
    """Rename an existing memory block.

    Args:
        old_label: The current label of the block
        new_label: The new label (must be unique, snake_case)

    Returns:
        Confirmation of the rename
    """
    session = get_session()
    block = session.query(MemoryBlock).filter_by(label=old_label).first()
    if not block:
        return f"Error: Memory block '{old_label}' not found."
    if err := _check_writable(block):
        return err

    existing = session.query(MemoryBlock).filter_by(label=new_label).first()
    if existing:
        return f"Error: Memory block '{new_label}' already exists."

    block.label = new_label
    session.commit()
    return f"Renamed memory block from '{old_label}' to '{new_label}'."


@tool
def view_memory_blocks(label: str = None) -> str:
    """View all memory blocks or a specific one.

    Args:
        label: Optional - view a specific block. If None, shows all blocks.

    Returns:
        Formatted memory block contents
    """
    session = get_session()

    if label:
        block = session.query(MemoryBlock).filter_by(label=label).first()
        if not block:
            return f"Error: Memory block '{label}' not found."
        return f"<memory_block label=\"{block.label}\">\n{block.content}\n</memory_block>"

    blocks = session.query(MemoryBlock).all()
    if not blocks:
        return "No memory blocks found."

    result = []
    for block in blocks:
        result.append(f"<memory_block label=\"{block.label}\">\n{block.content}\n</memory_block>")
    return "\n\n".join(result)
