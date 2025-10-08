# here we will write the utility functions to learn the inside structure of git
import binascii
import os
import struct
from pathlib import Path


class ExploreGit:

    def __init__(self) -> None:
        self.path = Path()
        self.current_dir = self.path.cwd()
        self.project_dir = self.current_dir.parent.parent
        final_git = self.project_dir / ".git"
        git_dir_list = os.listdir(final_git)
        index_of_index = git_dir_list.index("index")
        self.index_path = final_git / git_dir_list[index_of_index]
        pass

    def read_git_index(self, path: Path):

        try:
            # open the index file in binary form
            with open(path, "rb") as f:
                # reading the entire file content
                data = f.read()

            # Parse the header (12 bytes)
            if len(data) < 12:
                print("Error: Index file is too small to contain a valid header.")
                return

            header = data[:12]  # first 12 are for header
            signature, version, numentry = struct.unpack(">4sII", header)
            if signature != b"DIRC":
                print("Error: Invalid index file signature. Expected 'DIRC'.")
                return

            print(f"Header:")
            print(f"  Signature: {signature.decode('ascii')}")
            print(f"  Version: {version}")
            print(f"  Number of entries: {numentry}")

            # Start parsing entries after the header
            offset = 12
            entries = []

            for i in range(numentry):
                if offset + 62 > len(data):
                    print(f"Error: Not enough data for entry {i + 1}.")
                    break

                # Each entry has a fixed-size portion (at least 62 bytes) + variable-length name
                entry_data = data[offset:]

                # Parse fixed-size fields (40 bytes for metadata + 20 bytes for SHA-1)
                ctime_s, ctime_ns, mtime_s, mtime_ns, dev, ino, mode, uid, gid, size = (
                    struct.unpack(">IIIIIIIIII", entry_data[:40])
                )
                sha1 = entry_data[40:60]  # 20-byte SHA-1 hash
                sha1_hex = binascii.hexlify(sha1).decode("ascii")

                # Parse flags (2 bytes)
                flags = struct.unpack(">H", entry_data[60:62])[0]
                name_length = (
                    flags & 0xFFF
                )  # Lower 12 bits of flags indicate name length

                # Read the file name (variable length, null-terminated)
                if offset + 62 + name_length > len(data):
                    print(f"Error: Invalid name length for entry {i + 1}.")
                    break

                name = entry_data[62 : 62 + name_length].decode("utf-8")
                # Entries are padded to align to 8-byte boundaries
                entry_size = 62 + name_length
                padding = 8 - (entry_size % 8) if entry_size % 8 != 0 else 0
                entry_size += padding

                # Store entry details
                entries.append(
                    {
                        "index": i + 1,
                        "name": name,
                        "sha1": sha1_hex,
                        "mode": oct(mode)[-6:],  # Convert mode to octal (e.g., 100644)
                        "size": size,
                        "ctime": ctime_s,
                        "mtime": mtime_s,
                    }
                )

                # Move to the next entry
                offset += entry_size

            # Print entries in a readable format
            print("\nIndex Entries:")
            for entry in entries:
                print(f"Entry {entry['index']}:")
                print(f"  File: {entry['name']}")
                print(f"  SHA-1: {entry['sha1']}")
                print(f"  Mode: {entry['mode']}")
                print(f"  Size: {entry['size']} bytes")
                print(f"  CTime: {entry['ctime']}")
                print(f"  MTime: {entry['mtime']}")
                print()

            # Check for extensions (optional)
            if offset < len(data) - 20:  # 20 bytes reserved for checksum
                print("Extensions present (not parsed):")
                print(binascii.hexlify(data[offset:-20]).decode("ascii"))

            # Read the checksum (last 20 bytes)
            checksum = binascii.hexlify(data[-20:]).decode("ascii")
            print(f"\nChecksum: {checksum}")

        except Exception as e:
            raise e

        pass
