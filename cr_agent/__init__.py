"""Core package for cr-agent."""

from __future__ import annotations

import importlib
from typing import Any

__all__ = ["models"]


def __getattr__(name: str) -> Any:
    if name == "models":
        module = importlib.import_module(".models", __name__)
        globals()[name] = module
        return module
    raise AttributeError(name)
