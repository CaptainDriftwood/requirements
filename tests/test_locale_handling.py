import locale
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from src.main import (
    _is_locale_available,
    cli,
    get_default_locale,
    get_system_locale,
    set_locale,
    sort_packages,
)


class TestLocaleDetection:
    """Test locale detection and fallback functionality"""

    def test_get_system_locale_with_available_default(self):
        """Test locale detection when system default is available"""
        with (
            patch("locale.getdefaultlocale") as mock_getdefault,
            patch("src.main._is_locale_available") as mock_available,
        ):
            mock_getdefault.return_value = ("en_US", "UTF-8")
            mock_available.side_effect = lambda x: x == "en_US.UTF-8"

            result = get_system_locale()
            assert result == "en_US.UTF-8"

    def test_get_system_locale_fallback_to_c_utf8(self):
        """Test fallback to C.UTF-8 when system default not available"""
        with (
            patch("locale.getdefaultlocale") as mock_getdefault,
            patch("src.main._is_locale_available") as mock_available,
        ):
            mock_getdefault.return_value = (None, None)
            mock_available.side_effect = lambda x: x == "C.UTF-8"

            result = get_system_locale()
            assert result == "C.UTF-8"

    def test_get_system_locale_fallback_to_posix(self):
        """Test fallback to POSIX when UTF-8 locales not available"""
        with (
            patch("locale.getdefaultlocale") as mock_getdefault,
            patch("src.main._is_locale_available") as mock_available,
        ):
            mock_getdefault.return_value = (None, None)
            mock_available.side_effect = lambda x: x == "POSIX"

            result = get_system_locale()
            assert result == "POSIX"

    def test_get_system_locale_no_available_locale(self):
        """Test when no suitable locale is found"""
        with (
            patch("locale.getdefaultlocale") as mock_getdefault,
            patch("src.main._is_locale_available") as mock_available,
        ):
            mock_getdefault.return_value = (None, None)
            mock_available.return_value = False

            result = get_system_locale()
            assert result is None

    def test_get_system_locale_adds_utf8_suffix(self):
        """Test that UTF-8 suffix is added to plain locale names"""
        with (
            patch("locale.getdefaultlocale") as mock_getdefault,
            patch("src.main._is_locale_available") as mock_available,
        ):
            mock_getdefault.return_value = ("de_DE", "UTF-8")
            mock_available.side_effect = lambda x: x == "de_DE.UTF-8"

            result = get_system_locale()
            assert result == "de_DE.UTF-8"

    def test_is_locale_available_success(self):
        """Test locale availability check when locale exists"""
        with (
            patch("locale.setlocale") as mock_setlocale,
            patch("locale.getlocale") as mock_getlocale,
        ):
            mock_getlocale.return_value = ("en_US", "UTF-8")
            mock_setlocale.return_value = None

            result = _is_locale_available("en_US.UTF-8")
            assert result is True

            # Verify locale was tested and restored
            assert mock_setlocale.call_count == 2

    def test_is_locale_available_failure(self):
        """Test locale availability check when locale doesn't exist"""
        with patch("locale.setlocale") as mock_setlocale:
            mock_setlocale.side_effect = locale.Error("locale not available")

            result = _is_locale_available("invalid_locale")
            assert result is False

    def test_is_locale_available_empty_string(self):
        """Test locale availability with empty string"""
        result = _is_locale_available("")
        assert result is False

    def test_get_default_locale_caching(self):
        """Test that system locale is cached after first detection"""
        # Clear the cache first
        import src.main

        src.main._SYSTEM_LOCALE = None

        with patch("src.main.get_system_locale") as mock_get_system:
            mock_get_system.return_value = "en_US.UTF-8"

            # First call should invoke detection
            result1 = get_default_locale()
            assert result1 == "en_US.UTF-8"
            assert mock_get_system.call_count == 1

            # Second call should use cache
            result2 = get_default_locale()
            assert result2 == "en_US.UTF-8"
            assert mock_get_system.call_count == 1  # No additional calls


