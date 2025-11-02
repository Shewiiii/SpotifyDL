import os
import shutil
import tempfile
import subprocess
from pathlib import Path

from config import REPOSITORY_URL

PRESERVE_FILES = [
    ".env",
    "credentials.json",
]

PRESERVE_FOLDERS = [
    "songs",
]


def check_git_installed():
    try:
        subprocess.run(
            ["git", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def backup_preserved_items(workspace_dir, backup_dir):
    preserved_items = []

    # Backup files
    for file_name in PRESERVE_FILES:
        file_path: Path = workspace_dir / file_name
        if file_path.exists():
            backup_path: Path = backup_dir / file_name
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            preserved_items.append(file_name)

    # Backup folders
    for folder_name in PRESERVE_FOLDERS:
        folder_path: Path = workspace_dir / folder_name
        if folder_path.exists() and folder_path.is_dir():
            backup_path: Path = backup_dir / folder_name
            shutil.copytree(folder_path, backup_path, dirs_exist_ok=True)
            preserved_items.append(folder_name)

    return preserved_items


def restore_preserved_items(workspace_dir, backup_dir, preserved_items):
    for item_name in preserved_items:
        backup_path: Path = backup_dir / item_name
        restore_path: Path = workspace_dir / item_name

        if backup_path.is_file():
            restore_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, restore_path)
        elif backup_path.is_dir():
            shutil.copytree(backup_path, restore_path, dirs_exist_ok=True)


def clone_repo(repo_url, temp_dir):
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(temp_dir)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def update_files(
    workspace_dir, temp_repo_dir, preserve_files_set, preserve_folders_set
):
    updated_count = 0
    skipped_count = 0

    for root, dirs, files in os.walk(temp_repo_dir):
        if ".git" in dirs:
            dirs.remove(".git")

        rel_root = Path(root).relative_to(temp_repo_dir)

        # Skip preserved folders
        if any(str(rel_root).startswith(pf) for pf in preserve_folders_set):
            continue

        for file_name in files:
            rel_path = rel_root / file_name

            # Skip preserved files
            if str(rel_path) in preserve_files_set or file_name in preserve_files_set:
                skipped_count += 1
                continue

            src_file = Path(root) / file_name
            dest_file: Path = workspace_dir / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(src_file, dest_file)
            updated_count += 1


def main():
    if not check_git_installed():
        print("Git is not installed. Please install git and try again.")
        return

    workspace_dir = Path(__file__).parent.resolve()

    with tempfile.TemporaryDirectory() as temp_base:
        temp_base_path = Path(temp_base)
        backup_dir = temp_base_path / "backup"
        repo_dir = temp_base_path / "repo"

        backup_dir.mkdir(exist_ok=True)
        repo_dir.mkdir(exist_ok=True)
        preserved_items = backup_preserved_items(workspace_dir, backup_dir)
        if not clone_repo(REPOSITORY_URL, repo_dir):
            print("Failed to clone repository")
            return
        preserve_files_set = set(PRESERVE_FILES)
        preserve_folders_set = set(PRESERVE_FOLDERS)
        update_files(workspace_dir, repo_dir, preserve_files_set, preserve_folders_set)
        restore_preserved_items(workspace_dir, backup_dir, preserved_items)


if __name__ == "__main__":
    c = input(f"Update from {REPOSITORY_URL}? Your config will not be saved. (y/n): ")
    if c.lower() == "y":
        main()
        input("Success ! Press Enter to exit.")
