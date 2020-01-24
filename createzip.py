#!/usr/bin/env python3
"""
Create a ZIP archive containing all diffs from /var/lang.
"""
from fnmatch import fnmatch
from os import chdir, walk
from stat import S_ISLNK, S_ISREG
from sys import stderr, version_info
from zipfile import ZipFile, ZIP_DEFLATED

excluded = {
    "lib/python*/site-packages/boto3-*",
    "lib/python*/site-packages/boto3/*",
    "lib/python*/site-packages/botocore-*",
    "lib/python*/site-packages/botocore/*",
    "lib/python*/site-packages/easy_install.py",
    "lib/python*/site-packages/pip/*",
    "lib/python*/site-packages/pip-*",
    "lib/python*/site-packages/s3transfer/*",
    "lib/python*/site-packages/s3transfer-*",
    "lib/python*/site-packages/setuptools/*",
    "lib/python*/site-packages/setuptools-*",
    "lib/python*/site-packages/wheel/*",
    "lib/python*/site-packages/wheel-*",
    "lib/python*/site-packages/zope/component/testfiles/*",
    "lib/python*/site-packages/zope/component/testing.py",
    "lib/python*/site-packages/zope/component/tests/*",
    "lib/python*/site-packages/zope/deferredimport/samples/*",
    "lib/python*/site-packages/zope/event/tests.py",
    "lib/python*/site-packages/zope/hookable/tests/*",
    "lib/python*/site-packages/zope/interface/_zope_interface_coptimizations.c",
    "lib/python*/site-packages/zope/interface/common/tests/*",
    "lib/python*/site-packages/zope/interface/tests/*",
    "lib/python*/site-packages/zope/proxy/tests/*",
}

def main():
    maj_min = f"{version_info[0]}.{version_info[1]}"
    base_dir = "/tmp/venv"
    site_packages = f"{base_dir}/lib/python{maj_min}/site-packages"

    # Add certbot, distro, and jws from /bin
    files = ["bin/certbot", "bin/distro", "bin/jws"]

    # Add everything from site-packages
    for path, subdirs, filenames in walk(site_packages):
        for filename in filenames:
            pathname = path + "/" + filename
            assert pathname.startswith(base_dir + "/")
            relpath = pathname[len(base_dir) + 1:]
            for excluded_path in excluded:
                if fnmatch(relpath, excluded_path):
                    # Don't include this file;
                    break
            else:
                files.append(relpath)

    files.sort()
    zipname = "/certbot-layer-py%s.zip" % maj_min

    # Only Python 3.7+ has the compresslevel parameter.
    if version_info[0] > 3 or version_info[0] == 3 and version_info[1] >= 7:
        zip_kw = {"compresslevel": 9}
    else:
        zip_kw = {}

    with ZipFile(zipname, "w", compression=ZIP_DEFLATED, **zip_kw) as z:
        for relpath in files:
            print("Adding %s" % relpath)
            z.write(base_dir + "/" + relpath, arcname=f"python/{relpath}",)

if __name__ == "__main__":
    main()
