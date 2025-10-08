import hashlib
import json
import zlib
from pathlib import Path
from typing import Dict, List, Tuple


# Helper to write a Git object to .git/objects/
def write_git_object(sha: str, content: bytes, repo_root: str = "."):
    obj_dir = Path(repo_root) / ".pygit" / "objects" / sha[:2]
    obj_dir.mkdir(parents=True, exist_ok=True)
    obj_path = obj_dir / sha[2:]
    compressed = zlib.compress(content)
    with open(obj_path, "wb") as f:
        f.write(compressed)


# Recursive function to build and store a tree object
def build_tree(
    entries: List[Tuple[str, str, str]], prefix: str = "", repo_root: str = "."
) -> str:
    """
    Builds a Git tree object recursively.

    :param entries: List of (full_path, mode, sha) for all staged files under this prefix.
    :param prefix: Current directory prefix (e.g., 'doc/' for recursion).
    :return: Hex SHA-1 of the created tree object.
    """
    if not entries:
        raise ValueError("No entries to build tree from")

    # Group entries into files (direct children) and subdirs
    subdirs: Dict[str, List[Tuple[str, str, str]]] = {}
    files: List[Tuple[str, str, str]] = []  # (name, mode, sha)

    for full_path, mode, sha in entries:
        # Remove './' prefix and current prefix for relative path
        rel_path = full_path.lstrip("./")
        if prefix:
            if not rel_path.startswith(prefix):
                continue  # Skip entries not under this prefix
            rel_path = rel_path[len(prefix) :].lstrip("/")
        else:
            rel_path = rel_path.lstrip("/")

        parts = rel_path.split("/", 1)
        name = parts[0]

        if len(parts) == 1:
            # It's a file in this dir
            files.append((name, mode, sha))
        else:
            # It's in a subdir
            subdir_name = name
            if subdir_name not in subdirs:
                subdirs[subdir_name] = []
            subdirs[subdir_name].append((full_path, mode, sha))

    # Recursively build subtrees
    subtree_entries: List[Tuple[str, str, str]] = []
    for subdir_name, sub_entries in subdirs.items():
        sub_prefix = f"{prefix}{subdir_name}/"
        sub_tree_sha = build_tree(sub_entries, sub_prefix, repo_root)
        subtree_entries.append((subdir_name, "040000", sub_tree_sha))

    # Combine files and subtrees, sort by name
    all_entries = files + subtree_entries
    all_entries.sort(key=lambda e: e[0])  # Sort alphabetically by name

    # Serialize to Git tree format
    tree_content = b""
    for name, mode, sha in all_entries:
        entry = f"{mode} {name}\0".encode("utf-8") + bytes.fromhex(sha)
        tree_content += entry

    # Add header
    header = f"tree {len(tree_content)}\0".encode("utf-8")
    full_content = header + tree_content

    # Compute SHA-1
    tree_sha = hashlib.sha1(full_content).hexdigest()

    # Store the object
    write_git_object(tree_sha, full_content, repo_root)

    return tree_sha


# Main function to create root tree from index.json
def create_tree_from_index(repo_root: str = ".") -> str:
    """
    Loads index.json and creates the root tree object.

    :return: Hex SHA-1 of the root tree.
    """
    index_path = Path(repo_root) / ".pygit" / "index.json"
    if not index_path.exists():
        raise FileNotFoundError("index.json not found")

    with open(index_path, "r") as f:
        index_data = json.load(f)  # Dict: {path: {hash, mode, mtime, size}, ...}

    # Convert to list of tuples: (path, mode, sha)
    entries: List[Tuple[str, str, str]] = [
        (path, str(data["mode"]), data["hash"]) for path, data in index_data.items()
    ]

    if not entries:
        raise ValueError("No staged entries in index.json")

    # Build the root tree
    root_tree_sha = build_tree(entries, prefix="", repo_root=repo_root)
    return root_tree_sha
