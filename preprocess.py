#!/usr/bin/env python3
from io import StringIO
import json

def preprocess(obj, s):
    pos = 0
    s_len = len(s)
    result = StringIO()

    while pos < s_len:
        next_start = s.find("@@{", pos)
        if next_start == -1:
            result.write(s[pos:])
            break

        result.write(s[pos:next_start])
        next_end = s.find("}@@", next_start)
        assert next_end != -1

        var = s[next_start + 3:next_end]
        pos = next_end + 3

        elements = var.split(".")
        tree = obj
        for el in elements:
            tree = tree[el]

        result.write(tree)

    return result.getvalue()

def main():
    with open("versions.json", "r") as fd:
        versions = json.load(fd)

    with open("certbot-to-acm.yaml.in", "r") as ifd:
        infile = ifd.read()

    outfile = preprocess(versions, infile)

    with open("certbot-to-acm.yaml", "w") as ofd:
        ofd.write(outfile)

if __name__ == "__main__":
    main()
