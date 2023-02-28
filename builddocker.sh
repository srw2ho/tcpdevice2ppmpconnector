#!/bin/bash

git describe --tags --abbrev=0  > dockerversion.txt
echo -e "lese aus Datei dockerversion.txt die Version und schreibe diese into Build"


# Build=<dockerversion.txt

Build=$(<dockerversion.txt)



dockerimage="tcpdevice2ppmpconnector"

if [ "${Build}" == "" ]; then
    Build="latest"
fi


# echo -e "$Build"


echo -e " build dockerimage: $dockerimage  Build Version:" $Build






# sudo docker build --build-arg NODE_ENV=development --build-arg BUILDCMD=dev -f Dockerfile.MH -t grafana/grafana-mhdev:v7.6.5 .
sudo docker build -t ${dockerimage}:${Build}  -f Dockerfile .

# @docker build . -t %dockerimage%:%Build%

# save images in ../docker_images
mkdir ../docker_images
docker save -o ../docker_images/${dockerimage}_${Build}.zip ${dockerimage}:${Build}