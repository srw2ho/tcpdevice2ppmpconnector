import logging
from logging.handlers import RotatingFileHandler
import sys
import os
import json
import msgpack
import io

import asyncio
from mqttconnector.client import MQTTClient
from ppmpmessage.v3.device_state import DeviceState
from ppmpmessage.v3.device import Device
from ppmpmessage.v3.util import machine_message_generator
from ppmpmessage.v3.util import local_now
from ppmpmessage.convertor.simple_variables import SimpleVariables
from ppmpmessage.v3.device import Device
from ppmpmessage.v3.device import iotHubDevice

from tcpconnector.tcpclient import TCPClient
from tcpconnector.tcptarget import TCPTarget
from tcpconnector.tcpclient import msgPayload
from tcpconnector.tcpclient import msgPayloadType
from tcpconnector.tcpclient import msgConnectionInfo
from tcpconnector.tcpclient import connectionInfoType

from pathlib import Path
from threading import Thread
from tomlconfig.tomlutils import TomlParser

from statistics import mean,median

import statistics 

PROJECT_NAME = 'tcpdevice2ppmpconnector'

# load configuration from config file
toml = TomlParser(f'{PROJECT_NAME}.toml')

MQTT_ENABLED = toml.get('mqtt.enabled', True)
MQTT_NETWORK_NAME = toml.get('mqtt.network_name', 'mh')
MQTT_HOST = toml.get('mqtt.host', 'localhost')
MQTT_PORT = toml.get('mqtt.port', 1883)
MQTT_USERNAME = toml.get('mqtt.username', '')
MQTT_PASSWORD = toml.get('mqtt.password', '')
MQTT_TLS_CERT = toml.get('mqtt.tls_cert', '')

CYSTERNE_SENSOR_DISTANCE_MIN = toml.get('Cysterne.sensordistance_min', 28)
CYSTERNE_SENSOR_DISTANCE_MAX = toml.get('Cysterne.sensordistance_max', 174)


LOGFOLDER = "./logs/"

DEVICE_GATEWAY = Device(
    additionalData={
        'type': 'OPC_UA_GATEWAY',
    },
)
DEVICE_PLC = Device(
    additionalData={
        'type': 'PLC',
    },
)


# configure logging
logger = logging.getLogger('root')
logger.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

try:  
    os.mkdir(LOGFOLDER)
    logger.info(f'create logfolder: {LOGFOLDER}')
except OSError as error:  
    logger.info(f'create logfolder: {LOGFOLDER}:{error}')
# fl = logging.FileHandler('OPC-UA.log')
# Rotation file handler miit 200 000 bytes pro file und 10 files in rotation
fl = RotatingFileHandler(f'{LOGFOLDER}{PROJECT_NAME}.log',mode='a', maxBytes=2*(10**5), backupCount=10)
fl.setLevel(logging.ERROR)
fl.setFormatter(formatter)
logger.addHandler(fl)


# list of all OPC-UA client processes
asynctaskhandls = []
processes = []


globMQTTClient = MQTTClient(host=MQTT_HOST, port=MQTT_PORT, user=MQTT_USERNAME, password=MQTT_PASSWORD, tls_cert=MQTT_TLS_CERT)
    
iothubdevices = dict()

jsonPayloadArray = list()
Temp_Mean = 0
   
def createASCIIpayload(payload):
    
    # a = c_wchar_p(payload)
    
    buf = io.BytesIO()
    cmdlen =  len (payload) 
    cmdlenheader = cmdlen.to_bytes(4, byteorder="little")
    buf.write(cmdlenheader)
    header = bytes([0x55,0x55])    
    buf.write(header)
    convertedpayload = bytes(payload, 'utf-8')
    # convertedpayload = bytes(a.value, 'utf-8')
    buf.write(convertedpayload)
    return buf.getvalue()


def msgpackdeserialize(payload):
    try:
        
        # return umsgpack.Unpacker(payload._payload)
        return msgpack.unpackb(payload._payload,encoding="utf-8", raw=False)
        # return msgpack.unpackb(payload._payload)
    
    except Exception as exception:
        logger.error(f'msgpackdeserialize Error: {exception}')
        logger.info(f'msgpackdeserialize Error: {exception}')

        return {}

def parseCommand(commands,JsonDict):
    splittedcommands = commands.split(",")
    for command in splittedcommands:
        values = command.split("=")
        if len(values) > 1:
            param = values[0]
            value = values[1]
            JsonDict[param] = value
            

