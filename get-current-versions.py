#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor
import json
from boto3.session import Session

LAYER_NAMES = ("certbot-py38",)


def get_layer_versions(region, profile):
    result = {region: {}}
    session = Session(profile_name=profile, region_name=region)
    lam = session.client("lambda")
    for layer_name in LAYER_NAMES:
        max_version = 0
        max_version_arn = None
        runtime = None

        paginator = lam.get_paginator("list_layer_versions")
        for page in paginator.paginate(LayerName=layer_name):
            for layer_version in page.get("LayerVersions", []):
                if layer_version["Version"] > max_version:
                    max_version = layer_version["Version"]
                    max_version_arn = layer_version["LayerVersionArn"]
                    runtime = layer_version["CompatibleRuntimes"][0].replace(".", "")

        if max_version_arn is not None:
            result[region][runtime] = max_version_arn

    return result


def get_zip_versions(region, profile):
    session = Session(profile_name=profile, region_name=region)
    s3 = session.client("s3")
    result = s3.head_object(Bucket=f"ionosphere-public-{region}", Key="certbot-to-acm.zip")
    return {region: {"version": result["VersionId"]}}


def main():
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
        layer_versions_futures = []
        zip_versions_futures = []

        for profile, region in region_profiles:
            layer_versions_futures.append(tpe.submit(get_layer_versions, profile, region))
            zip_versions_futures.append(tpe.submit(get_zip_versions, profile, region))

    layer_versions = {}
    zip_versions = {}

    for future in layer_versions_futures:
        if future.exception() is None:
            layer_versions.update(future.result())

    for future in zip_versions_futures:
        if future.exception() is None:
            zip_versions.update(future.result())

    versions = {
        "Versions": {
            "CertbotLayer": layer_versions,
            "CertbotToACMFunctionZIP": zip_versions,
        }
    }

    with open("versions.json", "w") as fd:
        json.dump(versions, fd, indent=4)


if __name__ == "__main__":
    main()
