"""Agent package: the tool-calling loop and the persona."""

from src.agent.loop import AgentEvent, Turn, run
from src.agent.persona import system_prompt

__all__ = ["AgentEvent", "Turn", "run", "system_prompt"]
