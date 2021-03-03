"""Platform for sensor integration."""
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
#from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telnetlib import Telnet

class TouchtronicParams:
    def __init__(self, msg):
        self.params = {
            "state": msg[0],    # 1=Off | 5=Ignition | 6=Transition to full firing | 7=Full firing
            "o2" : msg[1],
            "o2_target" : msg[2],
            "boilerTemp" : msg[3],
            "boilerTemp_target" : msg[4],
            "smokeGasTemp" : msg[5],
            "draft" : msg[6],
            "draft_target" : msg[7],
            "power" : msg[8],
            "deliveryRate" : msg[9],
            "currentDrawer" : msg[10],
            "currentGrate" : msg[13],
            "currentCleaning" : msg[14],
            "outsideTemp" : msg[15],
            "outsideTemp_mean" : msg[16],
            "bufferTemp_top" : msg[17],
            "bufferTemp_ctr" : msg[19],
            "bufferTemp_btm" : msg[21],
            "returnTemp" : msg[23],
            "returnTemp_target" : msg[24],
            "control_k" : msg[27],
            "control_f" : msg[28],
            "runtimeSinceRefill" : msg[32],
            "runtimeSinceAshRemoval" : msg[33],
            "ashRemovals" : msg[34],
            "grateMovements" : msg[35],
            "bufferFillRate" : msg[42],
            "pelletStock" : msg[46],
            "pelletConsumption" : msg[47],
            "errorCode" : msg[49],
            "flowTemp" : msg[56],
            "flowTemp_target" : msg[57],
            "hotWaterTemp" : msg[95],
            "hotWaterTemp_target" : msg[96],
            "hotWaterPump": msg[97],
            "error" : (int(msg[141],16) & 0x2000) > 0
        }
            
    def get(self, p):
        return self.params[p]


class TouchtronicBridge:
    
    def __init__(self, hostIP):
        self.hostIP = hostIP
        self.tnc = Telnet(hostIP)
        self.connectionOK = False
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(lambda:self.__update(),'interval',seconds=5)
        self.scheduler.start()
        self.latestParams = TouchtronicParams(["0"]*150)
        
    def shutdown(self):
        self.scheduler.shutdown()
        print("Closing connection...")
        self.tnc.close()
        
    def __update(self):
        if self.connectionOK:
            try:
                data = self.tnc.read_very_eager()
            except EOFError as error:
                print(error)
                self.connectionOK = False
                return    
            msg = data.decode("ascii")
            lastMsgStart = msg.rfind("pm ")
            if lastMsgStart<0: 
                return
            lastMsg = msg[lastMsgStart+3:].split(' ')
            if len(lastMsg) != 150: 
                return
            self.latestParams = TouchtronicParams(lastMsg)
        else:
            print("Opening connection...")
            self.tnc.open(self.hostIP)
            self.connectionOK = True

    def getParams(self):
        return self.latestParams


SCAN_INTERVAL = timedelta(seconds=5)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    bridge = TouchtronicBridge("192.168.0.161")
    add_entities([NanoPKSensor(bridge, "boiler temperature", "boilerTemp", TEMP_CELSIUS)])


class NanoPKSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, bridge, description, paramName, measurementUnit):
        """Initialize the sensor."""
        self._state = None
        self._bridge = bridge
        self._description = description
        self._paramName = paramName
        self._unit = measurementUnit

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Nano-PK " + self._description

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = self._bridge.getParams().get(self._paramName)

