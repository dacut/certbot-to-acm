#!/usr/bin/env python3
"""\
Usage: deploy-certbot-to-acm.py [--region <region>]
Deploy certbot-to-acm Lambda function ZIP file.

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
            if opt in ("-h", "--help",):
                usage(stdout)
                return 0
            if opt in ("-r", "--region",):
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
    s3_bucket = f"ionosphere-public-{region}"
    filename = f"certbot-to-acm.zip"
    with open(filename, "rb") as fd:
        s3_result = s3.put_object(
            ACL="public-read", Body=fd, Bucket=s3_bucket, Key=filename)
    return 0

if __name__ == "__main__":
    sys_exit(main(argv[1:]))
