"""Configuration for CodeGuard Agent."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """Global configuration."""

    # Anthropic API
    api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    model: str = "claude-sonnet-4-6"  # Default model for agents
    thinking_model: str = "claude-opus-4-7"  # For complex reasoning tasks

    # Agent settings
    max_tokens: int = 8192
    temperature: float = 0.1  # Low temp for code analysis consistency

    # Project paths
    target_path: str = "."

    # Refactoring thresholds
    max_function_length: int = 50  # lines
    max_complexity: int = 10  # cyclomatic complexity
    max_nesting_depth: int = 4

    # Output
    verbose: bool = False
    output_format: str = "terminal"  # terminal, json, markdown

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


# Global singleton
config = Config()
