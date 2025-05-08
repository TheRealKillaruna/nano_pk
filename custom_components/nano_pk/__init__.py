"""The Hargassner Nano-PK boiler temperature sensor integration."""
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_FORMAT,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CONF_PARAMS,
    CONF_PARAMS_STANDARD,
    CONF_PARAMS_FULL,
    CONF_LANG,
    CONF_LANG_EN,
    CONF_LANG_DE
)


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_FORMAT): cv.string,
        vol.Optional(CONF_NAME, default="Hargassner"): cv.string,
        vol.Optional(CONF_UNIQUE_ID, default="1"): cv.string,
        vol.Optional(CONF_PARAMS, default=CONF_PARAMS_STANDARD): vol.In([CONF_PARAMS_STANDARD,CONF_PARAMS_FULL]),
        vol.Optional(CONF_LANG, default=CONF_LANG_EN): vol.In([CONF_LANG_EN,CONF_LANG_DE]),
    })
}, extra=vol.ALLOW_EXTRA
)


async def async_setup(hass, config) -> bool:
    
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][CONF_HOST] = config[DOMAIN].get(CONF_HOST)
    hass.data[DOMAIN][CONF_NAME] = config[DOMAIN].get(CONF_NAME)
    hass.data[DOMAIN][CONF_FORMAT] = config[DOMAIN].get(CONF_FORMAT)
    hass.data[DOMAIN][CONF_PARAMS] = config[DOMAIN].get(CONF_PARAMS)
    hass.data[DOMAIN][CONF_LANG] = config[DOMAIN].get(CONF_LANG)
    hass.data[DOMAIN][CONF_UNIQUE_ID] = config[DOMAIN].get(CONF_UNIQUE_ID)

    await async_load_platform(hass, 'sensor', DOMAIN, {}, config)

    return True
