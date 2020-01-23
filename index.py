"""
Lambda entrypoint for handling Certbot renewals.
"""
import certbot.main
from os import makedirs, walk
from sys import stderr
from typing import Any, Dict

DEFAULT_ENDPOINT = "https://acme-staging-v02.api.letsencrypt.org/directory"
DEFAULT_RSA_KEY_SIZE = 2048
VALID_RSA_KEY_SIZES = (2048, 3072, 4096,)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda entry point. The input event has the following fields:
    {
        "acm-certificate": "arn:aws:acm:<region>:<account-id>:certificate/...",
        "agree-tos": true,
        "domains": ["name1.example.com", "name2.example.com", ...],
        "email": "email@example.com",
        "endpoint": "https://acme-staging-v02.api.letsencrypt.org/directory",
        "rsa-key-size": 2048
    }

    agree-tos is NOT optional and must be set.
    endpoint is optional and defaults to the LetsEncrypt staging server.
    rsa-key-size is optional and defaults to 2048.
    """
    acm_certificate = event.get("acm-certificate")
    agree_tos = event.get("agree-tos")
    domains = event.get("domains", [])
    email = event.get("email")
    endpoint = event.get("endpoint", DEFAULT_ENDPOINT)
    rsa_key_size = event.get("rsa-key-size", DEFAULT_RSA_KEY_SIZE)

    errors = []
    if acm_certificate is None:
        errors.append("acm-certificate must be specified")

    if not agree_tos:
        errors.append("agree-tos must be specified and set to true")

    if not domains:
        errors.append("domains not specified or is empty")

    if rsa_key_size not in VALID_RSA_KEY_SIZES:
        errors.append(
            f"rsa-key-size must be one of {', '.join(VALID_RSA_KEY_SIZES)}: "
            f"{rsa_key_size}")

    if errors:
        raise ValueError("Invalid event: " + '\n'.join(errors))

    makedirs("/tmp/certbot/config")
    makedirs("/tmp/certbot/work")
    makedirs("/tmp/certbot/log")

    cmd = [
        "certonly", "--non-interactive",
        "--preferred-challenges", "dns",
        "--user-agent-comment", "certbot-to-acm/0.1",
        "--agree-tos",
        "--config-dir", "/tmp/certbot/config",
        "--work-dir", "/tmp/certbot/work",
        "--logs-dirs", "/tmp/certbot/log",
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
    if result != 0:
        print(f"certbot command failed: {result}", file=stderr)
        raise RuntimeError(
            f"certbot command exited with exit code {result}")

    for path, subdirs, filenames in walk("/tmp/certbot/config"):
        for filename in filenames:
            print(path + "/" + filename)

    return {}
