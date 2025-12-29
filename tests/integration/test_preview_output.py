from src.main import cli


def test_update_preview_output_format(cli_runner, tmp_path, create_requirements_file):
    """Test that update command shows full file with unified diff-style output."""
    create_requirements_file(tmp_path, "project", "django==3.0\nrequests==2.25.1\n")

    result = cli_runner.invoke(
        cli, ["update", "requests", "2.30.0", "--preview", str(tmp_path)]
    )

    # Should show file path
    assert "requirements.txt" in result.stdout

    # Should show unchanged lines (with space prefix for alignment)
    assert "django==3.0" in result.stdout

    # Should show diff-style output with old and new version
    assert "-requests==2.25.1" in result.stdout
    assert "+requests==2.30.0" in result.stdout


def test_add_preview_output_format(cli_runner, tmp_path, create_requirements_file):
    """Test that add command shows full file with unified diff-style output."""
    create_requirements_file(tmp_path, "project", "django==3.0\n")

    result = cli_runner.invoke(cli, ["add", "pytest", "--preview", str(tmp_path)])

    # Should show file path
    assert "requirements.txt" in result.stdout

    # Should show existing lines
    assert "django==3.0" in result.stdout

    # Should show diff-style output with added package
    assert "+pytest" in result.stdout


def test_remove_preview_output_format(cli_runner, tmp_path, create_requirements_file):
    """Test that remove command shows full file with unified diff-style output."""
    create_requirements_file(tmp_path, "project", "django==3.0\nrequests==2.25.1\n")

    result = cli_runner.invoke(cli, ["remove", "requests", "--preview", str(tmp_path)])

    # Should show file path
    assert "requirements.txt" in result.stdout

    # Should show remaining lines
    assert "django==3.0" in result.stdout

    # Should show diff-style output with removed package
    assert "-requests==2.25.1" in result.stdout


def test_sort_preview_output_format(cli_runner, tmp_path, create_requirements_file):
    """Test that sort command shows full file with unified diff-style output."""
    create_requirements_file(tmp_path, "project", "requests==2.25.1\ndjango==3.0\n")

    result = cli_runner.invoke(cli, ["sort", "--preview", str(tmp_path)])

    # Should show file path
    assert "requirements.txt" in result.stdout

    # Should show the sorted file content (django before requests alphabetically)
    # The diff shows the reordering
    assert "django==3.0" in result.stdout
    assert "requests==2.25.1" in result.stdout


def test_all_preview_commands_consistent_format(
    cli_runner, tmp_path, create_requirements_file
):
    """Test that all preview commands use consistent output format."""
    create_requirements_file(tmp_path, "project", "requests==2.25.1\ndjango==3.0\n")

    # Test all commands that support preview
    commands = [
        ["update", "requests", "2.30.0", "--preview", str(tmp_path)],
        ["add", "pytest", "--preview", str(tmp_path)],
        ["remove", "requests", "--preview", str(tmp_path)],
        ["sort", "--preview", str(tmp_path)],
    ]

    for cmd in commands:
        result = cli_runner.invoke(cli, cmd)

        # All should show file path consistently
        assert "requirements.txt" in result.stdout, (
            f"Command {cmd[0]} missing file path"
        )

        # All should have successful exit code
        assert result.exit_code == 0, (
            f"Command {cmd[0]} failed with exit code {result.exit_code}"
        )


def test_preview_shows_full_file_context(
    cli_runner, tmp_path, create_requirements_file
):
    """Test that preview mode shows all lines, not just changed lines."""
    create_requirements_file(
        tmp_path, "project", "click==8.0.0\ndjango==3.0\nrequests==2.25.1\n"
    )

    result = cli_runner.invoke(
        cli, ["update", "django", "4.0.0", "--preview", str(tmp_path)]
    )

    # Should show all lines from the file
    assert "click==8.0.0" in result.stdout
    assert "requests==2.25.1" in result.stdout

    # Should show the change
    assert "-django==3.0" in result.stdout
    assert "+django==4.0.0" in result.stdout
