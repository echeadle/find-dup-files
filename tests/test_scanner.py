import os
import json
from pathlib import Path
from app.core.scanner import walk_directory
import pytest


def test_walk_directory_basic(tmp_path: Path):
    """
    Test that walk_directory finds all files in a simple directory structure.
    """
    # Create a simple directory structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir2").mkdir()
    (tmp_path / "file1.txt").touch()
    (tmp_path / "dir1" / "file2.txt").touch()
    (tmp_path / "dir2" / "file3.txt").touch()

    # Collect the yielded paths
    found_paths = list(walk_directory(str(tmp_path)))

    # Assert that all files were found
    assert len(found_paths) == 3
    assert tmp_path / "file1.txt" in found_paths
    assert tmp_path / "dir1" / "file2.txt" in found_paths
    assert tmp_path / "dir2" / "file3.txt" in found_paths


def test_walk_directory_skip_hidden(tmp_path: Path):
    """
    Test that walk_directory skips hidden directories and files.
    """
    # Create a directory structure with hidden files and directories
    (tmp_path / ".hidden_dir").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / ".hidden_file.txt").touch()
    (tmp_path / "__init__.py").touch()
    (tmp_path / "file1.txt").touch()
    (tmp_path / ".hidden_dir" / "file2.txt").touch()
    (tmp_path / "__pycache__" / "file3.txt").touch()

    # Collect the yielded paths
    found_paths = list(walk_directory(str(tmp_path)))

    # Assert that only the non-hidden file and the __init__.py file was found
    assert len(found_paths) == 2
    assert tmp_path / "file1.txt" in found_paths
    assert tmp_path / "__init__.py" in found_paths


def test_walk_directory_skip_symlinks(tmp_path: Path):
    """
    Test that walk_directory skips symbolic links.
    """
    # Create a directory structure with a symlink
    (tmp_path / "file1.txt").touch()
    os.symlink(tmp_path / "file1.txt", tmp_path / "symlink.txt")

    # Collect the yielded paths
    found_paths = list(walk_directory(str(tmp_path)))

    # Assert that only the file was found, not the symlink
    assert len(found_paths) == 1
    assert tmp_path / "file1.txt" in found_paths


def test_walk_directory_skip_config(tmp_path: Path):
    """
    Test that walk_directory skips directories listed in the config file.
    """
    # Create a config file
    config_data = {"excluded_directories": ["excluded_dir"]}
    config_file = tmp_path / "config.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    # Create a directory structure with an excluded directory
    (tmp_path / "excluded_dir").mkdir()
    (tmp_path / "file1.txt").touch()
    (tmp_path / "excluded_dir" / "file2.txt").touch()

    # Collect the yielded paths
    found_paths = list(walk_directory(str(tmp_path), str(config_file)))

    # Assert that only the non-excluded file was found
    assert len(found_paths) == 1
    assert tmp_path / "file1.txt" in found_paths
