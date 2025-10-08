import os
import pathlib

path = pathlib.Path(".")
lib_path = path / "test" / "lib"
test_file = lib_path / "test.txt"
content = [("1", "2"), ("3", "4")]

with open(test_file, "w+") as f:
    f.write(str(content))
    written_content = f.read()

print(written_content)
