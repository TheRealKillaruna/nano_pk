# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 22:22:58 2021

@author: Tobias
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
import xml.etree.ElementTree as xml
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import BRIDGE_STATE_OK, BRIDGE_STATE_DISCONNECTED, BRIDGE_TIMEOUT, TELNET_PORT

_LOGGER = logging.getLogger(__name__)



class HargassnerMessageTemplates:

    _TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

    @staticmethod
    def _load_templates(template_dir) -> dict:
        """Load all XML template files at module import time (outside the event loop)."""
        templates = {}
        for fname in sorted(os.listdir(template_dir)):
            if fname.endswith(".xml"):
                key = fname[:-4]  # strip .xml
                path = os.path.join(template_dir, fname)
                with open(path, encoding="utf-8") as f:
                    templates[key] = f.read()
        return templates

    # Loaded once at module import time — no I/O on the event loop
    DICT = _load_templates(_TEMPLATES_DIR)


class HargassnerParameter:
    
    _DESCRIPTIONS = { "ZK":"boiler state", "O2":"o2", "O2soll":"o2 target", "TK":"boiler temperature", "TKsoll":"boiler temperature target", "TRG":"smoke gas temperature", 
                      "SZist":"draft", "SZsoll":"draft target", "Leistung":"output", "ESsoll":"delivery rate", "I Es":"drawer current", "I Sr":"grate current", "I Rein":"cleaning current",
                      "Taus":"outside temperature", "TA Gem.":"mean outside temperature", "TPo":"buffer temperature top", "TPm":"buffer temperature center", "TPu":"buffer temperature bottom",
                      "TRL":"return temperature", "TRLsoll":"return temperature target", "LZ ES seit Füll.":"runtime since refill", "LZ ES seit Ent.":"runtime since ash removal",
                      "Anzahl Entasch.":"ash removals", "Anzahl SR Beweg.":"grate movements", "Puff Füllgrad":"buffer level", "Lagerstand":"pellet stock", "Verbrauchszähler":"pellet consumption",
                      "Störungs Nr":"error code", "TVL_1":"flow 1 temperature", "TVLs_1":"flow 1 temperature target", "TVL_2":"flow 2 temperature", "TVLs_2":"flow 2 temperature target",
                      "TVL_3":"flow 3 temperature", "TVLs_3":"flow 3 temperature target", "TVL_4":"flow 4 temperature", "TVLs_4":"flow 4 temperature target",
                      "TVL_5":"flow 5 temperature", "TVLs_5":"flow 5 temperature target", "TVL_6":"flow 6 temperature", "TVLs_6":"flow 6 temperature target",
                      "TB1":"hot water 1 temperature", "TBs_1":"hot water 1 temperature target", "TB2":"hot water 2 temperature", "TBs_2":"hot water 2 temperature target",
                      "TB3":"hot water 3 temperature", "TBs_3":"hot water 3 temperature target", "Störung":"error" }
    
    def __init__(self, key, index, unit):
        self._key = key
        self._index = index
        self._value = None
        self._unit = unit
        if key in ["LZ ES seit Füll.", "LZ ES seit Ent.", "Anzahl Entasch.", "Anzahl SR Beweg.", "Verbrauchszähler"]:
            self._stateClass = "total_increasing"
        elif key=="Lagerstand":
            self._stateClass = "total"
        else:
            self._stateClass = "measurement"
    
    def __str__(self):
        if self.value(): return self.description() + " : " + self.value() + " " + self.unit()
        else: return self.description() + " : unknown"
    
    def key(self):
        return self._key
    
    def index(self):
        return self._index
            
    def value(self):
        return self._value
    
    def unit(self):
        return self._unit
    
    def description(self):
        return HargassnerParameter._DESCRIPTIONS.get(self.key(), self.key())
    
    def stateClass(self):
        return self._stateClass
    
    def isDigital(self):
        return False


class HargassnerAnalogueParameter(HargassnerParameter):
    
    def __init__(self, key, index, unit):
        super().__init__(key, index, unit)
        
    def initializeFromMessage(self, msg):
        self._value = msg[self._index]


class HargassnerDigitalParameter(HargassnerParameter):
    
    def __init__(self, key, index, bitmask):
        super().__init__(key, index, None)
        self._bitmask = bitmask
    
    def initializeFromMessage(self, msg):
        try:
            self._value = str((int(msg[self._index], 16) & self._bitmask) > 0)
        except Exception:
            self._value = None
    
    def isDigital(self):
        return True


