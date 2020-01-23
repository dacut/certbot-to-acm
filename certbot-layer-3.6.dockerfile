FROM lambci/lambda:build-python3.6
COPY getbaseline.py /tmp/
RUN /tmp/getbaseline.py
RUN pip3 install certbot

COPY zipdiffs.py /tmp/
RUN /tmp/zipdiffs.py

VOLUME /export