def splitintoCommands(payload,JsonDict):
    strippedpayload = payload.replace(" ", "")
    commands = strippedpayload.split(";")
    for command in commands:
        parseCommand(command,JsonDict )

def calculateMedianValue(JsonDict, Key):   
    if Key in JsonDict:
        KeyValue =JsonDict[Key]
       
        val =[ item[Key] for item in jsonPayloadArray if Key in item]
        val.append(KeyValue)
        startRange = 0
        rangelen = len(val)
        if rangelen > 5:  startRange = rangelen-5     
        val_ =[val[x] for x in range(startRange, rangelen) ]
        if len(val_) > 2:
            medianvalue = statistics.median(val_)
            JsonDict[f'{Key}_Mean'] = medianvalue
            return True
        else: JsonDict[f'{Key}_Mean'] = KeyValue
    return False

def getlastMedianValue(Key):   
    val =[ item[Key] for item in jsonPayloadArray if Key in item]
    rangelen = len(val)
    if rangelen > 0:  
        medianvalue = val[rangelen-1]
        return True, medianvalue
    return False , 0
    
def calculateCysternData(JsonDict):    


    HC_SR04_12_Mean = -1
    if calculateMedianValue(JsonDict, "HC_SR04.12"):
        HC_SR04_12_Mean = JsonDict["HC_SR04.12_Mean"]
        valueOk, Temp_Mean =getlastMedianValue("Temp_Mean")
        if valueOk:
            VinMeterProSec = 331.5 + (0.6 * Temp_Mean);
            MeasureDistance = (VinMeterProSec * HC_SR04_12_Mean) / (10000 * 2);
            SensorDistance = CYSTERNE_SENSOR_DISTANCE_MAX-MeasureDistance
            JsonDict["MeasureDistance"] = SensorDistance
            JsonDict["SensorDistance"] = SensorDistance
            if CYSTERNE_SENSOR_DISTANCE_MAX > CYSTERNE_SENSOR_DISTANCE_MIN :
                fillingLevel = (SensorDistance*100) / (CYSTERNE_SENSOR_DISTANCE_MAX - CYSTERNE_SENSOR_DISTANCE_MIN)
                JsonDict["fillingLevel"] = fillingLevel

    if calculateMedianValue(JsonDict, "Temp"):
        Temp_Mean = JsonDict["Temp_Mean"]

     
        # jsonPayloadArray["Distance"] = Distance
    if calculateMedianValue(JsonDict, "Humid"):
             Humid_Mean = JsonDict["Humid_Mean"]
    if calculateMedianValue(JsonDict, "Press"):
        Press_Mean = JsonDict["Press_Mean"]




    
def doBinaryCommands(data):
    JsonDict = dict()
    decodeddata = data._payload.decode("utf-8") 
    splitintoCommands(decodeddata,JsonDict)
    
    JsonfloatDict = {key: float (value) for key, value in JsonDict.items() }
    
    if data._TCPClient.target.get_host()== "Zysterne":
        calculateCysternData(JsonfloatDict)
    
    return JsonfloatDict 
        
def doSolar(payload):
    return 

def domsgPackSolar(data):
    # return msgpack.unpackb(data._payload)
    return msgpackdeserialize(data)

def doJsonPackSolar(data):
    # decodeddata = data._payload.decode("utf-8") 
    return json.loads(data._payload)
 
def createASCIIpayload(payload):
        
    
    buf = io.BytesIO()
    cmdlen =  len (payload) 
    cmdlenheader = cmdlen.to_bytes(4, byteorder="big")
    buf.write(cmdlenheader)
    header = bytes([0x55,0x55])    
    buf.write(header)
    convertedpayload = bytes(payload, 'utf-8')
    buf.write(convertedpayload)
    return buf.getvalue()

    
def sendMQTTPayload(data,jsonpayload):
    
    jsonPayloadArray.append(jsonpayload)
    if len (jsonPayloadArray) > 50:
        del jsonPayloadArray[0]
                    
    global iothubdevices
    global globMQTTClient
    deviceId = data._TCPClient.target.host 
    # decodeddata = data._payload.decode("utf-8") 
    # jsonpayload = json.loads(data._payload)

    acttime = local_now()
     
    if globMQTTClient!=None:  
        iotDevice = iothubdevices.get(deviceId)
    
        if iotDevice==None: 
            iotDevice =iotHubDevice(net_name='mh', devideid= deviceId, additionalData={'type': 'iotHub', },)
            iothubdevices[deviceId] = iotDevice
            globMQTTClient.publish(iotDevice.info_topic(), machine_message_generator(iotDevice),retain=True)

        simplevars = SimpleVariables(iotDevice, jsonpayload, acttime)
        ppmppayload = simplevars.to_ppmp()
                
        if globMQTTClient.isConnected():
            globMQTTClient.publish(iotDevice.ppmp_topic(), ppmppayload, retain=True)
            
        logger.info (f'MQTT-PPMP-Payload device:{iotDevice.getHostname()}:{ppmppayload}')



