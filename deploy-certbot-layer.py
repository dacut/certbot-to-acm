#!/usr/bin/env python3
"""\
Usage: deploy-certbot-layer.py <pyver>...
Deploy certbot layers. The <pyver> arguments are 3.6, 3.7, 3.8, etc.

Options:
    -h | --help
        Show this usage information.
"""
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from dataclasses import dataclass, field
from getopt import getopt, GetoptError
from sys import argv, exit as sys_exit, stderr, stdout
from typing import Dict, List, NamedTuple, Optional, Set
from boto3.session import Session


PROFILES = ("iono", "iono-gov")


@dataclass
class LayerVersionInfo:
    """
    Information about the deployment of a CertBot layer for a given region and Python version.
    """
    python_version: str
    s3_key: str
    s3_object_version: str
    lambda_layer_version: int


@dataclass
class RegionInfo:
    """
    Information about a region and the CertBot layers uploaded there.
    """
    region_name: str
    s3_bucket: Optional[str] = None
    version_info: Dict[str, LayerVersionInfo] = field(default_factory=dict)


@dataclass
class AccountInfo:
    """
    Information about a given AWS account
    """
    account_id: str
    partition: str
    regions: Set[str]

    @classmethod
    def for_profile(cls, profile_name: str) -> "AccountInfo":
        """
        Returns account information given the profile name. Credentials should be stored in ~/.aws/credentials.
        """
        return cls.for_session(Session(profile_name=profile_name))
    

    @classmethod
    def for_session(cls, session: Session) -> "AccountInfo":
        """
        Returns account information given a Boto3 session.
        """
        sts = session.client("sts")
        ec2 = session.client("ec2")
        cid = sts.get_caller_identity()
        account_id = cid["Account"]
        partition = cid["Arn"].split(":")[1]
        regions = set([region["RegionName"] for region in ec2.describe_regions()["Regions"]])

        return cls(account_id=account_id, partition=partition, regions=regions)


def main(args):
    """
    Main program entrypoint.
    """
    try:
        opts, args = getopt(args, "h", ["help"])

        for opt, val in opts:
            if opt in ["-h", "--help"]:
                usage(stdout)
                return 0
    except GetoptError as e:
        print(e, file=stderr)
        usage()
        return 2
    
    profile_to_account_info = {profile: AccountInfo.for_profile(profile) for profile in PROFILES}
    executor = ThreadPoolExecutor()
    futures = []
    for profile, account_info in profile_to_account_info.items():
        for region in account_info.regions:
            print(f"Submitting {profile}/{region}")
            futures.append(executor.submit(send_versions, profile, region, args))
    
    for future in wait(futures, return_when=ALL_COMPLETED)[0]:
        exc = future.exception()
        if exc is not None:
            print(exc, file=stderr)
    
    return 0


def send_versions(profile: str, region: str, versions: List[str]) -> None:
    b3 = Session(profile_name=profile, region_name=region)
    s3 = b3.client("s3")
    lam = b3.client("lambda")

    s3_bucket = f"ionosphere-public-{region}"

    for ver in versions:
        filename = f"lambda-layers/certbot-layer-py{ver}.zip"
        layer_name = f"certbot-py{ver.replace('.', '')}"
        print(f"Writing {filename} to {region}")
        with open(filename, "rb") as fd:
            s3_result = s3.put_object(ACL="public-read", Body=fd, Bucket=s3_bucket, Key=filename)
            s3_version = s3_result["VersionId"]

        print(f"Publishing Lambda layer for {region}/{ver}")
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


def usage(fd=stderr):
    fd.write(__doc__)


if __name__ == "__main__":
    sys_exit(main(argv[1:]))
