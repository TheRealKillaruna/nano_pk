"""Platform for sensor integration."""
import logging

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from .const import (
    DOMAIN, CONF_PARAMS, CONF_PARAMS_STANDARD, CONF_PARAMS_FULL,
    CONF_LANG, CONF_LANG_DE, CONF_LANG_FR, CONF_LANG_EN,
    BRIDGE_STATE_OK, CONF_UNIQUE_ID
)
from .hargassner import HargassnerBridge

_LOGGER = logging.getLogger(__name__)


class HargassnerSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, bridge, description, paramName, icon=None):
        """Initialize the sensor."""
        super().__init__(bridge)
        self._description = description
        self._paramName = paramName
        self._icon = icon
        self._unique_id = bridge.getUniqueIdBase()
        self._unit = bridge.getUnit(paramName)
        self._attr_has_entity_name = True
        
        sc = bridge.getStateClass(paramName)
        if (self._unit is None):
            self._stateClass = None
            self._deviceClass = SensorDeviceClass.ENUM
            self._attr_options = ["True", "False"]
        else:
            if sc == "measurement": self._stateClass = SensorStateClass.MEASUREMENT
            elif sc == "total": self._stateClass = SensorStateClass.TOTAL
            elif sc == "total_increasing": self._stateClass = SensorStateClass.TOTAL_INCREASING
            
            if self._unit == "°C": self._deviceClass = SensorDeviceClass.TEMPERATURE
            else: self._deviceClass = None

    @property
    def name(self):
        return self._description

    @property
    def device_class(self):
        return self._deviceClass

    @property
    def state_class(self):
        return self._stateClass

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def icon(self):
        return self._icon
        
    @property
    def available(self):
        # Le capteur est disponible si le pont est connecté et que le coordinateur a des données
        return super().available and self.coordinator.is_connected

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.getValue(self._paramName)

    @property
    def unique_id(self):
        return self._unique_id + self._paramName

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.getUniqueIdBase())},
            "name": self.coordinator.name.replace(" connection", ""),
            "manufacturer": "Hargassner",
            "model": "Nano-PK",
        }


class HargassnerEnergySensor(HargassnerSensor):

    def __init__(self, bridge):
        super().__init__(bridge, "Energy consumption", "Verbrauchszähler", "mdi:radiator")
        self._deviceClass = SensorDeviceClass.ENERGY
        self._unit = "kWh"

    @property
    def native_value(self):
        try:
            val = self.coordinator.getValue(self._paramName)
            if val is not None:
                return 4.8 * float(val)
        except Exception:
            pass
        return None

    @property
    def unique_id(self):
        return self._unique_id + self._paramName + "-E"


class HargassnerErrorSensor(HargassnerSensor):

    ERRORS = {
        "5" : "Aschelade entleeren", 
        "6" : "Aschelade zu voll", 
       "29" : "Verbrennungsstörung", 
       "30" : "Batterie leer", 
       "31" : "Blockade Einschubmotor", 
       "32" : "Füllzeit überschritten", 
       "70" : "Pelletslagerstand niedrig", 
       "89" : "Schieberost schwergängig", 
       "93" : "Aschelade offen", 
      "155" : "Spülung defekt", 
      "227" : "Lagerraumschalter aus", 
      "228" : "Pelletsbehälter fast leer", 
      "229" : "Füllstandsmelder kontrollieren", 
      "371" : "Brennraum prüfen"
    }

    def __init__(self, bridge):
        super().__init__(bridge, "Operation", "Störung", "mdi:alert")
        self._stateClass = None
        self._deviceClass = SensorDeviceClass.ENUM
        self._attr_options = ["OK", "Unknown", "Unknown Error"] + list(self.ERRORS.values())

    @property
    def native_value(self):
        rawState = self.coordinator.getValue(self._paramName)
        if rawState is None: 
            return "Unknown"
        elif rawState == "False":
            return "OK"
        else:
            try:
                errorID = self.coordinator.getValue("Störungs Nr")
                errorDescr = self.ERRORS.get(errorID)
                if errorDescr is None:
                    return "Unknown Error"
                else:
                    return errorDescr
            except Exception:
                return "Unknown Error"

    @property
    def icon(self):
        if self.native_value == "OK":
            return "mdi:check"
        return "mdi:alert"


