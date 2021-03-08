"""The Hargassner Nano-PK boiler temperature sensor integration."""
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from .hargassner import HargassnerMessageTemplates as hmt

DOMAIN = "nano_pk"

CONF_HOST = "host"
CONF_FORMAT = "msgformat"
CONF_NAME = "devicename"
CONF_PARAMS = "parameters"
CONF_PARAMS_STANDARD = "STANDARD"
CONF_PARAMS_FULL = "FULL"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_FORMAT): cv.string,
        vol.Optional(CONF_NAME, default="Hargassner"): cv.string,
        vol.Optional(CONF_PARAMS, default=CONF_PARAMS_STANDARD): vol.In([CONF_PARAMS_STANDARD,CONF_PARAMS_FULL]),
    })
}, extra=vol.ALLOW_EXTRA
)


def setup(hass, config):
    
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][CONF_HOST] = config[DOMAIN].get(CONF_HOST)
    hass.data[DOMAIN][CONF_NAME] = config[DOMAIN].get(CONF_NAME)
    hass.data[DOMAIN][CONF_FORMAT] = config[DOMAIN].get(CONF_FORMAT)
    hass.data[DOMAIN][CONF_PARAMS] = config[DOMAIN].get(CONF_PARAMS)

    hass.helpers.discovery.load_platform('sensor', DOMAIN, {}, config)

    return True