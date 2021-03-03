"""Platform for sensor integration."""
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from datetime import timedelta
from telnetlib import Telnet

SCAN_INTERVAL = timedelta(seconds=5)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    add_entities([NanoPKSensor("boiler temperature",3)])


class NanoPKSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, description, msgIdx):
        """Initialize the sensor."""
        self._state = None
        self._connectionOK = False
        self._tnc = Telnet()
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
        if self._connectionOK:
            try:
                data = self._tnc.read_very_eager()
            except EOFError as error:
                self._connectionOK = False
                return
            msg = data.decode("ascii")
            lastMsgStart = msg.rfind("pm ")
            if lastMsgStart<0: 
                return
            lastMsg = msg[lastMsgStart+3:].split(' ')
            if len(lastMsg) != 150: 
                return
            self._state = float(lastMsg[3])
        else:
            self._tnc.open("192.168.0.161")
            self._connectionOK = True
