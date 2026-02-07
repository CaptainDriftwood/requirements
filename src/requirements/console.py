"""Console output module with configurable color support.

This module provides centralized console output handling with support for:
- User-configurable colors via --color/--no-color flags
- User config file settings (~/.requirements/config.toml)
- Automatic NO_COLOR environment variable detection
- Consistent styling across the CLI
"""

from __future__ import annotations

import os

from rich.console import Console
from rich.theme import Theme

from requirements.config import get_color_setting

# Custom theme for consistent styling
THEME = Theme(
    {
        "warning": "yellow",
        "path": "cyan bold",
        "package": "green bold",
        "version": "green",
        "diff.added": "green",
        "diff.removed": "red",
    }
)


def _should_use_color(color_override: bool | None = None) -> bool:
    """Determine if color output should be used.

    Priority order:
    1. Explicit override from --color/--no-color flags
    2. NO_COLOR environment variable (if set, disables color)
    3. User config file (~/.requirements/config.toml)
    4. Default to auto-detection by rich

    Args:
        color_override: Explicit color setting from CLI flags.
            True = force color, False = no color, None = auto-detect.

    Returns:
        True if color should be enabled, False otherwise.
    """
    if color_override is not None:
        return color_override

    # NO_COLOR convention: https://no-color.org/
    # If NO_COLOR exists (regardless of value), disable color
    if "NO_COLOR" in os.environ:
        return False

    config_color = get_color_setting()
    if config_color is not None:
        return config_color

    # Default to auto-detection (enabled)
    return True


def create_console(color: bool | None = None) -> Console:
    """Create a Console instance with the appropriate color settings.

    Args:
        color: Color mode setting.
            True = force color on
            False = force color off
            None = auto-detect (respects NO_COLOR env var and config file)

    Returns:
        Configured Console instance.
    """
    force_terminal = None
    no_color = False

    if color is True:
        force_terminal = True
    elif color is False or not _should_use_color():
        no_color = True

    return Console(
        theme=THEME,
        force_terminal=force_terminal,
        no_color=no_color,
        soft_wrap=True,  # Don't hard-wrap text, let terminal handle it
    )
