"""Tests for file system utilities."""

import time
from pathlib import Path

from PrevisLib.utils.file_system import (
    clean_directory,
    count_files,
    ensure_directory,
    find_files,
    is_directory_empty,
    mo2_aware_copy,
    safe_delete,
)


class TestDirectoryOperations:
    """Test directory manipulation functions."""

    def test_clean_directory_creates_new(self, tmp_path: Path) -> None:
        """Test that clean_directory creates new directory."""
        test_dir = tmp_path / "test_clean"

        clean_directory(test_dir)

        assert test_dir.exists()
        assert test_dir.is_dir()
        assert is_directory_empty(test_dir)

    def test_clean_directory_removes_contents(self, tmp_path: Path) -> None:
        """Test that clean_directory removes existing contents."""
        test_dir = tmp_path / "test_clean"
        test_dir.mkdir()

        # Create some files
        (test_dir / "file1.txt").write_text("content")
        (test_dir / "file2.txt").write_text("content")
        (test_dir / "subdir").mkdir()

        assert not is_directory_empty(test_dir)

        clean_directory(test_dir)

        assert test_dir.exists()
        assert is_directory_empty(test_dir)

    def test_clean_directory_no_create(self, tmp_path: Path) -> None:
        """Test clean_directory with create=False."""
        test_dir = tmp_path / "test_clean"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        clean_directory(test_dir, create=False)

        assert not test_dir.exists()

    def test_ensure_directory_creates_path(self, tmp_path: Path) -> None:
        """Test that ensure_directory creates directory path."""
        test_dir = tmp_path / "deep" / "nested" / "path"

        ensure_directory(test_dir)

        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_directory_existing_path(self, tmp_path: Path) -> None:
        """Test ensure_directory on existing path."""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()

        # Should not raise error
        ensure_directory(test_dir)
        assert test_dir.exists()


class TestFileOperations:
    """Test file manipulation functions."""

    def test_find_files_basic(self, tmp_path: Path) -> None:
        """Test basic file finding."""
        # Create test files
        (tmp_path / "file1.txt").write_text("content")
        (tmp_path / "file2.txt").write_text("content")
        (tmp_path / "file3.py").write_text("content")

        txt_files = find_files(tmp_path, "*.txt")
        assert len(txt_files) == 2
        assert all(f.suffix == ".txt" for f in txt_files)

    def test_find_files_recursive(self, tmp_path: Path) -> None:
        """Test recursive file finding."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        (tmp_path / "root.txt").write_text("content")
        (subdir / "nested.txt").write_text("content")

        # Recursive search
        txt_files = find_files(tmp_path, "*.txt", recursive=True)
        assert len(txt_files) == 2

        # Non-recursive search
        txt_files = find_files(tmp_path, "*.txt", recursive=False)
        assert len(txt_files) == 1
        assert txt_files[0].name == "root.txt"

    def test_count_files(self, tmp_path: Path) -> None:
        """Test file counting."""
        # Create test files
        for i in range(5):
            (tmp_path / f"file{i}.txt").write_text("content")

        count = count_files(tmp_path, "*.txt")
        assert count == 5

        count = count_files(tmp_path, "*.py")
        assert count == 0

    def test_safe_delete_file(self, tmp_path: Path) -> None:
        """Test safe deletion of files."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        assert test_file.exists()

        result = safe_delete(test_file)
        assert result is True
        assert not test_file.exists()

    def test_safe_delete_directory(self, tmp_path: Path) -> None:
        """Test safe deletion of directories."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        result = safe_delete(test_dir)
        assert result is True
        assert not test_dir.exists()

    def test_safe_delete_nonexistent(self, tmp_path: Path) -> None:
        """Test safe deletion of non-existent file."""
        nonexistent = tmp_path / "nonexistent.txt"

        result = safe_delete(nonexistent)
        assert result is True  # Should return True for already gone files

    def test_mo2_aware_copy_file(self, tmp_path: Path) -> None:
        """Test MO2-aware file copying."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"

        source.write_text("test content")

        start_time = time.time()
        mo2_aware_copy(source, dest, delay=0.1)  # Short delay for testing
        elapsed = time.time() - start_time

        assert dest.exists()
        assert dest.read_text() == "test content"
        assert elapsed >= 0.1  # Should have waited at least the delay time

    def test_mo2_aware_copy_directory(self, tmp_path: Path) -> None:
        """Test MO2-aware directory copying."""
        source = tmp_path / "source_dir"
        dest = tmp_path / "dest_dir"

        source.mkdir()
        (source / "file1.txt").write_text("content1")
        (source / "file2.txt").write_text("content2")

        mo2_aware_copy(source, dest, delay=0.1)

        assert dest.exists()
        assert (dest / "file1.txt").exists()
        assert (dest / "file2.txt").exists()
        assert (dest / "file1.txt").read_text() == "content1"
