# Moehwald OPC-UA to PPMP Gateway

### Installation from Repository (online)
```bash
pip install git+https://sourcecode.socialcoding.bosch.com/scm/mh_ees1/opcua2ppmp.git
```

### Bundle python and project into .exe
```bash
pyinstaller opcua2ppmp.spec --onefile --clean
```

### Configuration
The configuration file has to be stored as "%PROGRAMDATA%\Moehwald\opcua2ppmp.toml":
```toml
[grpc]
enabled = true
port = 50052

[mqtt]
enabled = true
network_name = "mh"
host = "10.33.198.103"
port = 1883
username = ""
password = ""
publish_collections = true
refresh_time = 0.1

[opcua]
hosts = ["10.33.198.216",]
ports = [4840,]
paths = [
    ["0:Objects,4:PLC1,4:GVL_RK,4:PCComm"],
]

```

### Usage
```python
python -m opcua2ppmp
```

# Build Docker
    docker build --build-arg http_proxy="http://dailybuild:moehwald007@rb-proxy-de.bosch.com:8080" --build-arg https_proxy="http://dailybuild:moehwald007@rb-proxy-de.bosch.com:8080" --build-arg no_proxy="localhost,rb-artifactory.bosch.com" . -t opcua2ppmp
    
# Run Docker
        docker run --rm -i -t opcua2ppmp /bin/sh