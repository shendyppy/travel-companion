"""Agent package: the tool-calling loop, the persona, and seeded tool calls."""

from src.agent.loop import AgentEvent, Turn, run
from src.agent.persona import system_prompt
from src.agent.seed import SEEDABLE, Seed, parse as parse_seed

__all__ = ["AgentEvent", "SEEDABLE", "Seed", "Turn", "parse_seed", "run", "system_prompt"]
