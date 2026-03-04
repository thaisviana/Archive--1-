"""
Agent initialization and singleton management.

This module centralizes agent instantiation to ensure a single instance
is used across the application, avoiding redundant initialization costs.
"""

from references.agent_assembly import assemble_agent as _assemble_agent

# Global instance
_instance = None
_workspace_dir = "./workspace"


def initialize_agent(workspace_dir: str = "./workspace"):
    """
    Initialize agent with a specific workspace directory.
    
    Call this once at startup if you need a custom workspace.
    Safe to call multiple times - only returns the existing instance if already initialized.
    
    Args:
        workspace_dir: Path to workspace directory. Defaults to "./workspace"
    
    Returns:
        The initialized agent instance
    """
    global _instance, _workspace_dir
    
    if _instance is not None:
        return _instance
    
    _workspace_dir = workspace_dir
    _instance = _assemble_agent(workspace_dir=workspace_dir)
    return _instance


def get_agent():
    """
    Get the agent instance, initializing it if necessary (lazy initialization).
    
    Returns:
        The agent instance
    """
    global _instance
    
    if _instance is None:
        _instance = _assemble_agent(workspace_dir=_workspace_dir)
    
    return _instance


def reset_agent():
    """
    Reset the agent instance. Useful for testing.
    
    After calling this, the next get_agent() call will create a fresh instance.
    """
    global _instance
    _instance = None
