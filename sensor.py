"""Platform for sensor integration."""
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from telnetlib import Telnet

class TouchtronicParams:
    def __init__(self, msg):
        self.state              = msg[0]    # 1=Off | 5=Ignition | 6=Transition to full firing | 7=Full firing
        self.o2                 = msg[1]
        self.o2_target          = msg[2]
        self.boilerTemp         = msg[3]
        self.boilerTemp_target  = msg[4]
        self.smokeGasTemp       = msg[5]
        self.draft              = msg[6]
        self.draft_target       = msg[7]
        self.power              = msg[8]
        self.deliveryRate       = msg[9]
        self.currentDrawer      = msg[10]
        self.currentGrate       = msg[13]
        self.currentCleaning    = msg[14]
        self.outsideTemp        = msg[15]
        self.outsideTemp_mean   = msg[16]
        self.bufferTemp_top     = msg[17]
        self.bufferTemp_ctr     = msg[19]
        self.bufferTemp_btm     = msg[21]
        self.returnTemp         = msg[23]
        self.returnTemp_target  = msg[24]
        self.control_k          = msg[27]
        self.control_f          = msg[28]
        self.RuntimeSinceRefill = msg[32]
        self.RuntimeSinceAshRemoval = msg[33]
        self.ashRemovals        = msg[34]
        self.grateMovements     = msg[35]
        self.bufferFillRate     = msg[42]
        self.pelletStock        = msg[46]
        self.pelletConsumption  = msg[47]
        self.errorCode          = msg[49]
        self.flowTemp           = msg[56]
        self.flowTemp_target    = msg[57]
        self.hotWaterTemp       = msg[95]
        self.hotWaterTemp_target= msg[96]
        self.hotWaterPump       = msg[97]
        self.error              = (int(msg[141],16) & 0x2000) > 0


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
    add_entities([NanoPKSensor(bridge, "boiler temperature", 3)])


class NanoPKSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, bridge, description, msgIdx):
        """Initialize the sensor."""
        self._state = None
        self._bridge = bridge
        self._description = description
        self._msgIdx = msgIdx

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
        return TEMP_CELSIUS

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        p = self._bridge.getParams()
        self._state = p.boilerTemp

