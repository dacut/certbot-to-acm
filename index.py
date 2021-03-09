"""
Lambda entrypoint for handling Certbot renewals.
"""
# pylint: disable=invalid-name
from fnmatch import fnmatch
from hashlib import sha256
from logging import getLogger
from os import chmod, scandir, lstat, makedirs, symlink, unlink, walk
from os.path import basename, isdir
from re import compile as re_compile, fullmatch
from shutil import rmtree
from stat import S_ISLNK, S_ISREG
from sys import stderr
from tarfile import open as tarfile_open
from tempfile import TemporaryFile, TemporaryDirectory
from typing import Any, Dict, NamedTuple, Optional, Set

from botocore.exceptions import ClientError
import boto3
import certbot.main


class CertbotCertificate(NamedTuple):
    certificate: bytes
    chain: bytes
    full_chain: bytes
    private_key: bytes


STAGING_ENDPOINT = "https://acme-staging-v02.api.letsencrypt.org/directory"
PRODUCTION_ENDPOINT = "https://acme-v02.api.letsencrypt.org/directory"
DEFAULT_ENDPOINT = STAGING_ENDPOINT
DEFAULT_RSA_KEY_SIZE = 2048
DEFAULT_KMS_KEY = "alias/aws/s3"
DEFAULT_SSM_KMS_KEY = "alias/aws/ssm"
DEFAULT_SSM_TIER = "Standard"
VALID_RSA_KEY_SIZES = (2048, 3072, 4096)

CERT_FILENAME_PATTERN = "live/*/cert.pem"
CHAIN_FILENAME_PATTERN = "live/*/chain.pem"
FULLCHAIN_FILENAME_PATTERN = "live/*/fullchain.pem"
KEY_FILENAME_PATTERN = "live/*/privkey.pem"

# Regular expression for Certbot directories that are valid
VALID_DOMAIN_DIR_MATCHER = re_compile(
    r"(?P<domain>(?:[0-9a-z][-0-9a-z]*[0-9a-z]|[0-9a-z])(?:\.(?:[0-9a-z][-0-9a-z]*[0-9a-z]|[0-9a-z]))*)"
)

# Regular expression for Certbot directories that were created because symbolic links/permissions were an issue
MOVED_DOMAIN_DIR_MATCHER = re_compile(
    r"(?P<domain>(?:[0-9a-z][-0-9a-z]*[0-9a-z]|[0-9a-z])(?:\.(?:[0-9a-z][-0-9a-z]*[0-9a-z]|[0-9a-z]))*)-[0-9]{4}"
)

# Archived filenames
ARCHIVED_FILE_MATCHER = re_compile(r"(?P<filetype>cert|chain|fullchain|privkey)(?P<version>[0-9]+)\.pem")

# All filetypes that Certbot produces
ALL_FILETYPES = ("cert", "chain", "fullchain", "privkey")

s3 = boto3.client("s3")
ssm = boto3.client("ssm")
log = getLogger()


