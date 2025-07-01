"""Consolidated tests for file system utilities and operations."""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from PrevisLib.utils.file_system import (
    clean_directory,
    copy_with_callback,
    count_files,
    ensure_directory,
    find_files,
    is_directory_empty,
    mo2_aware_copy,
    mo2_aware_move,
    safe_delete,
    wait_for_file,
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


class TestExtendedFileOperations:
    """Test extended file system operations."""

    def test_is_directory_empty_nonexistent(self, tmp_path: Path) -> None:
        """Test checking if non-existent directory is empty."""
        nonexistent = tmp_path / "nonexistent"
        assert is_directory_empty(nonexistent) is True

    def test_is_directory_empty_with_files(self, tmp_path: Path) -> None:
        """Test checking if directory with files is empty."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        # Empty directory
        assert is_directory_empty(test_dir) is True

        # Add a file
        test_file = test_dir / "file.txt"
        test_file.write_text("content")
        assert is_directory_empty(test_dir) is False

    def test_is_directory_empty_with_subdirs(self, tmp_path: Path) -> None:
        """Test checking directory with subdirectories."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        # Add subdirectory
        subdir = test_dir / "subdir"
        subdir.mkdir()
        assert is_directory_empty(test_dir) is False

    def test_wait_for_file_exists_immediately(self, tmp_path: Path) -> None:
        """Test waiting for file that already exists."""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("content")

        result = wait_for_file(test_file, timeout=1.0)
        assert result is True

    def test_wait_for_file_timeout(self, tmp_path: Path) -> None:
        """Test waiting for file that never appears."""
        test_file = tmp_path / "nonexistent.txt"

        start_time = time.time()
        result = wait_for_file(test_file, timeout=0.1)
        elapsed = time.time() - start_time

        assert result is False
        assert elapsed >= 0.1

    def test_wait_for_file_appears_later(self, tmp_path: Path) -> None:
        """Test waiting for file that appears during wait."""
        test_file = tmp_path / "delayed.txt"

        def create_file_later() -> None:
            time.sleep(0.05)
            test_file.write_text("content")

        import threading

        thread = threading.Thread(target=create_file_later)
        thread.start()

        result = wait_for_file(test_file, timeout=0.2, check_interval=0.01)
        thread.join()

        assert result is True

    @patch("time.sleep")
    def test_mo2_aware_move(self, mock_sleep: MagicMock, tmp_path: Path) -> None:
        """Test MO2-aware file move."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("content")

        mo2_aware_move(source, dest, delay=1.5)

        assert not source.exists()
        assert dest.exists()
        assert dest.read_text() == "content"
        mock_sleep.assert_called_once_with(1.5)

    @patch("time.sleep")
    def test_mo2_aware_copy_file(self, mock_sleep: MagicMock, tmp_path: Path) -> None:
        """Test MO2-aware file copy."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("content")

        mo2_aware_copy(source, dest, delay=2.0)

        assert source.exists()
        assert dest.exists()
        assert dest.read_text() == "content"
        mock_sleep.assert_called_once_with(2.0)

    @patch("time.sleep")
    def test_mo2_aware_copy_directory(self, mock_sleep: MagicMock, tmp_path: Path) -> None:
        """Test MO2-aware directory copy."""
        source_dir = tmp_path / "source_dir"
        dest_dir = tmp_path / "dest_dir"
        source_dir.mkdir()

        # Create files in source
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "file2.txt").write_text("content2")

        mo2_aware_copy(source_dir, dest_dir, delay=1.0)

        assert source_dir.exists()
        assert dest_dir.exists()
        assert (dest_dir / "file1.txt").read_text() == "content1"
        assert (dest_dir / "file2.txt").read_text() == "content2"
        mock_sleep.assert_called_once_with(1.0)

    def test_find_files_non_recursive(self, tmp_path: Path) -> None:
        """Test finding files non-recursively."""
        # Create files in different levels
        (tmp_path / "root1.txt").write_text("content")
        (tmp_path / "root2.log").write_text("content")

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "sub1.txt").write_text("content")

        # Non-recursive should only find root files
        txt_files = find_files(tmp_path, "*.txt", recursive=False)
        assert len(txt_files) == 1
        assert txt_files[0].name == "root1.txt"

    def test_count_files_extended(self, tmp_path: Path) -> None:
        """Test counting files with extended scenarios."""
        # Create test files
        (tmp_path / "file1.txt").write_text("content")
        (tmp_path / "file2.txt").write_text("content")
        (tmp_path / "file3.log").write_text("content")

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file4.txt").write_text("content")

        # Count all files (includes directory)
        total_count = count_files(tmp_path, "*", recursive=True)
        assert total_count == 5  # 3 files + 1 dir + 1 file in subdir

        # Count only txt files
        txt_count = count_files(tmp_path, "*.txt", recursive=True)
        assert txt_count == 3

        # Count non-recursive (includes directory but not files inside it)
        root_count = count_files(tmp_path, "*", recursive=False)
        assert root_count == 4  # 3 files + 1 directory

    @patch("time.sleep")
    def test_safe_delete_with_retries(self, mock_sleep: MagicMock, tmp_path: Path) -> None:
        """Test safe deletion with retry logic."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with patch("pathlib.Path.unlink") as mock_unlink:
            # First two calls fail, third succeeds
            mock_unlink.side_effect = [PermissionError("Access denied"), PermissionError("Access denied"), None]

            result = safe_delete(test_file, retry_count=3, retry_delay=0.1)

            assert result is True
            assert mock_unlink.call_count == 3
            assert mock_sleep.call_count == 2  # Two retries

    @patch("time.sleep")
    def test_safe_delete_all_retries_fail(self, mock_sleep: MagicMock, tmp_path: Path) -> None:
        """Test safe deletion when all retries fail."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with patch("pathlib.Path.unlink") as mock_unlink:
            mock_unlink.side_effect = PermissionError("Access denied")

            result = safe_delete(test_file, retry_count=2, retry_delay=0.1)

            assert result is False
            assert mock_unlink.call_count == 2
            assert mock_sleep.call_count == 1  # One retry

    def test_copy_with_callback_file(self, tmp_path: Path) -> None:
        """Test copying file with progress callback."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("content")

        callback_calls = []

        def progress_callback(current: int, total: int) -> None:
            callback_calls.append((current, total))

        copy_with_callback(source, dest, progress_callback)

        assert dest.exists()
        assert dest.read_text() == "content"
        assert callback_calls == [(1, 1)]

    def test_copy_with_callback_directory(self, tmp_path: Path) -> None:
        """Test copying directory with progress callback."""
        source_dir = tmp_path / "source_dir"
        dest_dir = tmp_path / "dest_dir"
        source_dir.mkdir()

        # Create multiple files
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "file2.txt").write_text("content2")
        (source_dir / "file3.txt").write_text("content3")

        callback_calls = []

        def progress_callback(current: int, total: int) -> None:
            callback_calls.append((current, total))

        copy_with_callback(source_dir, dest_dir, progress_callback)

        assert dest_dir.exists()
        assert (dest_dir / "file1.txt").read_text() == "content1"
        assert (dest_dir / "file2.txt").read_text() == "content2"
        assert (dest_dir / "file3.txt").read_text() == "content3"

        # Should have 3 callback calls for 3 files
        assert len(callback_calls) == 3
        assert callback_calls[-1] == (3, 3)  # Final call should be (3, 3)

    def test_copy_with_callback_no_callback(self, tmp_path: Path) -> None:
        """Test copying without callback function."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("content")

        # Should not raise error with None callback
        copy_with_callback(source, dest, callback=None)

        assert dest.exists()
        assert dest.read_text() == "content"

    def test_copy_with_callback_nested_directory(self, tmp_path: Path) -> None:
        """Test copying directory with nested structure."""
        source_dir = tmp_path / "source_dir"
        dest_dir = tmp_path / "dest_dir"
        source_dir.mkdir()

        # Create nested structure
        nested_dir = source_dir / "nested"
        nested_dir.mkdir()
        (source_dir / "root_file.txt").write_text("root content")
        (nested_dir / "nested_file.txt").write_text("nested content")

        callback_calls = []

        def progress_callback(current: int, total: int) -> None:
            callback_calls.append((current, total))

        copy_with_callback(source_dir, dest_dir, progress_callback)

        assert dest_dir.exists()
        assert (dest_dir / "root_file.txt").read_text() == "root content"
        assert (dest_dir / "nested" / "nested_file.txt").read_text() == "nested content"

        # Should have called callback for each file
        assert len(callback_calls) == 2
