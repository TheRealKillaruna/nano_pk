"""The Hargassner Nano-PK integration."""
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

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
    CONF_LANG_DE,
    CONF_LANG_FR,
)
from .hargassner import HargassnerBridge

PLATFORMS = [Platform.SENSOR]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_FORMAT): cv.string,
                vol.Optional(CONF_NAME, default="Hargassner"): cv.string,
                vol.Optional(CONF_UNIQUE_ID, default="1"): cv.string,
                vol.Optional(CONF_PARAMS, default=CONF_PARAMS_STANDARD): vol.In(
                    [CONF_PARAMS_STANDARD, CONF_PARAMS_FULL]
                ),
                vol.Optional(CONF_LANG, default=CONF_LANG_EN): vol.In(
                    [CONF_LANG_EN, CONF_LANG_DE, CONF_LANG_FR]
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Nano-PK integration from YAML."""
    if DOMAIN not in config:
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data=dict(config[DOMAIN]),
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nano-PK from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    name = entry.data[CONF_NAME]
    unique_id = entry.data[CONF_UNIQUE_ID]
    msg_format = entry.data[CONF_FORMAT]

    bridge = HargassnerBridge(hass, host, name, unique_id, msgFormat=msg_format)
    await bridge.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = bridge

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        bridge = hass.data[DOMAIN].pop(entry.entry_id)
        if bridge._writer:
            bridge._writer.close()
            try:
                await bridge._writer.wait_closed()
            except Exception:
                pass

    return unload_ok
