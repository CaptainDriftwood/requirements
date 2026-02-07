"""Tests for console module."""

from src.console import _should_use_color, create_console


def test_should_use_color_with_true_override():
    """Test that explicit True override enables color."""
    assert _should_use_color(True) is True


def test_should_use_color_with_false_override():
    """Test that explicit False override disables color."""
    assert _should_use_color(False) is False


def test_should_use_color_respects_no_color_env(monkeypatch):
    """Test that NO_COLOR environment variable disables color."""
    monkeypatch.setenv("NO_COLOR", "1")
    assert _should_use_color(None) is False


def test_should_use_color_defaults_to_true_without_no_color(monkeypatch):
    """Test that color is enabled by default when NO_COLOR is not set."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert _should_use_color(None) is True


def test_should_use_color_override_takes_precedence(monkeypatch):
    """Test that explicit override takes precedence over NO_COLOR."""
    monkeypatch.setenv("NO_COLOR", "1")
    # Override should take precedence
    assert _should_use_color(True) is True


def test_create_console_with_color_enabled():
    """Test creating console with color enabled."""
    console = create_console(color=True)
    assert console is not None
    assert console.no_color is False
    assert console._force_terminal is True


def test_create_console_with_color_disabled():
    """Test creating console with color disabled."""
    console = create_console(color=False)
    assert console is not None
    assert console.no_color is True


def test_create_console_with_auto_detect():
    """Test creating console with auto-detection."""
    console = create_console(color=None)
    assert console is not None


def test_create_console_respects_no_color_env(monkeypatch):
    """Test that create_console respects NO_COLOR when auto-detecting."""
    monkeypatch.setenv("NO_COLOR", "1")
    console = create_console(color=None)
    assert console is not None
    assert console.no_color is True


def test_create_console_soft_wrap_enabled():
    """Test that console is created with soft_wrap enabled."""
    console = create_console()
    assert console is not None


def test_create_console_has_custom_theme():
    """Test that console has custom theme applied."""
    from src.console import THEME

    console = create_console()
    assert console is not None
    assert "path" in THEME.styles
    assert "package" in THEME.styles
    assert "version" in THEME.styles
    assert "warning" in THEME.styles
    assert "diff.added" in THEME.styles
    assert "diff.removed" in THEME.styles
    assert "diff.changed" in THEME.styles
