# implementation of git
import json
import os
import pathlib

from lib import Add, Commit


class pygit:

    def __init__(self) -> None:
        self.path = pathlib.Path(".")
        self.pygit = self.path / ".pygit"
        self.pygit_init_tree = {
            "dirs": ["objects", "hooks", "info", "refs"],
            "files": ["config", "index.json"],
        }
        self.index_file = self.pygit / "index.json"
        self.obj_dir = self.pygit / "objects"

    def init(self):
        if not os.path.exists(self.pygit):

            print("Initializing a .pygit dir")
            os.mkdir(self.pygit)  # create the directory

            # create the new sub-dir
            for dir in self.pygit_init_tree["dirs"]:
                os.mkdir(self.pygit / dir)

            for file in self.pygit_init_tree["files"]:
                if file == "index.json":
                    with open(self.pygit / file, "w") as f:
                        json.dump({}, f)
                else:
                    open(self.pygit / file, "x")

        else:
            print("pygit already exists")

    def add(self, files):

        if not os.path.exists(self.pygit):
            print("Initialize a pygit dir first")
            return

        add = Add(files=files, pygit=self.pygit)

        add.stage_files(files=files)

        pass

    def commit(self, message):
        commit = Commit(pygit=self.pygit)
        commit.commit(message=message)
        pass
