"""
Lambda entrypoint for handling Certbot renewals.
"""
# pylint: disable=invalid-name
from fnmatch import fnmatch
from os import makedirs, unlink, walk
from os.path import exists
from re import fullmatch
from shutil import rmtree
from sys import stderr
from typing import Any, Dict, List, Optional
from zipfile import ZipFile, ZIP_DEFLATED

from botocore.exceptions import ClientError
import boto3
import certbot.main

DEFAULT_ENDPOINT = "https://acme-staging-v02.api.letsencrypt.org/directory"
DEFAULT_RSA_KEY_SIZE = 2048
DEFAULT_KMS_KEY = "alias/aws/s3"
VALID_RSA_KEY_SIZES = (2048, 3072, 4096,)
CERTBOT_TEMP_DIR = "/tmp/certbot"
CERTBOT_CONFIG_ZIP = "/tmp/certbot-config.zip"
CERTBOT_CONFIG_DIR = f"{CERTBOT_TEMP_DIR}/config"
CERTBOT_WORK_DIR = f"{CERTBOT_TEMP_DIR}/work"
CERTBOT_LOG_DIR = f"{CERTBOT_TEMP_DIR}/log"

CERT_FILENAME_PATTERN = f"{CERTBOT_CONFIG_DIR}/live/*/cert.pem"
CHAIN_FILENAME_PATTERN = f"{CERTBOT_CONFIG_DIR}/live/*/chain.pem"
KEY_FILENAME_PATTERN = f"{CERTBOT_CONFIG_DIR}/live/*/privkey.pem"

def get_certificate_tags(arn: str) -> Dict[str, str]:
    """
    Return the tags for the specified certificate.
    """
    acm = boto3.client("acm")
    result = acm.list_tags_for_certificate(CertificateArn=arn)
    return {item["Key"]: item["Value"] for item in result["Tags"]}