class HargassnerBridge(DataUpdateCoordinator):
       
    def __init__(self, hass, hostIP, name, uniqueId, msgFormat):
        super().__init__(
            hass,
            _LOGGER,
            name=name + " connection",
            update_interval=timedelta(seconds=5),
        )
        self._hostIP = hostIP
        self._connectionOK = False
        self._reader = None
        self._writer = None
        self._latestUpdate = None
        self._paramData = {}
        self._expectedMsgLength = 0
        self._missedMsgs = 0
        self._name = name + " connection"
        self._unique_id = uniqueId
        if not self.setMessageFormat(msgFormat):
            raise ValueError(f"Invalid message format: '{msgFormat[:200]}...'")
        
        
    def setMessageFormat(self, msgFormat):
        if msgFormat in HargassnerMessageTemplates.DICT:
            msgFormat = HargassnerMessageTemplates.DICT[msgFormat]  # expand template name to full XML string
        if not msgFormat.startswith("<DAQPRJ>"):
            _LOGGER.error("HargassnerBridge.setMessageFormat(): Message template does not start with '<DAQPRJ>'.")
            return False
        self._paramData = {}
        root = xml.fromstring(msgFormat)
        analog = root.find("ANALOG")
        for channel in analog.findall("CHANNEL"):
            uniqueName = channel.get("name")
            nameCount = 1
            while uniqueName in self._paramData: # in case parameter name is duplicate, add a counter to make it unique
                nameCount += 1
                uniqueName = channel.get("name") + "_" + str(nameCount)
            chUnit = channel.get("unit")
            if chUnit is None: strUnit = None # in case parameter has no unit, do not use string conversion but set explicitly to None
            elif chUnit == "": strUnit = None # also treat empty unit attributes as no unit
            else: strUnit = chUnit
            self._paramData[uniqueName] = HargassnerAnalogueParameter(uniqueName, int(channel.get("id")), strUnit)
        ofsDigital = len(self._paramData) # assuming that channel ids/indices are listed consecutively without any misses!
        lenDigital = 0
        digital = root.find("DIGITAL")
        for channel in digital.findall("CHANNEL"):
            self._paramData[channel.get("name")] = HargassnerDigitalParameter(channel.get("name"), ofsDigital + int(channel.get("id")), 1 << int(channel.get("bit")))
            lenDigital = int(channel.get("id")) + 1 # assuming that channel ids are increasing
        self._expectedMsgLength = ofsDigital + lenDigital
        _LOGGER.info("HargassnerBridge.setMessageFormat(): successfully parsed %d elements.", self._expectedMsgLength)
        return True
        
    async def async_will_remove_from_hass(self) -> None:
        """Close connection."""
        await super().async_will_remove_from_hass()
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
        
    async def _async_update_data(self):
        if self._connectionOK:
            try:
                msgReceived = False
                async with asyncio.timeout(BRIDGE_TIMEOUT):
                    data = await self._reader.read(64*1024)   # read up to 64k
                lines = data.decode().strip().split("\n")
                for l in reversed(lines):
                    msg = l.split()[1:] # remove first field "pm"
                    if len(msg) != self._expectedMsgLength:
                        continue
                    for param in self._paramData.values():
                        param.initializeFromMessage(msg)
                    self._latestUpdate = datetime.now()
                    msgReceived = True
                    self._missedMsgs = 0
                    break
                if not msgReceived:
                    _LOGGER.warning("HargassnerBridge.async_update(): Received message has unexpected length.")
                    self._missedMsgs += 1
                    if self._missedMsgs > 10: self._connectionOK = False    # reconnect if too many errors
            except Exception as e:
                _LOGGER.error("HargassnerBridge.async_update(): Telnet connection error (" + repr(e) + ")")
                self._connectionOK = False
        else:
            _LOGGER.info("HargassnerBridge.async_update(): Opening connection...")
            try:
                if self._writer:
                    self._writer.close()
                    await self._writer.wait_closed()
                async with asyncio.timeout(BRIDGE_TIMEOUT):
                    self._reader, self._writer = await asyncio.open_connection(self._hostIP, TELNET_PORT)
                self._connectionOK = True
            except Exception:
                _LOGGER.error("HargassnerBridge.async_update(): Error opening connection")
                raise UpdateFailed("Error opening connection")
        
        return self._paramData
    
    @property
    def is_connected(self) -> bool:
        return self._connectionOK
    
    @property
    def state(self) -> str:
        if self._connectionOK: return BRIDGE_STATE_OK
        else: return BRIDGE_STATE_DISCONNECTED
        
    @property
    def unique_id(self) -> str:
        return self._unique_id

    def getUniqueIdBase(self):
        return self._unique_id

    def getValue(self, paramName):
        param = self._paramData.get(paramName)
        if param==None: 
            _LOGGER.warning("HargassnerBridge.getValue(): Parameter key " + paramName + " not known.")
            return None 
        return param.value()
    
    def getUnit(self, paramName):
        param = self._paramData.get(paramName)
        if param==None: 
            _LOGGER.warning("HargassnerBridge.getUnit(): Parameter key " + paramName + " not known.")
            return None 
        return param.unit()
    
    def getStateClass(self, paramName):
        param = self._paramData.get(paramName)
        if param==None: 
            _LOGGER.warning("HargassnerBridge.getStateClass(): Parameter key " + paramName + " not known.")
            return None 
        return param.stateClass()
    
    def isDigital(self, paramName):
        param = self._paramData.get(paramName)
        if param==None:
            _LOGGER.warning("HargassnerBridge.isDigital(): Parameter key " + paramName + " not known.")
            return False
        return param.isDigital()
    
    def parameters(self):
        return self._paramData
    
    def latestUpdateTime(self):
        return self._latestUpdate
