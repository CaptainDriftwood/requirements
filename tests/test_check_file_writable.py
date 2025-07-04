import tempfile
from pathlib import Path

from src.main import check_file_writable


def test_check_file_writable_preview_mode():
    """Test that check_file_writable returns True when preview=True."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile() as temp_file:
        file_path = Path(temp_file.name)
        
        # Should return True regardless of file permissions when preview=True
        result = check_file_writable(file_path, preview=True)
        assert result is True


def test_check_file_writable_normal_mode():
    """Test that check_file_writable works correctly in normal mode."""
    # Create a temporary file that should be writable
    with tempfile.NamedTemporaryFile() as temp_file:
        file_path = Path(temp_file.name)
        
        # Should return True for writable file in normal mode
        result = check_file_writable(file_path, preview=False)
        assert result is True


def test_check_file_writable_read_only_file(tmp_path, capsys):
    """Test that check_file_writable returns False for read-only files."""
    # Create a read-only file
    file_path = tmp_path / "readonly.txt"
    file_path.write_text("test content")
    file_path.chmod(0o444)  # Make it read-only
    
    # Should return False and print warning for read-only file
    result = check_file_writable(file_path, preview=False)
    assert result is False
    
    # Check that warning was printed to stderr
    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert "read-only" in captured.err
    assert str(file_path) in captured.err