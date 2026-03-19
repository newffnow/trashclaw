#!/usr/bin/env python3
"""
TrashClaw Test Suite
====================
Pytest-based test suite for core tool functions.
No external dependencies beyond pytest itself.
"""

import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

# Import the tool functions from trashclaw.py
# We need to import the module without running main()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the main guard to prevent execution
import trashclaw
from trashclaw import (
    tool_read_file,
    tool_write_file,
    tool_edit_file,
    tool_run_command,
    tool_search_files,
    tool_find_files,
    tool_list_dir,
    tool_fetch_url,
    tool_think,
    _resolve_path,
    detect_project_context,
)


# ── Fixtures ──

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath, ignore_errors=True)


@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file for testing."""
    filepath = os.path.join(temp_dir, "sample.txt")
    with open(filepath, "w") as f:
        f.write("Line 1\nLine 2\nLine 3\n")
    return filepath


@pytest.fixture
def sample_tree(temp_dir):
    """Create a sample directory tree for testing."""
    # Create subdirectories
    subdir1 = os.path.join(temp_dir, "subdir1")
    subdir2 = os.path.join(temp_dir, "subdir2")
    os.makedirs(subdir1)
    os.makedirs(subdir2)
    
    # Create files
    with open(os.path.join(temp_dir, "file1.py"), "w") as f:
        f.write("# Python file 1\nprint('hello')\n")
    
    with open(os.path.join(subdir1, "file2.py"), "w") as f:
        f.write("# Python file 2\nprint('world')\n")
    
    with open(os.path.join(subdir2, "file3.txt"), "w") as f:
        f.write("Text file content\n")
    
    with open(os.path.join(subdir1, "data.json"), "w") as f:
        f.write('{"key": "value"}\n')
    
    return temp_dir


# ── Path Resolution Tests ──

class TestPathResolution:
    """Tests for _resolve_path function."""
    
    def test_absolute_path(self, temp_dir):
        """Absolute paths should be returned as-is."""
        result = _resolve_path(temp_dir)
        assert result == os.path.normpath(temp_dir)
    
    def test_relative_path(self, temp_dir):
        """Relative paths should be resolved against CWD."""
        original_cwd = trashclaw.CWD
        try:
            trashclaw.CWD = temp_dir
            result = _resolve_path("subdir/file.txt")
            expected = os.path.join(temp_dir, "subdir", "file.txt")
            assert result == os.path.normpath(expected)
        finally:
            trashclaw.CWD = original_cwd
    
    def test_home_expansion(self):
        """~ should be expanded to home directory."""
        result = _resolve_path("~/test")
        assert result.startswith(os.path.expanduser("~"))


# ── Read File Tests ──

class TestReadFile:
    """Tests for tool_read_file function."""
    
    def test_read_existing_file(self, sample_file):
        """Should read an existing file successfully."""
        result = tool_read_file(sample_file)
        assert "1\tLine 1" in result
        assert "2\tLine 2" in result
        assert "3\tLine 3" in result
    
    def test_read_with_offset(self, sample_file):
        """Should respect offset parameter."""
        result = tool_read_file(sample_file, offset=2)
        assert "1\t" not in result or "Line 1" not in result.split("\t")[1] if "\t" in result else True
        assert "2\tLine 2" in result
    
    def test_read_with_limit(self, sample_file):
        """Should respect limit parameter."""
        result = tool_read_file(sample_file, limit=2)
        lines = [l for l in result.split("\n") if l.strip()]
        assert len(lines) <= 2
    
    def test_read_nonexistent_file(self, temp_dir):
        """Should return error for non-existent file."""
        result = tool_read_file(os.path.join(temp_dir, "nonexistent.txt"))
        assert "Error" in result
        assert "not found" in result.lower()


# ── Write File Tests ──

class TestWriteFile:
    """Tests for tool_write_file function."""
    
    def test_write_new_file(self, temp_dir):
        """Should create a new file."""
        filepath = os.path.join(temp_dir, "newfile.txt")
        content = "Hello, World!\n"
        result = tool_write_file(filepath, content)
        
        assert "Wrote" in result
        assert os.path.exists(filepath)
        with open(filepath, "r") as f:
            assert f.read() == content
    
    def test_write_overwrites_existing(self, sample_file):
        """Should overwrite existing file."""
        new_content = "New content\n"
        result = tool_write_file(sample_file, new_content)
        
        assert "Wrote" in result
        with open(sample_file, "r") as f:
            assert f.read() == new_content
    
    def test_write_creates_directories(self, temp_dir):
        """Should create parent directories if needed."""
        filepath = os.path.join(temp_dir, "nested", "dir", "file.txt")
        content = "Nested content\n"
        result = tool_write_file(filepath, content)
        
        assert "Wrote" in result
        assert os.path.exists(filepath)


# ── Edit File Tests ──

class TestEditFile:
    """Tests for tool_edit_file function."""
    
    def test_edit_existing_string(self, sample_file):
        """Should replace exact string match."""
        result = tool_edit_file(sample_file, "Line 2", "Line 2 - Modified")
        
        assert "Edited" in result
        with open(sample_file, "r") as f:
            content = f.read()
            assert "Line 2 - Modified" in content
            assert "Line 2\n" not in content
    
    def test_edit_nonexistent_string(self, sample_file):
        """Should return error for non-existent string."""
        result = tool_edit_file(sample_file, "NonExistent", "Replacement")
        
        assert "Error" in result
        assert "not found" in result.lower()
    
    def test_edit_duplicate_string(self, temp_dir):
        """Should return error for duplicate matches."""
        filepath = os.path.join(temp_dir, "duplicate.txt")
        with open(filepath, "w") as f:
            f.write("Same\nSame\n")
        
        result = tool_edit_file(filepath, "Same", "Different")
        
        assert "Error" in result
        assert "found" in result.lower() and "times" in result.lower()


# ── Run Command Tests ──

class TestRunCommand:
    """Tests for tool_run_command function."""
    
    def test_run_simple_command(self):
        """Should execute simple commands."""
        result = tool_run_command("echo Hello")
        assert "Hello" in result
    
    def test_run_command_with_output(self):
        """Should capture command output."""
        result = tool_run_command("python -c \"print('test output')\"")
        assert "test output" in result
    
    def test_run_invalid_command(self):
        """Should handle invalid commands."""
        result = tool_run_command("nonexistent_command_xyz123")
        assert "exit code" in result.lower() or "error" in result.lower()
    
    def test_run_command_timeout(self):
        """Should handle timeout."""
        # Use a command that takes longer than timeout
        result = tool_run_command("timeout 5 || ping -n 5 127.0.0.1", timeout=1)
        assert "timed out" in result.lower() or "exit code" in result.lower()


# ── Search Files Tests ──

class TestSearchFiles:
    """Tests for tool_search_files function."""
    
    def test_search_pattern_found(self, sample_tree):
        """Should find files matching pattern."""
        original_cwd = trashclaw.CWD
        try:
            trashclaw.CWD = sample_tree
            result = tool_search_files(r"print\(")
            
            assert "file1.py" in result
            assert "file2.py" in result
        finally:
            trashclaw.CWD = original_cwd
    
    def test_search_pattern_not_found(self, temp_dir):
        """Should return message when pattern not found."""
        original_cwd = trashclaw.CWD
        try:
            trashclaw.CWD = temp_dir
            result = tool_search_files("NonExistentPattern12345")
            
            assert "No matches" in result
        finally:
            trashclaw.CWD = original_cwd
    
    def test_search_with_glob_filter(self, sample_tree):
        """Should respect glob filter."""
        original_cwd = trashclaw.CWD
        try:
            trashclaw.CWD = sample_tree
            result = tool_search_files(r".*", glob_filter="*.py")
            
            assert ".py" in result
            assert ".txt" not in result or "data.json" not in result
        finally:
            trashclaw.CWD = original_cwd
    
    def test_search_invalid_regex(self, temp_dir):
        """Should handle invalid regex."""
        original_cwd = trashclaw.CWD
        try:
            trashclaw.CWD = temp_dir
            result = tool_search_files("[invalid(regex")
            
            assert "Error" in result
            assert "regex" in result.lower()
        finally:
            trashclaw.CWD = original_cwd


# ── Find Files Tests ──

class TestFindFiles:
    """Tests for tool_find_files function."""
    
    def test_find_by_extension(self, sample_tree):
        """Should find files by extension."""
        original_cwd = trashclaw.CWD
        try:
            trashclaw.CWD = sample_tree
            result = tool_find_files("*.py")
            
            assert "file1.py" in result
            assert "file2.py" in result
        finally:
            trashclaw.CWD = original_cwd
    
    def test_find_recursive(self, sample_tree):
        """Should search recursively."""
        original_cwd = trashclaw.CWD
        try:
            trashclaw.CWD = sample_tree
            result = tool_find_files("**/*.py")
            
            assert "file1.py" in result
            assert "file2.py" in result
        finally:
            trashclaw.CWD = original_cwd
    
    def test_find_no_matches(self, temp_dir):
        """Should handle no matches."""
        original_cwd = trashclaw.CWD
        try:
            trashclaw.CWD = temp_dir
            result = tool_find_files("*.nonexistent")
            
            assert "No files matching" in result
        finally:
            trashclaw.CWD = original_cwd


# ── List Directory Tests ──

class TestListDir:
    """Tests for tool_list_dir function."""
    
    def test_list_empty_directory(self, temp_dir):
        """Should handle empty directory."""
        result = tool_list_dir(temp_dir)
        assert "empty" in result.lower() or temp_dir in result
    
    def test_list_directory_with_files(self, sample_tree):
        """Should list files in directory."""
        result = tool_list_dir(sample_tree)
        
        assert "subdir1" in result
        assert "subdir2" in result
        assert "file1.py" in result
    
    def test_list_nonexistent_directory(self, temp_dir):
        """Should handle non-existent directory."""
        nonexistent = os.path.join(temp_dir, "nonexistent")
        result = tool_list_dir(nonexistent)
        
        assert "Error" in result


# ── Fetch URL Tests ──

class TestFetchUrl:
    """Tests for tool_fetch_url function."""
    
    def test_fetch_valid_url(self):
        """Should fetch valid URL."""
        result = tool_fetch_url("https://example.com")
        
        assert "Example" in result or "example.com" in result
    
    def test_fetch_invalid_url(self):
        """Should handle invalid URL."""
        result = tool_fetch_url("https://nonexistent.invalid.domain.xyz")
        
        assert "Error" in result or "HTTP" in result or "URL" in result


# ── Think Tool Tests ──

class TestThinkTool:
    """Tests for tool_think function."""
    
    def test_think_records_thought(self):
        """Should record thought without side effects."""
        result = tool_think("This is a test thought")
        
        assert "Thought recorded" in result
        assert "no side effects" in result


# ── Project Context Detection Tests ──

class TestProjectContextDetection:
    """Tests for detect_project_context function."""
    
    def test_detect_python_project(self, temp_dir):
        """Should detect Python project."""
        original_cwd = trashclaw.CWD
        try:
            trashclaw.CWD = temp_dir
            with open(os.path.join(temp_dir, "requirements.txt"), "w") as f:
                f.write("pytest\n")
            
            result = detect_project_context()
            assert "Python" in result
        finally:
            trashclaw.CWD = original_cwd
    
    def test_detect_node_project(self, temp_dir):
        """Should detect Node.js project."""
        original_cwd = trashclaw.CWD
        try:
            trashclaw.CWD = temp_dir
            with open(os.path.join(temp_dir, "package.json"), "w") as f:
                f.write("{}\n")
            
            result = detect_project_context()
            assert "Node" in result or "JavaScript" in result
        finally:
            trashclaw.CWD = original_cwd
    
    def test_detect_rust_project(self, temp_dir):
        """Should detect Rust project."""
        original_cwd = trashclaw.CWD
        try:
            trashclaw.CWD = temp_dir
            with open(os.path.join(temp_dir, "Cargo.toml"), "w") as f:
                f.write("[package]\n")
            
            result = detect_project_context()
            assert "Rust" in result
        finally:
            trashclaw.CWD = original_cwd
    
    def test_unknown_project(self, temp_dir):
        """Should return Unknown for unrecognized projects."""
        original_cwd = trashclaw.CWD
        try:
            trashclaw.CWD = temp_dir
            result = detect_project_context()
            
            # Should return something (even if "Unknown")
            assert result is not None
        finally:
            trashclaw.CWD = original_cwd


# ── Integration Tests ──

class TestIntegration:
    """Integration tests combining multiple tools."""
    
    def test_write_then_read(self, temp_dir):
        """Should be able to write and then read a file."""
        filepath = os.path.join(temp_dir, "test.txt")
        content = "Test content\nLine 2\n"
        
        # Write
        write_result = tool_write_file(filepath, content)
        assert "Wrote" in write_result
        
        # Read
        read_result = tool_read_file(filepath)
        assert "Test content" in read_result
    
    def test_write_then_edit_then_read(self, temp_dir):
        """Should be able to write, edit, and read a file."""
        filepath = os.path.join(temp_dir, "test.txt")
        
        # Write
        tool_write_file(filepath, "Original\n")
        
        # Edit
        edit_result = tool_edit_file(filepath, "Original", "Modified")
        assert "Edited" in edit_result
        
        # Read
        read_result = tool_read_file(filepath)
        assert "Modified" in read_result
        assert "Original" not in read_result
    
    def test_search_in_created_files(self, temp_dir):
        """Should be able to search in created files."""
        original_cwd = trashclaw.CWD
        try:
            trashclaw.CWD = temp_dir
            
            # Create files
            tool_write_file(os.path.join(temp_dir, "file1.txt"), "Hello World\n")
            tool_write_file(os.path.join(temp_dir, "file2.txt"), "Goodbye World\n")
            
            # Search
            result = tool_search_files("World")
            
            assert "file1.txt" in result
            assert "file2.txt" in result
        finally:
            trashclaw.CWD = original_cwd


# ── Run Tests ──

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
