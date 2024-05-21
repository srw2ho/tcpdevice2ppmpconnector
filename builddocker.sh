#!/bin/bash

git describe --tags --abbrev=0  > dockerversion.txt
echo -e "lese aus Datei dockerversion.txt die Version und schreibe diese into Build"


# Build=<dockerversion.txt

Build=$(<dockerversion.txt)

# PYTHON_INSTALLVERSION=3.11-bookworm # for RASPI 5
PYTHON_INSTALLVERSION=3.11-slim-buster # for RASPI 5
# PYTHON_INSTALLVERSION=3.9-slim-bookworm # for RASPI 4
# PYTHON_INSTALLVERSION=3.9-bookworm # for RASPI 4
# PYTHON_INSTALLVERSION=3.9-slim-buster # for RASPI 4 funktioniert nicht mit lgpio

dockerimage="tcpdevice2ppmpconnector"

if [ "${Build}" == "" ]; then
    Build="latest"
fi


# echo -e "$Build"


echo -e " build dockerimage: $dockerimage  Build Version:" $Build



# sudo docker build --build-arg NODE_ENV=development --build-arg BUILDCMD=dev -f Dockerfile.MH -t grafana/grafana-mhdev:v7.6.5 .
sudo docker build -t ${dockerimage}:${Build} --build-arg PYTHON_VERSION=${PYTHON_INSTALLVERSION} -f Dockerfile .

# @docker build . -t %dockerimage%:%Build%

# save images in ../docker_images
mkdir ../docker_images
docker save -o ../docker_images/${dockerimage}_${Build}.zip ${dockerimage}:${Build}