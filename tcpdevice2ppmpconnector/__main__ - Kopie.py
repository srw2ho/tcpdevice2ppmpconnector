import sys
from mqttconnector.client import MQTTClient
from ppmpmessage.v3.device_state import DeviceState
from ppmpmessage.v3.device import Device
from ppmpmessage.v3.util import machine_message_generator
from ppmpmessage.v3.util import local_now
from ppmpmessage.convertor.simple_variables import SimpleVariables
from ppmpmessage.v3.device import Device
from ppmpmessage.v3.device import iotHubDevice

from pathlib import Path
from threading import Thread
from tomlconfig.tomlutils import TomlParser

PROJECT_NAME = 'tcpdevice2ppmpconnector'

# load configuration from config file
toml = TomlParser(f'{PROJECT_NAME}.toml')

GRPC_ENABLED = toml.get('grpc.enabled', True)
GRPC_PORT = toml.get('grpc.port', 50052)

MQTT_ENABLED = toml.get('mqtt.enabled', True)
MQTT_NETWORK_NAME = toml.get('mqtt.network_name', 'mh')
MQTT_HOST = toml.get('mqtt.host', 'localhost')
MQTT_PORT = toml.get('mqtt.port', 1883)
MQTT_USERNAME = toml.get('mqtt.username', '')
MQTT_PASSWORD = toml.get('mqtt.password', '')
MQTT_TLS_CERT = toml.get('mqtt.tls_cert', '')
MQTT_PUBLISH_COLLECTIONS = toml.get('mqtt.publish_collections', True)
MQTT_REFRESH_TIME = toml.get('mqtt.refresh_time', 0.1)

OPC_UA_HOSTS = toml.get('opcua.hosts', ['localhost'])
OPC_UA_PORTS = toml.get('opcua.ports', [4840])
OPC_UA_PATHS = toml.get('opcua.paths', [['0:Objects,4:PLC1,4:GVL_RK,4:PCComm']])

DEVICE_TYPE = 'PLC'
DEVICE = Device(
    additionalData={
        'type': DEVICE_TYPE
    },
)

def run_opc_ua_server(opc_ua_host, opc_ua_port, opc_ua_path):
    opc_ua_server = OPCUAServer(
        GRPC_ENABLED=GRPC_ENABLED,
        GRPC_PORT=GRPC_PORT,
        MQTT_ENABLED=MQTT_ENABLED,
        MQTT_HOST=MQTT_HOST,
        MQTT_PORT=MQTT_PORT,
        MQTT_USERNAME=MQTT_USERNAME,
        MQTT_PASSWORD=MQTT_PASSWORD,
        MQTT_TLS_CERT=MQTT_TLS_CERT,
        MQTT_PUBLISH_COLLECTIONS=MQTT_PUBLISH_COLLECTIONS,
        MQTT_REFRESH_TIME=MQTT_REFRESH_TIME,
        PAYLOAD_GENERATOR=lambda variables, timestamp: SimpleVariables(DEVICE, variables, timestamp).to_ppmp()
    )

    opc_ua_server.establish_connection(opc_ua_host, opc_ua_path, port=opc_ua_port, first_run=True)


def main():
    pv = PermitVerify()

    # pylint: disable=no-member
    if not pv.verify() or not pv.check_not_expired():
        print("no valid permit found!")
        sys.exit(1)

    for host, port, path in zip(OPC_UA_HOSTS, OPC_UA_PORTS, OPC_UA_PATHS):
        # create new thread for each OPC-UA client
        thread = Thread(target=run_opc_ua_server, args=(host, port, path))
        thread.start()

if __name__ == '__main__':
    main()
