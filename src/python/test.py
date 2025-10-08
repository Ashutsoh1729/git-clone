import json
import os
import subprocess
from pathlib import Path

from lib import Commit


def main():

    pygit = Path("./.pygit")
    commit = Commit(pygit=pygit)
    # print(commit.list_of_tuples)
    commit.build_tree()
    pass


if __name__ == "__main__":
    main()
