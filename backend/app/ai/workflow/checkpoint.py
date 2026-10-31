"""LangGraph workflow checkpointer provider for human approval state persistence."""

from langgraph.checkpoint.memory import MemorySaver

_shared_checkpointer: MemorySaver | None = None


def get_workflow_checkpointer() -> MemorySaver:
    """Return the shared in-memory checkpointer for LangGraph state persistence."""
    global _shared_checkpointer
    if _shared_checkpointer is None:
        _shared_checkpointer = MemorySaver()
    return _shared_checkpointer


def reset_workflow_checkpointer() -> None:
    """Reset the checkpointer state (primarily for isolated test fixtures)."""
    global _shared_checkpointer
    _shared_checkpointer = MemorySaver()
