"""Platform for sensor integration."""
import logging
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from .const import DOMAIN, CONF_HOST, CONF_FORMAT, CONF_NAME, CONF_PARAMS, CONF_PARAMS_STANDARD, CONF_PARAMS_FULL, CONF_LANG, CONF_LANG_EN, CONF_LANG_DE, BRIDGE_STATE_OK
from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from telnetlib import Telnet
import xml.etree.ElementTree as xml
from .hargassner import HargassnerBridge
from .error import HargassnerErrors


_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None) -> None:
    """Set up the sensor platform."""
    host = hass.data[DOMAIN][CONF_HOST]
    format = hass.data[DOMAIN][CONF_FORMAT]
    name = hass.data[DOMAIN][CONF_NAME]
    paramSet = hass.data[DOMAIN][CONF_PARAMS]
    lang = hass.data[DOMAIN][CONF_LANG]
    uniqueId = hass.data[DOMAIN][CONF_LANG]
    bridge = HargassnerBridge(host, name, uniqueId, msgFormat=format)
    errorLog = bridge.getErrorLog()
    if errorLog != "": _LOGGER.error(errorLog)
    if paramSet == CONF_PARAMS_FULL:
        entities = [bridge]
        for p in bridge.data().values(): 
            if p.key()=="Störung": 
                entities.append(HargassnerErrorSensor(bridge, name))
                entities.append(HargassnerProblemSensor(bridge, name))
                entities.append(HargassnerSolutionSensor(bridge, name))
            elif p.key()=="ZK": 
                entities.append(HargassnerStateSensor(bridge, name, lang))
            else:
                entities.append(HargassnerSensor(bridge, name+" "+p.description(), p.key()))
        entities.append(HargassnerEnergySensor(bridge, name))
        async_add_entities(entities)
    else:
        async_add_entities([
            bridge,
            HargassnerErrorSensor(bridge, name),
            HargassnerStateSensor(bridge, name, lang),
            HargassnerSensor(bridge, name+" boiler temperature", "TK"),
            HargassnerSensor(bridge, name+" smoke gas temperature", "TRG"),
            HargassnerSensor(bridge, name+" output", "Leistung", "mdi:fire"),
            HargassnerSensor(bridge, name+" outside temperature", "Taus"),
            HargassnerSensor(bridge, name+" buffer temperature 0", "TB1", "mdi:thermometer-lines"),
            HargassnerSensor(bridge, name+" buffer temperature 1", "TPo", "mdi:thermometer-lines"),
            HargassnerSensor(bridge, name+" buffer temperature 2", "TPm", "mdi:thermometer-lines"),
            HargassnerSensor(bridge, name+" buffer temperature 3", "TPu", "mdi:thermometer-lines"),
            HargassnerSensor(bridge, name+" return temperature", "TRL", "mdi:coolant-temperature"),
            HargassnerSensor(bridge, name+" buffer level", "Puff Füllgrad", "mdi:gauge"),
            HargassnerSensor(bridge, name+" pellet stock", "Lagerstand", "mdi:silo"),
            HargassnerSensor(bridge, name+" pellet consumption", "Verbrauchszähler", "mdi:basket-unfill"),
            HargassnerSensor(bridge, name+" flow temperature", "TVL_1", "mdi:coolant-temperature"),
            HargassnerEnergySensor(bridge, name)
    ])


class HargassnerSensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, bridge, description, paramName, icon=None):
        """Initialize the sensor."""
        self._value = None
        self._bridge = bridge
        self._description = description
        self._paramName = paramName
        self._icon = icon
        self._unique_id = bridge.getUniqueIdBase()
        self._unit = bridge.getUnit(paramName)
        sc = bridge.getStateClass(paramName)
        if (self._unit==None):
            self._stateClass = None
            self._deviceClass = SensorDeviceClass.ENUM
            self._options = ["True", "False"]
        else:
            if sc=="measurement": self._stateClass = SensorStateClass.MEASUREMENT
            elif sc=="total": self._stateClass = SensorStateClass.TOTAL
            elif sc=="total_increasing": self._stateClass = SensorStateClass.TOTAL_INCREASING
            if self._unit=="°C": self._deviceClass = SensorDeviceClass.TEMPERATURE
            else: self._deviceClass = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._description

    @property
    def device_class(self):
        """Return the state of the sensor."""
        return self._deviceClass

    @property
    def state_class(self):
        """Return the state of the sensor."""
        return self._stateClass

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._value

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def icon(self):
        """Return an icon for the sensor in the GUI."""
        return self._icon
        
    @property
    def available(self):
        if self._bridge.state == BRIDGE_STATE_OK: return True
        else: return False

    async def async_update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._value = self._bridge.getValue(self._paramName)

    @property
    def unique_id(self):
        """Return the unique id of the sensor."""
        return self._unique_id + self._paramName


class HargassnerEnergySensor(HargassnerSensor):

    def __init__(self, bridge, deviceName):
        super().__init__(bridge, deviceName+" energy consumption", "Verbrauchszähler", "mdi:radiator")
        self._deviceClass = SensorDeviceClass.ENERGY
        self._unit = "kWh"

    async def async_update(self):
        try:
            self._value = 4.8 * float(self._bridge.getValue(self._paramName))
        except Exception:
            _LOGGER.warning("HargassnerEnergySensor.update(): Invalid value.\n")
            self._value = None

    @property
    def unique_id(self):
        """Return the unique id of the sensor."""
        return self._unique_id + self._paramName + "-E"


