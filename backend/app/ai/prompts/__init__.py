"""Prompt template storage and loader for AccessGuard AI agent workflows."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load prompt template text by name (e.g. 'finding_analysis_v1')."""
    filename = f"{name}.txt" if not name.endswith(".txt") else name
    filepath = PROMPTS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Prompt template not found: {filename}")
    return filepath.read_text(encoding="utf-8").strip()


__all__ = ["PROMPTS_DIR", "load_prompt"]