async def connected(connectioninfo): 
    try:
        if (connectioninfo._connectionInfoType == connectionInfoType.CONNECTED) or (connectioninfo._connectionInfoType == connectionInfoType.CHECKCONNECTION):
            # if (connectioninfo._TCPClient._target.host !="Zysterne"): return
            
            test_string='GPIOServiceClient.Start' 
            xmd = createASCIIpayload(test_string)
            await connectioninfo._TCPClient.writesenddata(xmd)
  
        
    except Exception as ex:
        logger.error(f'connected:{ex}')
        logger.info(f'connected:{ex}') 


   
            
async def readinqueue(in_queue): 
    
    while True:
        try:
            data = await in_queue.get()
            if data._msgPayloadType == msgPayloadType.ASCIISOLAR:
                doSolar(data)
            if data._msgPayloadType == msgPayloadType.BINARY:
                jsonPayload = doBinaryCommands(data)
                sendMQTTPayload(data,jsonPayload)
                
            if data._msgPayloadType == msgPayloadType.MSGPACKSOLAR:
                package = domsgPackSolar(data)
                print (package)
            if data._msgPayloadType == msgPayloadType.JSONSOLAR:
                jsonPayload = doJsonPackSolar(data)
                sendMQTTPayload(data,jsonPayload)

            await asyncio.sleep(0.1)
        except Exception as ex:
            logger.error(f'readinqueue error:{ex}')
            logger.info(f'readinqueue error:{ex}')


async def run_tcpconnector(host, port, _timeout):
    
    target = TCPTarget (host,port,timeout=_timeout)
    globtcpclient = TCPClient(target)
    await globtcpclient.connect(on_reciveEvent_batch=readinqueue, on_connect_event= connected)
    
    logger.error(f'test_TCPConnectin:close by user')   
    return



async def run_alltcpconnectors(hosts, ports, timeoutsinsec):
    try:
        loop = asyncio.get_event_loop()
        for host, port, tmoutinsec in zip(hosts, ports, timeoutsinsec):
            tskhandle = asyncio.create_task(run_tcpconnector(host, port, tmoutinsec) ) 
            # tskhandle = loop.create_task(run_tcpconnector(host, port, timeoutsinsec) )
            asynctaskhandls.append(tskhandle)
                # loop.run_until_complete(run_tcpconnector(host, port, timeoutsinsec))
        while True:
            
            await asyncio.sleep(1)
    except KeyboardInterrupt as ex:
        logger.info(f'Receiving has stopped by user:{ex}') 
         
    except Exception as ex:
        logger.error(f'run_alltcpconnectors error:{ex}')  
        logger.info(f'run_alltcpconnectors error:{ex}')    
    finally:
        return 
        # loop.run_until_complete(client.close())


def start_tcpconnections():
    global globMQTTClient
    hosts = toml.get('tcpdevices.hosts', ['localhost'])
    ports = toml.get('tcpdevices.ports', [4840])
    timeoutsinsec = toml.get('tcpdevices.timeoutsinsecs', [10])

    # send complete config list for all devices (as gateway, not only single PLC device)
    globMQTTClient = MQTTClient(host=MQTT_HOST, port=MQTT_PORT, user=MQTT_USERNAME, password=MQTT_PASSWORD, tls_cert=MQTT_TLS_CERT)
    # create machine message with state ERROR (LWT) (do this before(!) connect)


    # connect to MQTT
    globMQTTClient.connect()

    loop = asyncio.get_event_loop()


    try:
        # loop.create_task(run_alltcpconnectors(hosts, ports, timeoutsinsec))
        # loop.run_forever()
        loop.run_until_complete(run_alltcpconnectors(hosts, ports, timeoutsinsec))
   
    except KeyboardInterrupt:
        print("Receiving has stopped.")
    finally:
        # loop.run_until_complete(client.close())
        loop.stop()
    

def main():


    # start OPC-UA client(s)
    start_tcpconnections()

if __name__ == '__main__':
    main()
