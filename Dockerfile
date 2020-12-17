# FROM python:slim-buster
FROM python:3.8-slim-buster
# FROM python:3.8.0-slim

RUN apt update && apt install -y git gcc
RUN git config --global credential.helper cache

COPY ./ ./

RUN pip install Cython

RUN pip install git+https://github.com/srw2ho/tcpdevice2ppmpconnector.git


ENTRYPOINT tail -f /dev/null
