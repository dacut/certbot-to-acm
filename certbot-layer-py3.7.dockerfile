FROM lambci/lambda:build-python3.7
RUN python3 -m venv /tmp/venv
ENV VIRTUAL_ENV=/tmp/venv
ENV PATH=/tmp/venv/bin:$PATH
RUN pip3 install certbot certbot-dns-route53
COPY createzip.py /tmp/
RUN /tmp/createzip.py

VOLUME /export
