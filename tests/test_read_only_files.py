import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from src.main import cli


class TestReadOnlyFiles(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner(mix_stderr=False)
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
    def tearDown(self):
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_requirements_file(self, filename: str, content: str, read_only: bool = False):
        """Create a requirements.txt file with given content, optionally read-only"""
        file_path = self.temp_path / filename
        file_path.write_text(content)
        
        if read_only:
            # Make file read-only
            os.chmod(file_path, 0o444)
        
        return file_path
    
    def test_update_all_files_read_only(self):
        """Test update command when all files are read-only"""
        # Create read-only files (must be named requirements.txt for gather_requirements_files to find them)
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("django==3.0\nrequests==2.25.1\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("flask==1.1.4\nrequests==2.25.1\n")
        os.chmod(file2, 0o444)
        
        result = self.runner.invoke(cli, ["update", "requests", "2.30.0", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should show warning messages for read-only files
        self.assertIn("Warning:", result.stderr)
        self.assertIn("read-only", result.stderr)
        
        # Files should remain unchanged
        self.assertEqual(file1.read_text(), "django==3.0\nrequests==2.25.1\n")
        self.assertEqual(file2.read_text(), "flask==1.1.4\nrequests==2.25.1\n")
    
    def test_update_subset_files_read_only(self):
        """Test update command when subset of files are read-only"""
        # Create mixed files - one read-only, one writable
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("django==3.0\nrequests==2.25.1\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("flask==1.1.4\nrequests==2.25.1\n")
        
        result = self.runner.invoke(cli, ["update", "requests", "2.30.0", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should show warning for read-only file only
        self.assertIn("Warning:", result.stderr)
        self.assertIn("read-only", result.stderr)
        
        # Should show success message for writable file
        self.assertIn("Updated", result.stdout)
        
        # Read-only file should remain unchanged
        self.assertEqual(file1.read_text(), "django==3.0\nrequests==2.25.1\n")
        
        # Writable file should be updated
        updated_content = file2.read_text()
        self.assertIn("requests==2.30.0", updated_content)
    
    def test_update_preview_mode_no_warnings(self):
        """Test update command with --preview flag doesn't show read-only warnings"""
        # Create read-only files
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("django==3.0\nrequests==2.25.1\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("flask==1.1.4\nrequests==2.25.1\n")
        os.chmod(file2, 0o444)
        
        result = self.runner.invoke(cli, ["update", "requests", "2.30.0", "--preview", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should NOT show warning messages in preview mode
        self.assertNotIn("Warning:", result.stderr)
        self.assertNotIn("read-only", result.stderr)
        
        # Should show preview output
        self.assertIn("Previewing changes", result.stdout)
        
        # Files should remain unchanged
        self.assertEqual(file1.read_text(), "django==3.0\nrequests==2.25.1\n")
        self.assertEqual(file2.read_text(), "flask==1.1.4\nrequests==2.25.1\n")
    
    def test_add_all_files_read_only(self):
        """Test add command when all files are read-only"""
        # Create read-only files
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("django==3.0\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("flask==1.1.4\n")
        os.chmod(file2, 0o444)
        
        result = self.runner.invoke(cli, ["add", "pytest", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should show warning messages for read-only files
        self.assertIn("Warning:", result.stderr)
        self.assertIn("read-only", result.stderr)
        
        # Files should remain unchanged
        self.assertEqual(file1.read_text(), "django==3.0\n")
        self.assertEqual(file2.read_text(), "flask==1.1.4\n")
    
    def test_add_subset_files_read_only(self):
        """Test add command when subset of files are read-only"""
        # Create mixed files - one read-only, one writable
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("django==3.0\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("flask==1.1.4\n")
        
        result = self.runner.invoke(cli, ["add", "pytest", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should show warning for read-only file only
        self.assertIn("Warning:", result.stderr)
        self.assertIn("read-only", result.stderr)
        
        # Should show success message for writable file
        self.assertIn("Updated", result.stdout)
        
        # Read-only file should remain unchanged
        self.assertEqual(file1.read_text(), "django==3.0\n")
        
        # Writable file should be updated
        updated_content = file2.read_text()
        self.assertIn("pytest", updated_content)
    
    def test_add_preview_mode_no_warnings(self):
        """Test add command with --preview flag doesn't show read-only warnings"""
        # Create read-only files
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("django==3.0\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("flask==1.1.4\n")
        os.chmod(file2, 0o444)
        
        result = self.runner.invoke(cli, ["add", "pytest", "--preview", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should NOT show warning messages in preview mode
        self.assertNotIn("Warning:", result.stderr)
        self.assertNotIn("read-only", result.stderr)
        
        # Should show preview output
        self.assertIn("Previewing changes", result.stdout)
        
        # Files should remain unchanged
        self.assertEqual(file1.read_text(), "django==3.0\n")
        self.assertEqual(file2.read_text(), "flask==1.1.4\n")
    
    def test_remove_all_files_read_only(self):
        """Test remove command when all files are read-only"""
        # Create read-only files
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("django==3.0\nrequests==2.25.1\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("flask==1.1.4\nrequests==2.25.1\n")
        os.chmod(file2, 0o444)
        
        result = self.runner.invoke(cli, ["remove", "requests", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should show warning messages for read-only files
        self.assertIn("Warning:", result.stderr)
        self.assertIn("read-only", result.stderr)
        
        # Files should remain unchanged
        self.assertEqual(file1.read_text(), "django==3.0\nrequests==2.25.1\n")
        self.assertEqual(file2.read_text(), "flask==1.1.4\nrequests==2.25.1\n")
    
    def test_remove_subset_files_read_only(self):
        """Test remove command when subset of files are read-only"""
        # Create mixed files - one read-only, one writable
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("django==3.0\nrequests==2.25.1\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("flask==1.1.4\nrequests==2.25.1\n")
        
        result = self.runner.invoke(cli, ["remove", "requests", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should show warning for read-only file only
        self.assertIn("Warning:", result.stderr)
        self.assertIn("read-only", result.stderr)
        
        # Should show success message for writable file
        self.assertIn("Removed", result.stdout)
        
        # Read-only file should remain unchanged
        self.assertEqual(file1.read_text(), "django==3.0\nrequests==2.25.1\n")
        
        # Writable file should be updated (requests removed)
        updated_content = file2.read_text()
        self.assertNotIn("requests", updated_content)
        self.assertIn("flask==1.1.4", updated_content)
    
    def test_remove_preview_mode_no_warnings(self):
        """Test remove command with --preview flag doesn't show read-only warnings"""
        # Create read-only files
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("django==3.0\nrequests==2.25.1\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("flask==1.1.4\nrequests==2.25.1\n")
        os.chmod(file2, 0o444)
        
        result = self.runner.invoke(cli, ["remove", "requests", "--preview", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should NOT show warning messages in preview mode
        self.assertNotIn("Warning:", result.stderr)
        self.assertNotIn("read-only", result.stderr)
        
        # Should show preview output
        self.assertIn("Previewing changes", result.stdout)
        
        # Files should remain unchanged
        self.assertEqual(file1.read_text(), "django==3.0\nrequests==2.25.1\n")
        self.assertEqual(file2.read_text(), "flask==1.1.4\nrequests==2.25.1\n")
    
    def test_sort_all_files_read_only(self):
        """Test sort command when all files are read-only"""
        # Create read-only files with unsorted content
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("requests==2.25.1\ndjango==3.0\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("pytest==6.0\nflask==1.1.4\n")
        os.chmod(file2, 0o444)
        
        result = self.runner.invoke(cli, ["sort", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should show warning messages for read-only files
        self.assertIn("Warning:", result.stderr)
        self.assertIn("read-only", result.stderr)
        
        # Files should remain unchanged (unsorted)
        self.assertEqual(file1.read_text(), "requests==2.25.1\ndjango==3.0\n")
        self.assertEqual(file2.read_text(), "pytest==6.0\nflask==1.1.4\n")
    
    def test_sort_subset_files_read_only(self):
        """Test sort command when subset of files are read-only"""
        # Create mixed files - one read-only, one writable, both unsorted
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("requests==2.25.1\ndjango==3.0\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("pytest==6.0\nflask==1.1.4\n")
        
        result = self.runner.invoke(cli, ["sort", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should show warning for read-only file only
        self.assertIn("Warning:", result.stderr)
        self.assertIn("read-only", result.stderr)
        
        # Should show success message for writable file
        self.assertIn("Sorted", result.stdout)
        
        # Read-only file should remain unchanged (unsorted)
        self.assertEqual(file1.read_text(), "requests==2.25.1\ndjango==3.0\n")
        
        # Writable file should be sorted
        updated_content = file2.read_text()
        lines = updated_content.strip().split('\n')
        self.assertEqual(lines[0], "flask==1.1.4")
        self.assertEqual(lines[1], "pytest==6.0")
    
    def test_sort_preview_mode_no_warnings(self):
        """Test sort command with --preview flag doesn't show read-only warnings"""
        # Create read-only files with unsorted content
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("requests==2.25.1\ndjango==3.0\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("pytest==6.0\nflask==1.1.4\n")
        os.chmod(file2, 0o444)
        
        result = self.runner.invoke(cli, ["sort", "--preview", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should NOT show warning messages in preview mode
        self.assertNotIn("Warning:", result.stderr)
        self.assertNotIn("read-only", result.stderr)
        
        # Should show preview output
        self.assertIn("Previewing changes", result.stdout)
        
        # Files should remain unchanged
        self.assertEqual(file1.read_text(), "requests==2.25.1\ndjango==3.0\n")
        self.assertEqual(file2.read_text(), "pytest==6.0\nflask==1.1.4\n")
    
    def test_find_read_only_files_no_warnings(self):
        """Test find command with read-only files doesn't show warnings (read-only operation)"""
        # Create read-only files
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("django==3.0\nrequests==2.25.1\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("flask==1.1.4\nrequests==2.25.1\n")
        os.chmod(file2, 0o444)
        
        result = self.runner.invoke(cli, ["find", "requests", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should NOT show warning messages (find is read-only)
        self.assertNotIn("Warning:", result.stderr)
        self.assertNotIn("read-only", result.stderr)
        
        # Should show found files
        self.assertIn("requirements.txt", result.stdout)
    
    def test_cat_read_only_files_no_warnings(self):
        """Test cat command with read-only files doesn't show warnings (read-only operation)"""
        # Create read-only files
        subdir1 = self.temp_path / "project1"
        subdir1.mkdir()
        subdir2 = self.temp_path / "project2"
        subdir2.mkdir()
        
        file1 = subdir1 / "requirements.txt"
        file1.write_text("django==3.0\nrequests==2.25.1\n")
        os.chmod(file1, 0o444)
        
        file2 = subdir2 / "requirements.txt"
        file2.write_text("flask==1.1.4\nrequests==2.25.1\n")
        os.chmod(file2, 0o444)
        
        result = self.runner.invoke(cli, ["cat", str(self.temp_path)])
        
        # Should complete without crashing
        self.assertEqual(result.exit_code, 0)
        
        # Should NOT show warning messages (cat is read-only)
        self.assertNotIn("Warning:", result.stderr)
        self.assertNotIn("read-only", result.stderr)
        
        # Should show file contents
        self.assertIn("django==3.0", result.stdout)
        self.assertIn("flask==1.1.4", result.stdout)


if __name__ == "__main__":
    unittest.main()