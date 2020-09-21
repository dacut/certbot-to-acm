#!/usr/bin/env python3
from setuptools import setup

setup(
    name="certbot-to-acm",
    version="0.1.0",
    description="Lambda function for retrieving LetsEncrypt certificates and saving them to AWS Certificate Manager",
    url="https://github.com/dacut/certbot-to-acm/",
    py_modules=["index"]
)
