#!/usr/bin/env python3
"""
Create a ZIP archive containing all diffs from /var/lang.
"""
from json import load as json_load
from os import lstat, readlink, walk
from stat import S_ISLNK, S_ISREG
from sys import stderr, version_info
from zipfile import ZipFile, ZIP_DEFLATED

def main():
    with open("/baseline.json", "r") as fd:
        baseline = json_load(fd)

    files = set()
    base_dir = "/var/lang"
    for path, subdirs, filenames in walk(base_dir):
        for filename in filenames:
            pathname = path + "/" + filename
            s = lstat(pathname)
            base = baseline.get(pathname)

            if (base is None or
                (S_ISLNK(s.st_mode) and (
                    base["type"] != "link" or
                    base["target"] != readlink(pathname))) or
                (S_ISREG(s.st_mode) and (
                    base["type"] != "file" or
                    base["size"] != s.st_size or
                    base["mode"] != s.st_mode))):
                files.add(pathname[len(base_dir) + 1:])

    maj_min = "%d.%d" % (version_info[0], version_info[1])
    zipname = "/certbot-layer-%s.zip" % maj_min

    # Only Python 3.7+ has the compresslevel parameter.
    if version_info[0] > 3 or version_info[0] == 3 and version_info[1] >= 7:
        zip_kw = {"compresslevel": 9}
    else:
        zip_kw = {}

    with ZipFile(zipname, "w", compression=ZIP_DEFLATED, **zip_kw) as z:
        for filename in files:
            z.write(base_dir + "/" + filename, arcname=filename,)
            print("Adding %s" % filename)

if __name__ == "__main__":
    main()
