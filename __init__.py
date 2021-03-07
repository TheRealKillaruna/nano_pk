"""The Hargassner Nano-PK boiler temperature sensor integration."""
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

DOMAIN = "nano_pk"

CONF_HOST = "host"
CONF_NAME = "devicename"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default="Nano-PK"): cv.string,
    })
}, extra=vol.ALLOW_EXTRA
)

def setup(hass, config):
    """Your controller/hub specific code."""
    # Data that you want to share with your platforms
#    hass.data[DOMAIN] = {
#        'temperature': 23
#    }

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][CONF_HOST] = config[DOMAIN].get(CONF_HOST) #"192.168.0.161"
    hass.data[DOMAIN][CONF_NAME] = config[DOMAIN].get(CONF_NAME)

    hass.helpers.discovery.load_platform('sensor', DOMAIN, {}, config)

    return True