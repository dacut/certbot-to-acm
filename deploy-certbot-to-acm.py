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
from concurrent.futures import ThreadPoolExecutor
from getopt import getopt, GetoptError
from sys import argv, exit as sys_exit, stderr, stdout
from boto3.session import Session

def deploy(region, profile):
    b3 = Session(region_name=region, profile_name=profile)
    s3 = b3.client("s3")
    s3_bucket = f"ionosphere-public-{region}"
    filename = f"certbot-to-acm.zip"
    with open(filename, "rb") as fd:
        s3_result = s3.put_object(
            ACL="public-read", Body=fd, Bucket=s3_bucket, Key=filename)


def main(args):
    with open(".profiles.txt", "r") as fd:
        profiles = fd.read().strip().split("\n")

    region_profiles = []

    for profile in profiles:
        ec2 = Session(profile_name=profile).client("ec2")
        regions = [r["RegionName"] for r in ec2.describe_regions()["Regions"]]
        for region in regions:
            region_profiles.append((region, profile))

    region_profiles.sort()

    with ThreadPoolExecutor(max_workers=2 * len(region_profiles)) as tpe:
        futures = [tpe.submit(deploy, region, profile) for region, profile in region_profiles]

    for future in futures:
        future.result()

    return 0

if __name__ == "__main__":
    sys_exit(main(argv[1:]))
