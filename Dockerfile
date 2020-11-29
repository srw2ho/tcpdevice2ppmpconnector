# FROM python:slim-buster
FROM python:3.8-slim-buster
# FROM python:3.8.0-slim

RUN apt update && apt install -y git gcc
RUN git config --global credential.helper cache

COPY ./ ./

RUN pip install Cython

# RUN pip install git+https://dailybuild:moehwald007@sourcecode.socialcoding.bosch.com/scm/mh_ees1/tcpdevice2ppmpconnector.git
RUN pip install tcpdevice2ppmpconnector
# RUN python install ./setup.py

ENTRYPOINT tail -f /dev/null
