# here it will be used for the testing purposes of indivisual concepts

import hashlib
import json
import zlib
from pathlib import Path
from typing import Dict, List, Tuple


def write_objects(sha: str, content: bytes, repo_root: str = "."):
    obj_dir = Path(repo_root) / ".pygit" / "objects" / sha[:2]
    obj_dir.mkdir(exist_ok=True, parents=True)
    obj_path = obj_dir / sha[2:]
    compressed_file = zlib.compress(content)
    with open(obj_path, "wb") as f:  # wb is for writing bytes
        f.write(compressed_file)


def build_tree(
    entries: List[Tuple[str, str, str]], repo_root: str = ".", prefix: str = ""
):
    if not entries:
        raise ValueError("No entries to build the tree from ")

    subdir: Dict[str, List[Tuple[str, str, str]]] = {}
    files: List[Tuple[str, str, str]] = []

    for full_file_path, hash, mode in entries:

        # -- for removing the prefix
        # checking for prefix
        rel_path = full_file_path.lstrip(prefix)
        if prefix:
            if not rel_path.startswith(prefix):
                continue
            rel_path = rel_path[len(prefix) :].lstrip("/")
        else:
            rel_path = rel_path.lstrip("/")

        # ['test', 'lib', 'main.json'] -> For ideation

        # I have to sotre the dir and files in a tree structure
        # 1. file -> length of the part is 1,
        # 2. dir -> length of the parts list > 1, first element is the name of the dir
        # 3. empty dir not considered

        # when it find a file, it will add the hash and mode to an array
        parts = rel_path.split("/")
        name = parts[0]
        if len(parts) == 1:
            files.append((name, hash, mode))
        else:
            # here the dir will be handled
            subdir_name = name
            if subdir_name not in subdir:
                subdir[subdir_name] = []  # initializing an empty array for subdir
            subdir[subdir_name].append((full_file_path, hash, mode))

    # recursively building the subtree
    subtree_entries: List[Tuple[str, str, str]] = []
    for subdir_name, subdir_value in subdir.items():
        sub_prefix = f"{prefix}{subdir_name}/"
        sub_tree_hash = build_tree(prefix=sub_prefix, entries=subdir_value)
        subtree_entries.append((subdir_name, sub_tree_hash, "040000"))

        # combine the files and subtrees, currently not doing the sorting
    all_entries = files + subtree_entries

    # serializing the git tree format

    tree_content = b""
    for name, hash, mode in all_entries:
        entry = f"{mode} {name}\0".encode("utf-8") + bytes.fromhex(hash)
        tree_content += entry
    # Add header
    header = f"tree {len(tree_content)}\0".encode("utf-8")
    full_content = header + tree_content

    # Compute SHA-1
    tree_sha = hashlib.sha1(full_content).hexdigest()

    # storing the object
    write_objects(sha=tree_sha, content=full_content)

    return tree_sha


def main():
    path = Path(__file__).parent
    json_file_path = path / "lib" / "main.json"
    with open(json_file_path, "r") as f:
        content = json.load(f)

    list_of_tuples = [
        (item, content[item]["hash"], content[item]["mode"]) for item in content
    ]
    build_tree(entries=list_of_tuples, prefix="./")

    pass


if __name__ == "__main__":
    main()
    pass