class TestSetLocaleContextManager:
    """Test the set_locale context manager"""

    def test_set_locale_success(self):
        """Test successful locale setting"""
        with (
            patch("locale.setlocale") as mock_setlocale,
            patch("locale.getlocale") as mock_getlocale,
            patch("locale.strcoll") as mock_strcoll,
        ):
            mock_getlocale.return_value = ("en_US", "UTF-8")
            mock_strcoll.return_value = 0

            with set_locale("en_GB.UTF-8") as cmp_func:
                assert cmp_func == mock_strcoll

            # Verify locale was set and restored
            assert mock_setlocale.call_count == 2

    def test_set_locale_none(self):
        """Test set_locale with None locale"""
        with set_locale(None) as cmp_func:
            # Should get basic comparison function
            assert cmp_func("a", "b") == -1
            assert cmp_func("b", "a") == 1
            assert cmp_func("a", "a") == 0

    def test_set_locale_error_fallback(self):
        """Test graceful fallback when locale setting fails"""
        with patch("locale.setlocale") as mock_setlocale:
            mock_setlocale.side_effect = [
                ("en_US", "UTF-8"),  # getlocale call
                locale.Error("locale not available"),  # setlocale call
            ]

            with set_locale("invalid_locale") as cmp_func:
                # Should get fallback comparison function
                assert cmp_func("a", "b") == -1
                assert cmp_func("b", "a") == 1
                assert cmp_func("a", "a") == 0

    def test_set_locale_restore_failure(self):
        """Test when locale restoration fails"""
        with (
            patch("locale.setlocale") as mock_setlocale,
            patch("locale.getlocale") as mock_getlocale,
            patch("locale.strcoll") as mock_strcoll,
        ):
            mock_getlocale.return_value = ("en_US", "UTF-8")
            mock_setlocale.side_effect = [
                None,  # successful set
                locale.Error("restore failed"),  # failed restore
            ]

            # Should not raise exception
            with set_locale("en_GB.UTF-8") as cmp_func:
                assert cmp_func == mock_strcoll


class TestSortPackagesWithLocale:
    """Test sorting behavior with different locales"""

    def test_sort_packages_with_explicit_locale(self):
        """Test sorting with explicitly specified locale"""
        packages = ["zebra", "apple", "banana"]

        with patch("src.main.set_locale") as mock_set_locale:
            mock_set_locale.return_value.__enter__ = MagicMock(
                return_value=lambda a, b: (a > b) - (a < b)
            )
            mock_set_locale.return_value.__exit__ = MagicMock(return_value=None)

            result = sort_packages(
                packages, locale_="en_US.UTF-8", preserve_comments=False
            )

            mock_set_locale.assert_called_once_with("en_US.UTF-8")
            assert result == ["apple", "banana", "zebra"]

    def test_sort_packages_with_auto_detection(self):
        """Test sorting with automatic locale detection"""
        packages = ["zebra", "apple", "banana"]

        with (
            patch("src.main.get_default_locale") as mock_get_default,
            patch("src.main.set_locale") as mock_set_locale,
        ):
            mock_get_default.return_value = "en_US.UTF-8"
            mock_set_locale.return_value.__enter__ = MagicMock(
                return_value=lambda a, b: (a > b) - (a < b)
            )
            mock_set_locale.return_value.__exit__ = MagicMock(return_value=None)

            result = sort_packages(packages, locale_=None, preserve_comments=False)

            mock_get_default.assert_called_once()
            mock_set_locale.assert_called_once_with("en_US.UTF-8")
            assert result == ["apple", "banana", "zebra"]

    def test_sort_packages_with_comments_and_locale(self):
        """Test sorting with comment preservation and locale"""
        lines = [
            "# Web frameworks",
            "flask==2.0.0",
            "django==4.0.0",
            "",
            "# Data processing",
            "pandas==1.3.0",
            "numpy==1.21.0",
        ]

        with (
            patch("src.main.get_default_locale") as mock_get_default,
            patch("src.main.set_locale") as mock_set_locale,
        ):
            mock_get_default.return_value = "C.UTF-8"
            mock_set_locale.return_value.__enter__ = MagicMock(
                return_value=lambda a, b: (a > b) - (a < b)
            )
            mock_set_locale.return_value.__exit__ = MagicMock(return_value=None)

            result = sort_packages(lines, locale_=None)

            # Should preserve comments and sort packages within sections
            expected = [
                "# Web frameworks",
                "django==4.0.0",
                "flask==2.0.0",
                "",
                "# Data processing",
                "numpy==1.21.0",
                "pandas==1.3.0",
            ]
            assert result == expected


