import pathlib

from click.testing import CliRunner

from src.main import (
    add_package,
    cat_requirements,
    find_package,
    gather_requirements_files,
    remove_package,
    sort_requirements,
    update_package,
)


class TestGatherRequirementsFilesValidation:
    """Test file existence validation in gather_requirements_files function"""

    def test_nonexistent_path(self, capsys):
        """Test handling of non-existent paths"""
        nonexistent_path = pathlib.Path("/this/path/does/not/exist")
        result = gather_requirements_files([nonexistent_path])

        assert result == []
        captured = capsys.readouterr()
        assert "Error: Path '/this/path/does/not/exist' does not exist" in captured.err

    def test_wrong_filename(self, tmp_path, capsys):
        """Test handling of files that aren't named requirements.txt"""
        wrong_file = tmp_path / "dependencies.txt"
        wrong_file.write_text("requests==2.26.0\n")

        result = gather_requirements_files([wrong_file])

        assert result == []
        captured = capsys.readouterr()
        assert (
            "is not a requirements.txt file (found: dependencies.txt)" in captured.err
        )

    def test_valid_requirements_file(self, tmp_path):
        """Test handling of valid requirements.txt file"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.26.0\n")

        result = gather_requirements_files([req_file])

        assert result == [req_file]

    def test_directory_with_no_requirements_files(self, tmp_path, capsys):
        """Test handling of directory with no requirements.txt files"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = gather_requirements_files([empty_dir])

        assert result == []
        captured = capsys.readouterr()
        assert (
            f"Warning: No requirements.txt files found in directory '{empty_dir}'"
            in captured.err
        )

    def test_directory_with_requirements_files(self, tmp_path):
        """Test handling of directory with requirements.txt files"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.26.0\n")

        result = gather_requirements_files([tmp_path])

        assert req_file in result

    def test_mixed_valid_and_invalid_paths(self, tmp_path, capsys):
        """Test handling mix of valid and invalid paths"""
        # Valid file
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.26.0\n")

        # Invalid file
        wrong_file = tmp_path / "dependencies.txt"
        wrong_file.write_text("django==3.2.0\n")

        # Non-existent path
        nonexistent_path = tmp_path / "nonexistent"

        result = gather_requirements_files([req_file, wrong_file, nonexistent_path])

        assert result == [req_file]
        captured = capsys.readouterr()
        assert "is not a requirements.txt file" in captured.err
        assert "does not exist" in captured.err

    def test_venv_exclusion_still_works(self, tmp_path):
        """Test that virtual environment exclusion still works"""
        # Create a venv directory with requirements.txt
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        venv_req = venv_dir / "requirements.txt"
        venv_req.write_text("should-be-excluded==1.0.0\n")

        # Create a normal requirements.txt
        normal_req = tmp_path / "requirements.txt"
        normal_req.write_text("should-be-included==1.0.0\n")

        result = gather_requirements_files([tmp_path])

        assert normal_req in result
        assert venv_req not in result


class TestCommandFileValidation:
    """Test that all commands handle missing files gracefully"""

    def test_find_command_nonexistent_file(self, cli_runner: CliRunner):
        """Test find command with non-existent file"""
        result = cli_runner.invoke(find_package, ["django", "/nonexistent/path"])

        assert result.exit_code == 0  # Should not crash
        assert "Error: Path '/nonexistent/path' does not exist" in result.output

    def test_add_command_nonexistent_file(self, cli_runner: CliRunner):
        """Test add command with non-existent file"""
        result = cli_runner.invoke(add_package, ["django", "/nonexistent/path"])

        assert result.exit_code == 0  # Should not crash
        assert "Error: Path '/nonexistent/path' does not exist" in result.output

    def test_remove_command_nonexistent_file(self, cli_runner: CliRunner):
        """Test remove command with non-existent file"""
        result = cli_runner.invoke(remove_package, ["django", "/nonexistent/path"])

        assert result.exit_code == 0  # Should not crash
        assert "Error: Path '/nonexistent/path' does not exist" in result.output

    def test_update_command_nonexistent_file(self, cli_runner: CliRunner):
        """Test update command with non-existent file"""
        result = cli_runner.invoke(
            update_package, ["django", "4.2.0", "/nonexistent/path"]
        )

        assert result.exit_code == 0  # Should not crash
        assert "Error: Path '/nonexistent/path' does not exist" in result.output

    def test_sort_command_nonexistent_file(self, cli_runner: CliRunner):
        """Test sort command with non-existent file"""
        result = cli_runner.invoke(sort_requirements, ["/nonexistent/path"])

        assert result.exit_code == 0  # Should not crash
        assert "Error: Path '/nonexistent/path' does not exist" in result.output

    def test_cat_command_nonexistent_file(self, cli_runner: CliRunner):
        """Test cat command with non-existent file"""
        result = cli_runner.invoke(cat_requirements, ["/nonexistent/path"])

        assert result.exit_code == 0  # Should not crash
        assert "Error: Path '/nonexistent/path' does not exist" in result.output

    def test_wrong_filename_error_messages(self, cli_runner: CliRunner, tmp_path):
        """Test clear error messages for wrong filenames"""
        wrong_file = tmp_path / "dependencies.txt"
        wrong_file.write_text("requests==2.26.0\n")

        result = cli_runner.invoke(find_package, ["django", str(wrong_file)])

        assert result.exit_code == 0
        assert (
            "is not a requirements.txt file (found: dependencies.txt)" in result.output
        )

    def test_empty_directory_warning(self, cli_runner: CliRunner, tmp_path):
        """Test warning for empty directories"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = cli_runner.invoke(find_package, ["django", str(empty_dir)])

        assert result.exit_code == 0
        assert (
            f"Warning: No requirements.txt files found in directory '{empty_dir}'"
            in result.output
        )


class TestEdgeCases:
    """Test edge cases in file validation"""

    def test_file_deleted_between_glob_and_access(self, tmp_path, monkeypatch):
        """Test handling of files deleted between directory scan and file access"""
        # Create a requirements.txt file
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.26.0\n")

        # Mock pathlib.Path.glob to return the file, but Path.exists to return False
        original_glob = pathlib.Path.glob
        original_exists = pathlib.Path.exists

        def mock_glob(self, pattern):
            return original_glob(self, pattern)

        def mock_exists(self):
            if self.name == "requirements.txt":
                return False  # Simulate file was deleted
            return original_exists(self)

        monkeypatch.setattr(pathlib.Path, "glob", mock_glob)
        monkeypatch.setattr(pathlib.Path, "exists", mock_exists)

        # This should handle the case gracefully
        result = gather_requirements_files([tmp_path])
        assert result == []

    def test_symlink_handling(self, tmp_path):
        """Test handling of symlinks"""
        # Create a real requirements.txt file
        real_file = tmp_path / "real_requirements.txt"
        real_file.write_text("requests==2.26.0\n")

        # Create a symlink to it named requirements.txt
        symlink_file = tmp_path / "requirements.txt"
        symlink_file.symlink_to(real_file)

        result = gather_requirements_files([symlink_file])

        # Should work with symlinks
        assert result == [symlink_file]

    def test_broken_symlink_handling(self, tmp_path, capsys):
        """Test handling of broken symlinks"""
        # Create a symlink to a non-existent file
        broken_symlink = tmp_path / "requirements.txt"
        broken_symlink.symlink_to(tmp_path / "nonexistent.txt")

        result = gather_requirements_files([broken_symlink])

        # Should detect that the symlink target doesn't exist
        assert result == []
        # Note: Path.exists() returns False for broken symlinks
