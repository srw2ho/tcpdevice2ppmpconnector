# FROM python:3.11-slim-buster
ARG PYTHON_VERSION="3.11-bookworm"

FROM python:$PYTHON_VERSION

# FROM python:3.9-slim-buster
# FROM python:3.8-slim-buster
# FROM python:3.8.0-slim



RUN apt update && apt install -y git gcc
RUN git config --global credential.helper cache

COPY ./ ./

# Enable Virtual Environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
RUN . $VIRTUAL_ENV/bin/activate

RUN pip install --upgrade pip

RUN pip install Cython



RUN pip install git+https://github.com/srw2ho/tcpdevice2ppmpconnector.git


RUN pip install  pip-licenses
RUN pip-licenses --with-system --with-urls --order=license > ./python_dependencies.txt

RUN pip uninstall -y Cython pip-licenses 

ENTRYPOINT tail -f /dev/null