class TestCLILocaleParameter:
    """Test the --locale CLI parameter"""

    def test_cli_locale_parameter_help(self, cli_runner: CliRunner):
        """Test that --locale parameter appears in help"""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--locale" in result.output
        assert "Locale to use for sorting" in result.output

    def test_sort_command_with_locale_parameter(self, cli_runner: CliRunner, tmp_path):
        """Test sort command with --locale parameter"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("zebra==1.0.0\napple==2.0.0\nbanana==3.0.0\n")

        result = cli_runner.invoke(
            cli, ["--locale", "C", "sort", str(req_file), "--preview"]
        )
        assert result.exit_code == 0

        # Check that packages are sorted
        assert "apple==2.0.0" in result.output
        assert "banana==3.0.0" in result.output
        assert "zebra==1.0.0" in result.output

    def test_update_command_with_locale_parameter(
        self, cli_runner: CliRunner, tmp_path
    ):
        """Test update command with --locale parameter"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("zebra==1.0.0\napple==2.0.0\nbanana==3.0.0\n")

        result = cli_runner.invoke(
            cli,
            ["--locale", "C", "update", "apple", "2.1.0", str(req_file), "--preview"],
        )
        assert result.exit_code == 0
        assert "apple==2.1.0" in result.output

    def test_add_command_with_locale_parameter(self, cli_runner: CliRunner, tmp_path):
        """Test add command with --locale parameter"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("zebra==1.0.0\nbanana==3.0.0\n")

        result = cli_runner.invoke(
            cli, ["--locale", "C", "add", "apple", str(req_file), "--preview"]
        )
        assert result.exit_code == 0
        assert "apple" in result.output

    def test_remove_command_with_locale_parameter(
        self, cli_runner: CliRunner, tmp_path
    ):
        """Test remove command with --locale parameter"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("zebra==1.0.0\napple==2.0.0\nbanana==3.0.0\n")

        result = cli_runner.invoke(
            cli, ["--locale", "C", "remove", "apple", str(req_file), "--preview"]
        )
        assert result.exit_code == 0
        assert "apple" not in result.output
        assert "zebra==1.0.0" in result.output

    def test_invalid_locale_graceful_fallback(self, cli_runner: CliRunner, tmp_path):
        """Test that invalid locale falls back gracefully"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("zebra==1.0.0\napple==2.0.0\n")

        # Use an invalid locale - should fall back to ASCII sorting
        result = cli_runner.invoke(
            cli, ["--locale", "invalid_locale_xyz", "sort", str(req_file), "--preview"]
        )

        # Should still work (fall back to ASCII sorting)
        assert result.exit_code == 0
        assert "apple==2.0.0" in result.output
        assert "zebra==1.0.0" in result.output


class TestLocaleErrorScenarios:
    """Test various locale-related error scenarios"""

    def test_locale_error_during_sorting(self):
        """Test handling of locale errors during sorting"""
        packages = ["zebra", "apple"]

        with patch("src.main.set_locale") as mock_set_locale:
            # Mock locale setting failure
            mock_set_locale.return_value.__enter__ = MagicMock(
                return_value=lambda a, b: (a > b) - (a < b)
            )
            mock_set_locale.return_value.__exit__ = MagicMock(return_value=None)

            # Should not raise exception, should fall back gracefully
            result = sort_packages(packages, locale_="invalid", preserve_comments=False)
            assert result == ["apple", "zebra"]

    def test_system_without_utf8_locales(self):
        """Test behavior on systems without UTF-8 locale support"""
        with patch("src.main._is_locale_available") as mock_available:
            # Simulate system where only C/POSIX locales are available
            mock_available.side_effect = lambda x: x in ("C", "POSIX")

            result = get_system_locale()
            assert result in ("C", "POSIX")

    def test_completely_broken_locale_system(self):
        """Test behavior when locale system is completely broken"""
        with patch("src.main._is_locale_available") as mock_available:
            # Simulate system where no locales are available
            mock_available.return_value = False

            result = get_system_locale()
            assert result is None

            # Sorting should still work with ASCII fallback
            packages = ["zebra", "apple"]
            result = sort_packages(packages, locale_=None, preserve_comments=False)
            assert result == ["apple", "zebra"]