class HargassnerErrorSensor(HargassnerSensor):

    ERRORS = HargassnerErrors.ERRORS

    def __init__(self, bridge, deviceName):
        super().__init__(bridge, deviceName+" operation", "Störung", "mdi:alert")
        self._stateClass = None
        self._deviceClass = SensorDeviceClass.ENUM
        self._options = list(self.ERRORS.values())

    async def async_update(self):
        rawState = self._bridge.getValue(self._paramName)
        if rawState==None: self._value = "Unknown"
        elif rawState=="False":
            self._value = "OK"
            self._icon = "mdi:check"
        else:
            try:
                errorID = self._bridge.getValue("Störungs Nr")
                errorDescr = self.ERRORS.get(errorID)
                if errorDescr==None:
                    self._value = "Error " + errorID
                else:
                    self._value = errorDescr
            except Exception:
                _LOGGER.warning("HargassnerErrorSensor.update(): Invalid error ID.\n")
                self._value = "Unknown Error"
            self._icon = "mdi:alert"
        errorLog = self._bridge.getErrorLog()
        if errorLog != "": _LOGGER.error(errorLog)
        infoLog = self._bridge.getInfoLog()
        if infoLog != "": _LOGGER.info(infoLog)


class HargassnerProblemSensor(HargassnerSensor):

    PROBLEMS = HargassnerErrors.PROBLEMS

    def __init__(self, bridge, deviceName):
        super().__init__(bridge, deviceName+" problem", "Störung", "mdi:alert")
        self._stateClass = None
        self._deviceClass = SensorDeviceClass.ENUM
        self._options = list(self.PROBLEMS.values())

    async def async_update(self):
        rawState = self._bridge.getValue(self._paramName)
        if rawState==None: self._value = "Unknown"
        elif rawState=="False":
            self._value = "---"
            self._icon = "mdi:check"
        else:
            try:
                errorID = self._bridge.getValue("Störungs Nr")
                errorDescr = self.PROBLEMS.get(errorID)
                if errorDescr==None:
                    self._value = "Error " + errorID
                else:
                    self._value = errorDescr
            except Exception:
                _LOGGER.warning("HargassnerProblemSensor.update(): Invalid error ID.\n")
                self._value = "Unknown Error"
            self._icon = "mdi:alert"
        errorLog = self._bridge.getErrorLog()
        if errorLog != "": _LOGGER.error(errorLog)
        infoLog = self._bridge.getInfoLog()
        if infoLog != "": _LOGGER.info(infoLog)

    @property
    def unique_id(self):
        """Return the unique id of the sensor."""
        return self._unique_id + self._paramName + "_problem"


class HargassnerSolutionSensor(HargassnerSensor):

    SOLUTIONS = HargassnerErrors.SOLUTIONS

    def __init__(self, bridge, deviceName):
        super().__init__(bridge, deviceName+" solution", "Störung", "mdi:alert")
        self._stateClass = None
        self._deviceClass = SensorDeviceClass.ENUM
        self._options = list(self.SOLUTIONS.values())

    async def async_update(self):
        rawState = self._bridge.getValue(self._paramName)
        if rawState==None: self._value = "Unknown"
        elif rawState=="False":
            self._value = "---"
            self._icon = "mdi:check"
        else:
            try:
                errorID = self._bridge.getValue("Störungs Nr")
                errorDescr = self.SOLUTIONS.get(errorID)
                if errorDescr==None:
                    self._value = "Error " + errorID
                else:
                    self._value = errorDescr
            except Exception:
                _LOGGER.warning("HargassnerSolutionSensor.update(): Invalid error ID.\n")
                self._value = "Unknown Error"
            self._icon = "mdi:help-circle"
        errorLog = self._bridge.getErrorLog()
        if errorLog != "": _LOGGER.error(errorLog)
        infoLog = self._bridge.getInfoLog()
        if infoLog != "": _LOGGER.info(infoLog)

    @property
    def unique_id(self):
        """Return the unique id of the sensor."""
        return self._unique_id + self._paramName + "_solution"


class HargassnerStateSensor(HargassnerSensor):

    def __init__(self, bridge, deviceName, lang):
        super().__init__(bridge, deviceName+" boiler state", "ZK")
        self._stateClass = None
        self._deviceClass = SensorDeviceClass.ENUM
        if lang==CONF_LANG_DE:
            self._options = ["Unbekannt", "Aus", "Startvorbereitung", "Kessel Start", "Zündüberwachung", "Zündung", "Übergang LB", "Leistungsbrand", "Gluterhaltung", "Warten auf EA", "Entaschung", "-", "Putzen"]
        else:
            self._options = ["Unknown", "Off", "Preparing start", "Boiler start", "Monitoring ignition", "Ignition", "Transition to FF", "Full firing", "Ember preservation", "Waiting for AR", "Ash removal", "-", "Cleaning"]

    async def async_update(self):
        rawState = self._bridge.getValue(self._paramName)
        try:
            idxState = int(rawState)
            if not (idxState>=0 and idxState<=12):
                _LOGGER.warning("HargassnerStateSensor.update(): State index out of bounds.\n")
                idxState=0
        except Exception:
            _LOGGER.warning("HargassnerStateSensor.update(): Invalid state.\n")
            idxState = 0
        self._value = self._options[idxState]
        if idxState==6 or idxState==7: self._icon = "mdi:fireplace"  # (transition to) full firing
        else: self._icon = "mdi:fireplace-off"