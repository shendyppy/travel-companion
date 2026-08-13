"""
Tool package.

Tool modules are imported here purely so their decorators run and the tools get
registered. Adding a new tool means creating the module and adding it below.
"""

from src.tools import destinations, flights, places  # noqa: F401  (side effect: registration)
from src.tools.registry import dispatch, names, schemas, tool

__all__ = ["dispatch", "names", "schemas", "tool"]
