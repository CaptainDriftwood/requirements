#!/usr/bin/env python3
"""
Clean untracked files from the repository, similar to git clean.
Preserves specific directories: .claude, .venv, .idea, .run
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def get_git_clean_files() -> list[str]:
    """Get list of files that would be removed by git clean -fdx"""
    try:
        # Use git clean -ndx to get a dry run of what would be removed
        result = subprocess.run(
            ["git", "clean", "-ndx"], capture_output=True, text=True, check=True
        )

        files_to_remove = []
        for line in result.stdout.strip().split("\n"):
            if line.startswith("Would remove "):
                # Extract the file path from the output
                file_path = line.replace("Would remove ", "")
                files_to_remove.append(file_path)

        return files_to_remove
    except subprocess.CalledProcessError as e:
        print(f"Error running git clean: {e}", file=sys.stderr)
        sys.exit(1)


def should_preserve_path(path: str) -> bool:
    """Check if a path should be preserved based on protected directories"""
    protected_dirs = {".claude", ".venv", ".idea", ".run"}

    # Convert to Path object for easier manipulation
    path_obj = Path(path)

    # Check if the path itself is a protected directory at root level
    if path_obj.parts and path_obj.parts[0] in protected_dirs:
        return True

    # Check if any parent directory is protected at root level
    for parent in path_obj.parents:
        if parent.parts and parent.parts[0] in protected_dirs:
            return True

    return False


def prompt_user(file_path: str) -> bool:
    """Prompt user for confirmation to remove a file"""
    while True:
        response = input(f"Remove {file_path}? [y/n]: ").strip().lower()
        if response in ["y", "yes"]:
            return True
        if response in ["n", "no"]:
            return False
        print("Please enter 'y' or 'n'")


def remove_file_or_directory(path: str) -> None:
    """Remove a file or directory"""
    path_obj = Path(path)

    if path_obj.is_dir():
        # Remove directory and all its contents
        shutil.rmtree(path_obj)
    else:
        # Remove file
        path_obj.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean untracked files from the repository, preserving specific directories"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually removing",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Prompt for confirmation before removing each file",
    )

    args = parser.parse_args()

    # Get list of files that git clean would remove
    files_to_remove = get_git_clean_files()

    if not files_to_remove:
        print("No files to clean.")
        return

    # Filter out protected directories
    filtered_files = []
    preserved_files = []

    for file_path in files_to_remove:
        if should_preserve_path(file_path):
            preserved_files.append(file_path)
        else:
            filtered_files.append(file_path)

    # Show preserved files if any
    if preserved_files:
        print("Preserving protected directories:")
        for file_path in preserved_files:
            print(f"  {file_path}")
        print()

    if not filtered_files:
        print("No files to remove after filtering.")
        return

    # Process files based on mode
    if args.dry_run:
        print("Would remove:")
        for file_path in filtered_files:
            print(f"  {file_path}")
    else:
        removed_count = 0
        skipped_count = 0

        for file_path in filtered_files:
            if args.interactive:
                if prompt_user(file_path):
                    try:
                        remove_file_or_directory(file_path)
                        print(f"Removed: {file_path}")
                        removed_count += 1
                    except Exception as e:
                        print(f"Error removing {file_path}: {e}", file=sys.stderr)
                else:
                    print(f"Skipped: {file_path}")
                    skipped_count += 1
            else:
                try:
                    remove_file_or_directory(file_path)
                    print(f"Removed: {file_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing {file_path}: {e}", file=sys.stderr)

        # Summary
        if args.interactive:
            print(
                f"\nRemoved {removed_count} files/directories, skipped {skipped_count}"
            )
        else:
            print(f"\nRemoved {removed_count} files/directories")


if __name__ == "__main__":
    main()
