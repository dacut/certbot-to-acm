#!/usr/bin/env python3
"""\
Usage: deploy-certbot-layer.py [--region <region>] <python-version>...
Deploy certbot layers.

Options:
    -h | --help
        Show this usage information.

    -r <region> | --region <region>
        Use the specified AWS region. This must be specified.
"""
from getopt import getopt, GetoptError
from sys import argv, exit as sys_exit, stderr, stdout
from boto3.session import Session


def main(args):
    region = None
    try:
        opts, args = getopt(args, "hr:", ["help", "region="])

        for opt, val in opts:
            if opt in ["-h", "--help"]:
                usage(stdout)
                return 0
            if opt in ["-r", "--region"]:
                region = val
    except GetoptError as e:
        print(e, file=stderr)
        usage()
        return 2

    if region is None:
        print("--region must be specified", file=stderr)
        usage()
        return 2

    b3 = Session(region_name=region)
    s3 = b3.client("s3")
    lam = b3.client("lambda")

    s3_bucket = f"ionosphere-public-{region}"

    for ver in args:
        filename = f"certbot-layer-py{ver}.zip"
        layer_name = f"certbot-py{ver.replace('.', '')}"
        with open(filename, "rb") as fd:
            s3_result = s3.put_object(ACL="public-read", Body=fd, Bucket=s3_bucket, Key=filename)
            s3_version = s3_result["VersionId"]

        lam_result = lam.publish_layer_version(
            LayerName=layer_name,
            Description=f"Certbot for Python {ver}",
            Content={
                "S3Bucket": s3_bucket,
                "S3Key": filename,
                "S3ObjectVersion": s3_version,
            },
            CompatibleRuntimes=[f"python{ver}"],
            LicenseInfo="Apache-2.0",
        )
        lam_ver = lam_result["Version"]

        lam.add_layer_version_permission(
            LayerName=layer_name, VersionNumber=lam_ver, StatementId="Public", Action="lambda:GetLayerVersion", Principal="*"
        )

    return 0


def usage(fd=stderr):
    fd.write(__doc__)


if __name__ == "__main__":
    sys_exit(main(argv[1:]))