def get_list_certs_kw(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return the keyword arguments to use for list_certificates given the
    list of filters.
    """
    acm_kw = {}
    includes = {}

    status = filters.get("status")
    if status:
        if isinstance(status, str):
            status = [status]
        acm_kw["CertificateStatuses"] = status

    key_type = filters.get("key-type")
    if key_type:
        if isinstance(key_type, str):
            key_type = [key_type]
        includes["keyTypes"] = key_type

    key_usage = filters.get("key_usage")
    if key_usage:
        if isinstance(key_usage, str):
            key_usage = [key_usage]
        includes["keyUsage"] = key_usage

    extended_key_usage = filters.get("extended_key_usage")
    if extended_key_usage:
        if isinstance(extended_key_usage, str):
            extended_key_usage = [extended_key_usage]
        includes["extendedKeyUsage"] = extended_key_usage

    if includes:
        acm_kw["Includes"] = includes

    return acm_kw

def find_existing_certificate(
        arn: Optional[str], filters: Dict[str, Any]) -> Optional[str]:
    """
    Search ACM for an existing certificate matching the specified ARN or
    the list of filters.
    """
    acm = boto3.client("acm")

    if arn:
        try:
            result = acm.get_certificate(CertificateArn=arn)
            if "Certificate" not in result:
                raise ValueError(f"Invalid certificate ARN: {arn}")
        except ClientError as e:
            raise ValueError(f"Invalid certificate ARN: {arn} ({e})")

    cert_summaries = []
    acm_kw = get_list_certs_kw(filters)

    while True:
        print(f"Calling list_certificates with kw={acm_kw}")
        result = acm.list_certificates(**acm_kw)
        for cert_summary in result.get("CertificateSummaryList", []):
            cert_summaries.append(cert_summary)

        next_token = result.get("NextToken")
        if not next_token:
            break

        acm_kw["NextToken"] = next_token

    domain_name = filters.get("domain")
    if domain_name:
        # Filter out any certificates whose domain name doesn't match
        cert_summaries = [
            cs for cs in cert_summaries if cs.get("DomainName") == domain_name]

    if len(cert_summaries) == 0:
        return None

    if len(cert_summaries) == 1:
        return cert_summaries[0]["CertificateArn"]

    raise ValueError(
        "Multiple certificates found: " +
        " ".join([cs["CertificateArn"] for cs in cert_summaries]))

def download_certbot_config(config_bucket: str, config_key: str) -> None:
    """
    Download the configuration ZIP file from S3 and extract it to the certbot
    config directory.
    """
    s3 = boto3.client("s3")
    try:
        s3.download_file(
            Bucket=config_bucket, Key=config_key,
            Filename=CERTBOT_CONFIG_ZIP)
        with ZipFile(CERTBOT_CONFIG_ZIP, "r") as z:
            z.extractall("/tmp/certbot/config")
        unlink(CERTBOT_CONFIG_ZIP)
    except ClientError as e:
        if e.response.get("Error", {}).get("Message") == "Not Found":
            return
        raise

def create_config_zip() -> Dict[str, bytes]:
    """
    Create the configuration ZIP file for storage in S3 and return
    a dictionary containing Certificate, CertificateChain, and PrivateKey
    with those elements found.
    """
    acm_args = {}

    with ZipFile(CERTBOT_CONFIG_ZIP, "w", compression=ZIP_DEFLATED) as z:
        for path, _, filenames in walk(CERTBOT_CONFIG_DIR):
            for filename in filenames:
                pathname = path + "/" + filename
                relpath = pathname[len(CERTBOT_CONFIG_DIR) + 1:]
                print(f"Adding {relpath} to archive")
                z.write(pathname, relpath)

                if fnmatch(pathname, CERT_FILENAME_PATTERN):
                    with open(pathname, "rb") as fd:
                        acm_args["Certificate"] = fd.read()
                elif fnmatch(pathname, CHAIN_FILENAME_PATTERN):
                    with open(pathname, "rb") as fd:
                        acm_args["CertificateChain"] = fd.read()
                elif fnmatch(pathname, KEY_FILENAME_PATTERN):
                    with open(pathname, "rb") as fd:
                        acm_args["PrivateKey"] = fd.read()

    return acm_args

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda entry point. The input event has the following fields:
    {
        "acm-certificate-arn": "arn:aws:acm:<region>:<account-id>:certificate/...",
        "acm-certificate-filters": {
            "domain": "dns.domain.name",
            "extended-key-usage": [
                "TLS_WEB_SERVER_AUTHENTICATION",
                "TLS_WEB_CLIENT_AUTHENTICATION", "CODE_SIGNING",
                "EMAIL_PROTECTION", "TIME_STAMPING", "OCSP_SIGNING",
                "IPSEC_END_SYSTEM", "IPSEC_TUNNEL", "IPSEC_USER", "ANY",
                "NONE", "CUSTOM"
            ],
            "key-type": [
                "RSA_1024", "RSA_2048", "RSA_4096", "EC_prime256v1",
                "EC_secp384r1", "EC_secp521r1"],
            "key-usage": [
                "DIGITAL_SIGNATURE", "NON_REPUDIATION", "KEY_ENCIPHERMENT",
                "DATA_ENCIPHERMENT", "KEY_AGREEMENT", "CERTIFICATE_SIGNING",
                "CRL_SIGNING", "ENCIPHER_ONLY", "DECIPHER_ONLY", "ANY",
                "CUSTOM"],
            "status": [
                "PENDING_VALIDTION", "ISSUED", "INACTIVE", "EXPIRED",
                "VALIDATION_TIMED_OUT", "REVOKED", "FAILED"],
            "type": ["AMAZON_ISSUED", "IMPORTED"],
        },
        "agree-tos": true,
        "config-store-url": "s3://bucket/key.tar.gz",
        "config-store-kms-key": "alias/key-name",
        "domains": ["name1.example.com", "name2.example.com", ...],
        "email": "email@example.com",
        "endpoint": "https://acme-staging-v02.api.letsencrypt.org/directory",
        "rsa-key-size": 2048
    }

    *   acm-certificate-arn is optional. If set, any new certificates are
        imported into this ACM certificate.
    *   acm-certificate-filters is a list of filters to use to find an existing
        certificate to import into. This must return zero or one certificates.
    *   agree-tos is NOT optional and must be set.
    *   config-store-url is NOT optional and must be an
        s3://<bucket>/<key> URL. The certbot config directory is stored here
        as a ZIP archive.
    *   config-store-kms-key is a KMS alias or ARN used to encrypt the certbot
        config archive. If omitted, it defaults to "alias/aws/s3".
    *   endpoint is optional and defaults to the LetsEncrypt staging server.
    *   rsa-key-size is optional and defaults to 2048.
    """
    acm_certificate_arn = event.get("acm-certificate-arn")
    acm_certificate_filters = event.get("acm-certificate-filters", {})
    agree_tos = event.get("agree-tos")
    config_store_url = event.get("config-store-url")
    config_store_kms_key = event.get("config-store-kms-key", DEFAULT_KMS_KEY)
    domains = event.get("domains", [])
    email = event.get("email")
    endpoint = event.get("endpoint", DEFAULT_ENDPOINT)
    rsa_key_size = event.get("rsa-key-size", DEFAULT_RSA_KEY_SIZE)

    errors = []
    if not agree_tos:
        errors.append("agree-tos must be specified and set to true")

    if not config_store_url:
        errors.append("config-store-url must be specified")
    else:
        m = fullmatch(r"s3://([a-z0-9][-\.a-z0-9]*)/(.*)", config_store_url)
        if not m:
            errors.append("config-store-url is not a valid s3:// url")
        else:
            config_bucket = m.group(1)
            config_key = m.group(2)

    if not domains:
        errors.append("domains not specified or is empty")

    if rsa_key_size not in VALID_RSA_KEY_SIZES:
        errors.append(
            f"rsa-key-size must be one of {', '.join(VALID_RSA_KEY_SIZES)}: "
            f"{rsa_key_size}")

    if errors:
        raise ValueError("Invalid event: " + '\n'.join(errors))

    acm = boto3.client("acm")
    if acm_certificate_arn or acm_certificate_filters:
        acm_certificate_arn = find_existing_certificate(
            acm_certificate_arn, acm_certificate_filters)

    if exists(CERTBOT_CONFIG_DIR):
        rmtree(CERTBOT_CONFIG_DIR)
    if exists(CERTBOT_WORK_DIR):
        rmtree(CERTBOT_WORK_DIR)
    if exists(CERTBOT_LOG_DIR):
        rmtree(CERTBOT_LOG_DIR)

    makedirs(CERTBOT_CONFIG_DIR)
    makedirs(CERTBOT_WORK_DIR)
    makedirs(CERTBOT_LOG_DIR)

    download_certbot_config(config_bucket, config_key)

    cmd = [
        "certonly", "--non-interactive",
        "--preferred-challenges", "dns",
        "--user-agent-comment", "certbot-to-acm/0.1",
        "--agree-tos",
        "--config-dir", CERTBOT_CONFIG_DIR,
        "--work-dir", CERTBOT_WORK_DIR,
        "--logs-dir", CERTBOT_LOG_DIR,
        "--server", endpoint,
        "--dns-route53",
    ]

    if email:
        cmd += ["--email", email]
    else:
        cmd += ["--register-unsafely-without-email"]

    if isinstance(domains, str):
        domains = [domains]

    for domain in domains:
        cmd += ["--domain", domain]

    result = certbot.main.main(cmd)
    if result:
        print(f"certbot command failed: {result}", file=stderr)
        raise RuntimeError(
            f"certbot command exited with exit code {result}")

    acm_args = create_config_zip()

    if "Certificate" not in acm_args:
        raise ValueError("Did not find certificate")

    if "CertificateChain" not in acm_args:
        raise ValueError("Did not find certificate chain")

    if "PrivateKey" not in acm_args:
        raise ValueError("Did not find private key")

    with open(CERTBOT_CONFIG_ZIP, "rb") as fd:
        s3 = boto3.client("s3")
        s3.put_object(
            ACL='private', Body=fd, Bucket=config_bucket, Key=config_key,
            ServerSideEncryption="aws:kms", SSEKMSKeyId=config_store_kms_key)
    unlink(CERTBOT_CONFIG_ZIP)

    if acm_certificate_arn:
        acm_args["CertificateArn"] = acm_certificate_arn

    acm.import_certificate(**acm_args)

    return {}
