#!/usr/bin/env python3
"""
Get a baseline of the /var/lang directory for subsequent diffs.
"""
from json import dump as json_dump
from os import lstat, readlink, walk
from stat import S_ISLNK, S_ISREG
from sys import stderr

def main():
    files = {}
    for path, subdirs, filenames in walk("/var/lang"):
        for filename in filenames:
            pathname = path + "/" + filename
            s = lstat(pathname)
            if S_ISLNK(s.st_mode):
                files[pathname] = {
                    "type": "link",
                    "target": readlink(pathname),
                }
            elif S_ISREG(s.st_mode):
                files[pathname] = {
                    "type": "file",
                    "size": s.st_size,
                    "mode": s.st_mode,
                }
            else:
                print(f"Unsupported file: {pathname}", file=stderr)

    with open("/baseline.json", "w") as fd:
        json_dump(files, fd)

if __name__ == "__main__":
    main()
