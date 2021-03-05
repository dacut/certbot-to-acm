FROM lambci/lambda:build-python3.8
RUN python3 -m venv /tmp/venv
ENV VIRTUAL_ENV=/tmp/venv
ENV PATH=/tmp/venv/bin:$PATH
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
RUN yum install -y openssl11-devel
RUN cp /lib64/libssl.so.1.1.1g /lib64/libcrypto.so.1.1.1g /tmp/venv/lib/python3.8/site-packages/
RUN ln -s libssl.so.1.1.1g /tmp/venv/lib/python3.8/site-packages/libssl.so.1.1 && \
ln -s libssl.so.1.1.1g /tmp/venv/lib/python3.8/site-packages/libssl.so && \
ln -s libcrypto.so.1.1.1g /tmp/venv/lib/python3.8/site-packages/libcrypto.so.1.1 && \
ln -s libcrypto.so.1.1.1g /tmp/venv/lib/python3.8/site-packages/libcrypto.so
RUN pip3 install certbot certbot-dns-route53
# COPY createzip.py /tmp/
RUN mkdir -p /lambda-layers/python /lambda-layers/python/bin
RUN mv /tmp/venv/lib /lambda-layers/python/lib && \
rm -rf /lambda-layers/python/lib/python3.8/site-packages/boto3-* \
/lambda-layers/python/lib/python3.8/site-packages/boto3/* \
/lambda-layers/python/lib/python3.8/site-packages/botocore-* \
/lambda-layers/python/lib/python3.8/site-packages/botocore/* \
/lambda-layers/python/lib/python3.8/site-packages/easy_install.py \
/lambda-layers/python/lib/python3.8/site-packages/pip/* \
/lambda-layers/python/lib/python3.8/site-packages/pip-* \
/lambda-layers/python/lib/python3.8/site-packages/s3transfer/* \
/lambda-layers/python/lib/python3.8/site-packages/s3transfer-* \
/lambda-layers/python/lib/python3.8/site-packages/setuptools/* \
/lambda-layers/python/lib/python3.8/site-packages/setuptools-* \
/lambda-layers/python/lib/python3.8/site-packages/wheel/* \
/lambda-layers/python/lib/python3.8/site-packages/wheel-* \
/lambda-layers/python/lib/python3.8/site-packages/zope/component/testfiles/* \
/lambda-layers/python/lib/python3.8/site-packages/zope/component/testing.py \
/lambda-layers/python/lib/python3.8/site-packages/zope/component/tests/* \
/lambda-layers/python/lib/python3.8/site-packages/zope/deferredimport/samples/* \
/lambda-layers/python/lib/python3.8/site-packages/zope/event/tests.py \
/lambda-layers/python/lib/python3.8/site-packages/zope/hookable/tests/* \
/lambda-layers/python/lib/python3.8/site-packages/zope/interface/_zope_interface_coptimizations.c \
/lambda-layers/python/lib/python3.8/site-packages/zope/interface/common/tests/* \
/lambda-layers/python/lib/python3.8/site-packages/zope/interface/tests/* \
/lambda-layers/python/lib/python3.8/site-packages/zope/proxy/tests/*
RUN mv /tmp/venv/bin/certbot /tmp/venv/bin/distro /tmp/venv/bin/jws /lambda-layers/python/bin

WORKDIR /lambda-layers
RUN zip -y certbot-layer-py3.8.zip -9 -r .
VOLUME /export
