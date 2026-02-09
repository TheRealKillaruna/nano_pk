"""Platform for sensor integration."""
import logging
import asyncio
from datetime import timedelta

# Nettoyage des imports : plus de telnetlib, plus de apscheduler
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from .const import (
    DOMAIN, CONF_HOST, CONF_FORMAT, CONF_NAME, CONF_PARAMS, 
    CONF_PARAMS_STANDARD, CONF_PARAMS_FULL, CONF_LANG, 
    CONF_LANG_EN, CONF_LANG_DE, CONF_LANG_FR, BRIDGE_STATE_OK, CONF_UNIQUE_ID
)
from .hargassner import HargassnerBridge

_LOGGER = logging.getLogger(__name__)

# Très important : Définit la fréquence de lecture à 5 secondes
SCAN_INTERVAL = timedelta(seconds=5)

# --- DÉFINITION DES CLASSES D'ABORD (Pour éviter l'erreur "not defined") ---

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
        if (self._unit is None):
            self._stateClass = None
            self._deviceClass = SensorDeviceClass.ENUM
            self._options = ["True", "False"]
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
    def native_value(self):
        return self._value

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def icon(self):
        return self._icon
        
    @property
    def available(self):
        # Le capteur est disponible si le pont est connecté
        return self._bridge.state == BRIDGE_STATE_OK

    async def async_update(self):
        """Fetch new state data for the sensor."""
        # On lit la valeur depuis le cache du pont
        self._value = self._bridge.getValue(self._paramName)

    @property
    def unique_id(self):
        return self._unique_id + self._paramName


class HargassnerEnergySensor(HargassnerSensor):

    def __init__(self, bridge, deviceName):
        super().__init__(bridge, deviceName+" energy consumption", "Verbrauchszähler", "mdi:radiator")
        self._deviceClass = SensorDeviceClass.ENERGY
        self._unit = "kWh"

    async def async_update(self):
        try:
            val = self._bridge.getValue(self._paramName)
            if val is not None:
                self._value = 4.8 * float(val)
        except Exception:
            self._value = None

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

    def __init__(self, bridge, deviceName):
        super().__init__(bridge, deviceName+" operation", "Störung", "mdi:alert")
        self._stateClass = None
        self._deviceClass = SensorDeviceClass.ENUM
        self._options = list(self.ERRORS.values())

    async def async_update(self):
        # LOGS DE DEBUG : Pour voir si le pont remonte des erreurs
        err = self._bridge.getErrorLog()
        if err: _LOGGER.warning(f"Bridge Log: {err}")
        
        rawState = self._bridge.getValue(self._paramName)
        if rawState is None: 
            self._value = "Unknown"
        elif rawState == "False":
            self._value = "OK"
            self._icon = "mdi:check"
        else:
            try:
                errorID = self._bridge.getValue("Störungs Nr")
                errorDescr = self.ERRORS.get(errorID)
                if errorDescr is None:
                    self._value = "Error " + str(errorID)
                else:
                    self._value = errorDescr
            except Exception:
                self._value = "Unknown Error"
            self._icon = "mdi:alert"


class HargassnerStateSensor(HargassnerSensor):

    def __init__(self, bridge, deviceName, lang):
        super().__init__(bridge, deviceName+" boiler state", "ZK")
        self._stateClass = None
        self._deviceClass = SensorDeviceClass.ENUM
        if lang==CONF_LANG_DE:
            self._options = ["Unbekannt", "Aus", "Startvorbereitung", "Kessel Start", "Zündüberwachung", "Zündung", "Übergang LB", "Leistungsbrand", "Gluterhaltung", "Warten auf EA", "Entaschung", "-", "Putzen"]
        elif lang==CONF_LANG_FR:
            self._options = ["Inconnu", "Arrêt", "Préparation démarrage", "Démarrage chaudière", "Contrôle allumage", "Allumage", "Transition combustion", "Combustion", "Veille", "Décendrage dans 7mn", "Décendrage", "-", "Nettoyage"]
        else:
            self._options = ["Unknown", "Off", "Preparing start", "Boiler start", "Monitoring ignition", "Ignition", "Transition to FF", "Full firing", "Ember preservation", "Waiting for AR", "Ash removal", "-", "Cleaning"]

    async def async_update(self):
        rawState = self._bridge.getValue(self._paramName)
        try:
            if rawState is None:
                idxState = 0
            else:
                idxState = int(rawState)
                if not (idxState >= 0 and idxState < len(self._options)):
                    idxState = 0
        except Exception:
            idxState = 0
        self._value = self._options[idxState]
        if idxState == 6 or idxState == 7: self._icon = "mdi:fireplace" 
        else: self._icon = "mdi:fireplace-off"


# --- CONFIGURATION ET SETUP ---

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None) -> None:
    """Set up the sensor platform."""
    host = hass.data[DOMAIN][CONF_HOST]
    format = hass.data[DOMAIN][CONF_FORMAT]
    name = hass.data[DOMAIN][CONF_NAME]
    paramSet = hass.data[DOMAIN][CONF_PARAMS]
    lang = hass.data[DOMAIN][CONF_LANG]
    uniqueId = hass.data[DOMAIN][CONF_UNIQUE_ID]
    
    _LOGGER.info(f"Hargassner Nano-PK: Initialisation pour {host}...")
    
    # Création du pont
    bridge = HargassnerBridge(host, name, uniqueId, msgFormat=format)
    
    # Tentative de première connexion immédiate (pour éviter le 'Unavailable' au démarrage)
    try:
        await bridge.async_update()
        _LOGGER.info("Hargassner Nano-PK: Première connexion tentée.")
    except Exception as e:
        _LOGGER.warning(f"Hargassner Nano-PK: Erreur lors de la première connexion: {e}")

    entities = []
    # IMPORTANT : On ajoute le bridge à la liste des entités.
    # C'est grâce à ça que SCAN_INTERVAL (5s) va déclencher bridge.async_update()
    entities.append(bridge)

    if paramSet == CONF_PARAMS_FULL:
        for p in bridge.data().values(): 
            if p.key()=="Störung": 
                entities.append(HargassnerErrorSensor(bridge, name))
            elif p.key()=="ZK": 
                entities.append(HargassnerStateSensor(bridge, name, lang))
            else:
                entities.append(HargassnerSensor(bridge, name+" "+p.description(), p.key()))
        entities.append(HargassnerEnergySensor(bridge, name))
    else:
        entities.extend([
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
        
    async_add_entities(entities)
    _LOGGER.info(f"Hargassner Nano-PK: {len(entities)} entités ajoutées.")