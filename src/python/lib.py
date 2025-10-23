# here we will write the helper clases
import fnmatch
import hashlib
import json
import os
import stat
import zlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class Add:

    def __init__(self, files, pygit: Path) -> None:

        # either the user will give "." for all files or he will give indivisual file names
        if len(files) > 1 or "." not in files:
            self.files = files
        else:
            self.files = "."

        self.pygit = pygit
        self.obj_dir = pygit / "objects"
        self.index_path = pygit / "index.json"
        self.index_object = Index(index_path=self.index_path, obj_dir=self.obj_dir)

        pass

    #  NOTE: 1. create blob, 2. create sha-1 hash, 3. compress the content, 4. write the index file and blobs objects
    def compute_hash(self, content: str):
        header = f"blob {len(content)}\0".encode("utf-8")
        current_content = content.encode(encoding="utf-8")
        return hashlib.sha1(header + current_content).hexdigest()

    def write_blobs(self, content: str, obj_dir: Path):
        hash = self.compute_hash(content)
        blob_dir = obj_dir / hash[:2]
        blob_fileName = blob_dir / hash[2:]

        blob_dir.mkdir(exist_ok=True)
        # if os.path.exists()
        # it will write the code again and again
        with open(blob_fileName, "wb") as f:
            f.write(zlib.compress(content.encode("utf-8")))

        return hash

    def read_ignored_patterns(self, ignore_file=".pygitignore"):
        patterns = []
        if os.path.exists(ignore_file):
            with open(ignore_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line.startswith("#"):
                        patterns.append(line)

        return patterns

    def stage_files(self, files):
        ignore_pattern = self.read_ignored_patterns()
        self.index_object.delete_index_content()
        if type(self.files).__name__ == "list":
            for file in self.files:
                # print(file)
                pass
        elif type(self.files).__name__ == "str":
            for root, dirs, files in os.walk(self.files):
                # print(root)
                dirs[:] = [
                    dir
                    for dir in dirs
                    if not any(
                        fnmatch.fnmatch(dir, p.rstrip("/")) for p in ignore_pattern
                    )
                ]
                files[:] = [
                    file
                    for file in files
                    if not any(fnmatch.fnmatch(file, f) for f in ignore_pattern)
                ]
                print(files)

                for file in files:
                    full_file_path = root + "/" + file
                    with open(full_file_path, "r") as f:
                        content = f.read()
                        self.write_blobs(content=content, obj_dir=self.obj_dir)
                        current_hash = self.compute_hash(content)
                        self.index_object.write_index_content(
                            file_path=full_file_path, hash=current_hash
                        )


class Index:
    def __init__(self, index_path: Path, obj_dir: Path) -> None:
        if index_path.exists():
            self.index_path = index_path
            self.entries = self.load_index()
            self.obj_dir = obj_dir

    def load_index(self):
        if self.index_path.exists():
            with open(self.index_path) as f:
                return json.load(f)
        return {}

    def write_index_content(self, file_path, hash):

        blob_dir = hash[:2]
        blob_obj = hash[2:]
        blob_full_path = self.obj_dir / blob_dir / blob_obj

        if os.path.exists(blob_full_path):
            mode = self.file_mode(file_path)
            mtime = os.path.getmtime(file_path)
            size = os.path.getsize(file_path)
            self.entries[file_path] = {
                "hash": hash,
                "mode": mode,
                "mtime": mtime,
                "size": size,
            }
            with open(self.index_path, "w") as f:
                json.dump(self.entries, f, indent=2)

    def delete_index_content(self):
        # for files listed in index but not exists anymore in working directory
        #  NOTE: I have to write the code to remove the blob files also, other wise the db will be bloated with the code of the files that already got deleted
        index_keys = self.entries.keys()
        keys_to_remove = []
        for index_file_path in index_keys:
            if not os.path.exists(index_file_path):
                try:
                    hash: str = self.entries[index_file_path]["hash"]
                    complete_blob_path = self.obj_dir / hash[:2] / hash[2:]
                    #  FIX: file is not delted, may be becoz, the path is relative
                    #  here it is right according to os.path.exists, but it shows in the yazi, i have tried unlink, but it still creating it. That has 2 options- 1. It is not getting deleted , 2. The blob is getting created again
                    print(
                        f"\n Currently {index_file_path} exists at:{os.path.exists(complete_blob_path)} "
                    )

                    if complete_blob_path.exists():
                        complete_blob_path.unlink(missing_ok=True)
                    blob_dir = self.obj_dir / hash[:2]
                    if blob_dir.exists():
                        blob_dir.rmdir()

                    print(
                        f"\n Currently {index_file_path} shouldn't exist and it should show false : {os.path.exists(complete_blob_path)} "
                    )
                    # it may leave an empyt folder behind
                    keys_to_remove.append(index_file_path)
                except Exception as e:
                    print(f"Here the error is: {e}")
                    raise e

        for item in keys_to_remove:
            self.entries.pop(item)

        with open(self.index_path, "w") as f:
            json.dump(self.entries, f, indent=2)

    def file_mode(self, file_path):
        mode = stat.S_IMODE(os.stat(file_path).st_mode)
        mode_str = oct(mode)[2:]
        return f"100{mode_str}"


class Commit:
    def __init__(self, pygit: Path):
        self.index_path = pygit / "index.json"
        self.obj_dir = pygit / "objects"
        self.index = Index(index_path=self.index_path, obj_dir=self.obj_dir)
        self.list_of_tuples: List[Tuple[str, str, str]] = [
            (item, self.index.entries[item]["hash"], self.index.entries[item]["mode"])
            for item in self.index.entries
        ]
        pass

    def create_tree_from_index(self, repo_root: str = ".") -> str:
        """
        Loads index.json and creates the root tree object.

        :return: Hex SHA-1 of the root tree.
        """
        root_tree_sha = self.build_tree(
            repo_root=repo_root, prefix="", entries=self.list_of_tuples
        )
        return root_tree_sha
        pass

    def write_tree_objects(self, content: bytes, hash: str, repo_root: str = "."):
        obj_dir = Path(".") / ".pygit" / "objects" / hash[:2]
        obj_dir.mkdir(exist_ok=True, parents=True)
        obj_file_path = obj_dir / hash[2:]
        compressed_file = zlib.compress(content)
        with open(obj_file_path, "wb") as f:
            f.write(compressed_file)

    def build_tree(
        self,
        entries: List[Tuple[str, str, str]],
        repo_root: str = ".",
        prefix: str = "",
    ) -> str:
        """
        Builds a Git tree object recursively.

        :param entries: List of (full_path, mode, sha) for all staged files under this prefix.
        :param prefix: Current directory prefix (e.g., 'doc/' for recursion).
        :return: Hex SHA-1 of the created tree object.
        """

        # we will store the tree information in a tree object, which is a text like file with
        # it's own sha-1 hash for unique identification and is stored as a compressed zlib file
        # in objects dir
        if not entries:
            raise ValueError("No entries to build tree from")

        subdirs: Dict[str, List[Tuple[str, str, str]]] = {}
        files: List[Tuple[str, str, str]] = []

        for full_path, hash, mode in entries:
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
                files.append((name, hash, mode))
            else:
                # It's in a subdir
                subdir_name = name
                if subdir_name not in subdirs:
                    subdirs[subdir_name] = []
                subdirs[subdir_name].append((full_path, hash, mode))

        # now building the tree structure
        subtree_entries: List[Tuple[str, str, str]] = []
        for subdir_name, subdir_val in subdirs.items():
            sub_prefix = f"{prefix}{subdir_name}/"
            subtree_sha = self.build_tree(
                entries=subdir_val, prefix=sub_prefix, repo_root=repo_root
            )
            subtree_entries.append((subdir_name, subtree_sha, "040000"))

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
        self.write_tree_objects(
            hash=tree_sha, content=full_content, repo_root=repo_root
        )

        print(f"Tree hash is calculated for : {subtree_entries}")

        return tree_sha

        pass

        pass

    def commit(self, message: str):
        root_tree_hash = self.create_tree_from_index()
        time = datetime.now()
        final_data = f"\n{root_tree_hash},time:{time},message:{message}"
        git_dir = Path(".") / ".pygit"
        commit_file_path = git_dir / "commit.txt"
        with open(commit_file_path, "w") as f:
            f.write(final_data)

        # where to save the hash data


class Push:
    """
    we have to facilitate to add the functionalities to execute the below functions

    git remote add origin git@github.com:Ashutsoh1729/test-git.git
    git branch -M main
    git push -u origin main

    it will first check the following things:
        1. remote repo info exists or not

    """

    def __init__(self) -> None:
        pass

    def push(self):
        pass


class remote:
    def __init__(self):
        pass
