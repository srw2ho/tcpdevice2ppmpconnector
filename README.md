# srw2ho tcpdevice2ppmpconnector

### Installation from Repository (online)
```bash
pip install git+https://github.com/srw2ho/tcpdevice2ppmpconnector.git
```

### Bundle python and project into .exe
```bash
pyinstaller tcpdevice2ppmpconnector.spec --onefile --clean
```

### Configuration
The configuration file has to be stored as "%.../tcpdevice2ppmpconnector.toml":
```toml

### Usage
```python
python -m tcpdevice2ppmpconnector



### Usage

```

# Build Docker
    docker build  . -t tcpdevice2ppmpconnector
    
# Run Docker
        docker run --rm -i -t tcpdevice2ppmpconnector /bin/sh