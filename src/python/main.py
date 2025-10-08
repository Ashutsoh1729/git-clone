import argparse

from pygit import pygit


def main():

    git = pygit()

    parser = argparse.ArgumentParser()
    subParser = parser.add_subparsers(dest="command")

    subParser.add_parser("init", help="Initialize the pygit")

    addParser = subParser.add_parser("add", help="add to the stage")
    addParser.add_argument(
        "files", nargs="+", help="give the files names or '.' for all files"
    )

    commitParser = subParser.add_parser("commit", help="commit the current stage")
    commitParser.add_argument(
        "-m", nargs=1, type=str, help="Give the message for commit", required=True
    )

    args = parser.parse_args()

    if args.command == "init":
        git.init()
    elif args.command == "add":
        git.add(files=args.files)
    elif args.command == "commit":
        git.commit(message=args.m[0])


# print("Hello from python!")


if __name__ == "__main__":
    main()