def get_list_certs_kw(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return the keyword arguments to use for list_certificates given the list of filters.
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


def find_existing_certificate(arn: Optional[str], filters: Dict[str, Any]) -> Optional[str]:
    """
    Search ACM for an existing certificate matching the specified ARN or the list of filters.
    """
    acm = boto3.client("acm")

    if arn:
        try:
            result = acm.get_certificate(CertificateArn=arn)
            if "Certificate" not in result:
                raise ValueError(f"Invalid certificate ARN: {arn}")
            return arn
        except ClientError as e:
            raise ValueError(f"Invalid certificate ARN: {arn} ({e})")

    cert_summaries = []
    acm_kw = get_list_certs_kw(filters)

    while True:
        print(f"Calling list_certificates with kw={acm_kw}")
        list_result = acm.list_certificates(**acm_kw)
        for cert_summary in list_result.get("CertificateSummaryList", []):
            cert_summaries.append(cert_summary)

        next_token = list_result.get("NextToken")
        if not next_token:
            break

        acm_kw["NextToken"] = next_token

    domain_name = filters.get("domain")
    if domain_name:
        # Filter out any certificates whose domain name doesn't match
        cert_summaries = [cs for cs in cert_summaries if cs.get("DomainName") == domain_name]

    if len(cert_summaries) == 0:
        return None

    if len(cert_summaries) == 1:
        return cert_summaries[0]["CertificateArn"]

    raise ValueError("Multiple certificates found: " + " ".join([cs["CertificateArn"] for cs in cert_summaries]))


def download_certbot_config(config_bucket: str, config_key: str, certbot_config_dir: str, certbot_work_dir: str) -> None:
    """
    Download the configuration tar file from S3 and extract it to the certbot config directory.
    """
    with TemporaryFile(prefix="config", suffix=".tar.gz", dir=certbot_work_dir) as fd:
        try:
            result = s3.get_object(Bucket=config_bucket, Key=config_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return
            raise

        body = result["Body"]
        first_chunk = True

        while True:
            chunk = body.read(65536)
            if not chunk:
                break
            
            if first_chunk:
                if chunk[:4] == b'\x50\x4b\x03\x04':
                    # Legacy ZIP file -- don't use
                    return
                first_chunk = False

            fd.write(chunk)

        fd.seek(0)

        with tarfile_open(fd, "r") as tf:
            tf.extractall(certbot_config_dir)


def create_config_tarfile(config_dir: str, config_tarfile: str) -> CertbotCertificate:
    """
    Create the configuration tar file for storage in S3 and return a dictionary containing Certificate, CertificateChain, and
    PrivateKey with those elements found.
    """
    certificate = None
    chain = None
    full_chain = None
    private_key = None

    with tarfile_open(config_tarfile, "w:gz") as tf:
        for path, _, filenames in walk(config_dir):
            for filename in filenames:
                pathname = path + "/" + filename
                relpath_strip = len(config_dir) + 1
                relpath = pathname[relpath_strip:]
                print(f"Adding {relpath} to archive")
                tf.add(pathname, relpath, recursive=False)

                if fnmatch(relpath, CERT_FILENAME_PATTERN):
                    with open(pathname, "rb") as fd:
                        certificate = fd.read()
                elif fnmatch(relpath, CHAIN_FILENAME_PATTERN):
                    with open(pathname, "rb") as fd:
                        chain = fd.read()
                elif fnmatch(relpath, FULLCHAIN_FILENAME_PATTERN):
                    with open(pathname, "rb") as fd:
                        full_chain = fd.read()
                elif fnmatch(relpath, KEY_FILENAME_PATTERN):
                    with open(pathname, "rb") as fd:
                        private_key = fd.read()

    if certificate is None:
        raise ValueError(f"Did not find live certificate in {config_dir}")

    if chain is None:
        raise ValueError(f"Did not find intermediate certificate in {config_dir}")

    if full_chain is None:
        raise ValueError(f"Did not find full certificate chain in {config_dir}")

    if private_key is None:
        raise ValueError(f"Did not find private key in {config_dir}")

    return CertbotCertificate(certificate=certificate, chain=chain, full_chain=full_chain, private_key=private_key)


def get_ssm_parameter(parameter_name: str) -> Optional[str]:
    """
    Return the given SSM parameter, or None if it doesn't exist.
    """
    try:
        result = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        return result["Parameter"]["Value"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ParameterNotFound":
            return None
        raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda entry point. The input event has the following fields:
    {
        "acm-certificate-arn": "arn:aws:acm:<region>:<account-id>:certificate/...",
        "acm-certificate-filters": {
            "domain": "dns.domain.name",
            "extended-key-usage": [
                "TLS_WEB_SERVER_AUTHENTICATION", "TLS_WEB_CLIENT_AUTHENTICATION", "CODE_SIGNING", "EMAIL_PROTECTION",
                "TIME_STAMPING", "OCSP_SIGNING", "IPSEC_END_SYSTEM", "IPSEC_TUNNEL", "IPSEC_USER", "ANY", "NONE", "CUSTOM"
            ],
            "key-type": ["RSA_1024", "RSA_2048", "RSA_4096", "EC_prime256v1", "EC_secp384r1", "EC_secp521r1"],
            "key-usage": [
                "DIGITAL_SIGNATURE", "NON_REPUDIATION", "KEY_ENCIPHERMENT", "DATA_ENCIPHERMENT", "KEY_AGREEMENT",
                "CERTIFICATE_SIGNING", "CRL_SIGNING", "ENCIPHER_ONLY", "DECIPHER_ONLY", "ANY", "CUSTOM"],
            "status": ["PENDING_VALIDTION", "ISSUED", "INACTIVE", "EXPIRED", "VALIDATION_TIMED_OUT", "REVOKED", "FAILED"],
            "type": ["AMAZON_ISSUED", "IMPORTED"],
        },
        "agree-tos": true,
        "config-store-url": "s3://bucket/key.tar.gz",
        "config-store-kms-key": "alias/key-name",
        "domains": ["name1.example.com", "name2.example.com", ...],
        "email": "email@example.com",
        "endpoint": "https://acme-staging-v02.api.letsencrypt.org/directory",
        "rsa-key-size": 2048,
        "ssm-parameter-prefix": "/path/parameter",
        "ssm-kms-key": "alias/key-name"
    }

    *   acm-certificate-arn is optional. If set, any new certificates are imported into this ACM certificate.
    *   acm-certificate-filters is a list of filters to use to find an existing certificate to import into. This must return zero
        or one certificates.
    *   agree-tos is NOT optional and must be set.
    *   config-store-url is NOT optional and must be an s3://<bucket>/<key> URL. The certbot config directory is stored here as a
        tar.gz archive.
    *   config-store-kms-key is a KMS alias or ARN used to encrypt the certbot config archive. If omitted, it defaults
        to "alias/aws/s3".
    *   endpoint is optional and defaults to the LetsEncrypt staging server.
    *   rsa-key-size is optional and defaults to 2048.
    *   ssm-parameter-prefix is optional. If set, the resulting certificate, chain, and key files are save to the SSM parameter
        store under the given prefix.
    *   ssm-kms-key is optional. If ssm-parameter-prefix is set, this specifies the KMS alias or ARN used to encrypt the TLS key.
        If omitted, it defaults to "alias/aws/ssm".
    *   ssm-tier is optional and defaults to "Standard". Use "Advanced" to enable the use of advanced SSM features.
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
    ssm_parameter_prefix = event.get("ssm-parameter-prefix")
    ssm_kms_key = event.get("ssm-kms-key", DEFAULT_SSM_KMS_KEY)
    ssm_tier = event.get("ssm-tier", DEFAULT_SSM_TIER)

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
        errors.append(f"rsa-key-size must be one of {', '.join([str(s) for s in VALID_RSA_KEY_SIZES])}: " f"{rsa_key_size}")

    if errors:
        raise ValueError("Invalid event: " + "\n".join(errors))

    acm = boto3.client("acm")
    if acm_certificate_arn or acm_certificate_filters:
        acm_certificate_arn = find_existing_certificate(acm_certificate_arn, acm_certificate_filters)

    with TemporaryDirectory("certbot") as certbot_base_dir:
        certbot_config_dir = f"{certbot_base_dir}/config"
        certbot_work_dir = f"{certbot_base_dir}/work"
        certbot_log_dir = f"{certbot_base_dir}/log"
        certbot_config_tarfile = f"{certbot_base_dir}/config.tar.gz"

        makedirs(certbot_config_dir)
        makedirs(certbot_work_dir)
        makedirs(certbot_log_dir)

        download_certbot_config(config_bucket, config_key, certbot_config_dir, certbot_work_dir)

        cmd = [
            "certonly", "--non-interactive", "--preferred-challenges", "dns", "--user-agent-comment", "certbot-to-acm/0.1",
            "--agree-tos", "--config-dir", certbot_config_dir, "--work-dir", certbot_work_dir, "--logs-dir", certbot_log_dir,
            "--server", endpoint, "--dns-route53",
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
            raise RuntimeError(f"certbot command exited with exit code {result}")

        certbot_cert = create_config_tarfile(certbot_config_dir, certbot_config_tarfile)
        with open(certbot_config_tarfile, "rb") as fd:
            s3.put_object(
                ACL="private", Body=fd, Bucket=config_bucket, Key=config_key, ServerSideEncryption="aws:kms",
                SSEKMSKeyId=config_store_kms_key)
        unlink(certbot_config_tarfile)

        acm_args = {}
        if acm_certificate_arn:
            acm_args["CertificateArn"] = acm_certificate_arn
        acm.import_certificate(
            Certificate=certbot_cert.certificate, CertificateChain=certbot_cert.chain, PrivateKey=certbot_cert.private_key,
            **acm_args)

        if ssm_parameter_prefix:
            if not ssm_parameter_prefix.startswith("/"):
                ssm_parameter_prefix = "/" + ssm_parameter_prefix
            if not ssm_parameter_prefix.endswith("/"):
                ssm_parameter_prefix = ssm_parameter_prefix + "/"

            existing_cert = get_ssm_parameter(f"{ssm_parameter_prefix}cert")
            existing_chain = get_ssm_parameter(f"{ssm_parameter_prefix}chain")
            existing_fullchain = get_ssm_parameter(f"{ssm_parameter_prefix}fullchain")
            existing_key = get_ssm_parameter(f"{ssm_parameter_prefix}key")

            cert = certbot_cert.certificate.decode("utf-8")
            chain = certbot_cert.chain.decode("utf-8")
            fullchain = certbot_cert.full_chain.decode("utf-8")
            key = certbot_cert.private_key.decode("utf-8")

            if existing_cert != cert:
                ssm.put_parameter(
                    Name=f"{ssm_parameter_prefix}cert", Description=f"TLS certificate for {' '.join(domains)}", Overwrite=True,
                    Value=cert, Type="String", Tier=ssm_tier)
            if existing_chain != chain:
                ssm.put_parameter(
                    Name=f"{ssm_parameter_prefix}chain", Description=f"TLS intermediate for {' '.join(domains)}", Overwrite=True,
                    Value=chain, Type="String", Tier=ssm_tier)
            if existing_fullchain != fullchain:
                ssm.put_parameter(
                    Name=f"{ssm_parameter_prefix}fullchain", Description=f"TLS fullchain for {' '.join(domains)}", Overwrite=True,
                    Value=fullchain, Type="String", Tier=ssm_tier)
            if existing_key != key:
                ssm.put_parameter(
                    Name=f"{ssm_parameter_prefix}privkey", Description=f"TLS key for {' '.join(domains)}", KeyId=ssm_kms_key,
                    Overwrite=True, Value=key, Type="SecureString", Tier=ssm_tier)

    return {}