class HargassnerStateSensor(HargassnerSensor):

    def __init__(self, bridge, lang):
        super().__init__(bridge, "Boiler state", "ZK")
        self._stateClass = None
        self._deviceClass = SensorDeviceClass.ENUM
        if lang==CONF_LANG_DE:
            self._attr_options = ["Unbekannt", "Aus", "Startvorbereitung", "Kessel Start", "Zündüberwachung", "Zündung", "Übergang LB", "Leistungsbrand", "Gluterhaltung", "Warten auf EA", "Entaschung", "-", "Putzen"]
        elif lang==CONF_LANG_FR:
            self._attr_options = ["Inconnu", "Arrêt", "Préparation démarrage", "Démarrage chaudière", "Contrôle allumage", "Allumage", "Transition combustion", "Combustion", "Veille", "Décendrage dans 7mn", "Décendrage", "-", "Nettoyage"]
        else:
            self._attr_options = ["Unknown", "Off", "Preparing start", "Boiler start", "Monitoring ignition", "Ignition", "Transition to FF", "Full firing", "Ember preservation", "Waiting for AR", "Ash removal", "-", "Cleaning"]

    @property
    def native_value(self):
        rawState = self.coordinator.getValue(self._paramName)
        try:
            if rawState is None:
                idxState = 0
            else:
                idxState = int(rawState)
                if not (idxState >= 0 and idxState < len(self._attr_options)):
                    idxState = 0
        except Exception:
            idxState = 0
        return self._attr_options[idxState]

    @property
    def icon(self):
        val = self.native_value
        if val in [self._attr_options[6], self._attr_options[7]]:
            return "mdi:fireplace" 
        return "mdi:fireplace-off"


class HargassnerConnectionSensor(CoordinatorEntity, SensorEntity):
    """Representation of the Bridge Connection State."""

    def __init__(self, bridge):
        super().__init__(bridge)
        self._name = "Connection"
        self._unique_id = bridge.getUniqueIdBase() + "_Connection"
        self._attr_has_entity_name = True

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.getUniqueIdBase())},
            "name": self.coordinator.name.replace(" connection", ""),
            "manufacturer": "Hargassner",
            "model": "Nano-PK",
        }

    @property
    def native_value(self):
        return self.coordinator.state

    @property
    def icon(self):
        if self.coordinator.is_connected: return "mdi:network-outline"
        else: return "mdi:network-off-outline"


# --- CONFIGURATION ET SETUP ---


def _build_entities(bridge, lang, param_set):
    """Build the list of sensor entities for the given bridge and settings."""
    entities = [HargassnerConnectionSensor(bridge)]

    if param_set == CONF_PARAMS_FULL:
        for p in bridge.data().values():
            if p.key() == "Störung":
                entities.append(HargassnerErrorSensor(bridge))
            elif p.key() == "ZK":
                entities.append(HargassnerStateSensor(bridge, lang))
            else:
                entities.append(HargassnerSensor(bridge, p.description().capitalize(), p.key()))
        entities.append(HargassnerEnergySensor(bridge))
    else:
        entities.extend([
            HargassnerErrorSensor(bridge),
            HargassnerStateSensor(bridge, lang),
            HargassnerSensor(bridge, "Boiler temperature", "TK"),
            HargassnerSensor(bridge, "Smoke gas temperature", "TRG"),
            HargassnerSensor(bridge, "Output", "Leistung", "mdi:fire"),
            HargassnerSensor(bridge, "Outside temperature", "Taus"),
            HargassnerSensor(bridge, "Buffer temperature 0", "TB1", "mdi:thermometer-lines"),
            HargassnerSensor(bridge, "Buffer temperature 1", "TPo", "mdi:thermometer-lines"),
            HargassnerSensor(bridge, "Buffer temperature 2", "TPm", "mdi:thermometer-lines"),
            HargassnerSensor(bridge, "Buffer temperature 3", "TPu", "mdi:thermometer-lines"),
            HargassnerSensor(bridge, "Return temperature", "TRL", "mdi:coolant-temperature"),
            HargassnerSensor(bridge, "Buffer level", "Puff Füllgrad", "mdi:gauge"),
            HargassnerSensor(bridge, "Pellet stock", "Lagerstand", "mdi:silo"),
            HargassnerSensor(bridge, "Pellet consumption", "Verbrauchszähler", "mdi:basket-unfill"),
            HargassnerSensor(bridge, "Flow temperature", "TVL_1", "mdi:coolant-temperature"),
            HargassnerEnergySensor(bridge),
        ])

    return entities


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors from a config entry."""
    bridge = hass.data[DOMAIN][entry.entry_id]
    lang = entry.data[CONF_LANG]
    param_set = entry.data[CONF_PARAMS]

    entities = _build_entities(bridge, lang, param_set)
    async_add_entities(entities)
    _LOGGER.info("Hargassner Nano-PK: %d entities added via config entry.", len(entities))