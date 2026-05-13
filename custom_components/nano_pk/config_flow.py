"""Config flow for Hargassner Nano-PK integration."""
import asyncio
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_FORMAT,
    CONF_NAME,
    CONF_PARAMS,
    CONF_PARAMS_STANDARD,
    CONF_PARAMS_FULL,
    CONF_LANG,
    CONF_LANG_EN,
    CONF_LANG_DE,
    CONF_LANG_FR,
    CONF_UNIQUE_ID,
    BRIDGE_TIMEOUT,
)
from .hargassner import HargassnerMessageTemplates

_LOGGER = logging.getLogger(__name__)

TEMPLATES = [
    HargassnerMessageTemplates.NANO_V14K,
    HargassnerMessageTemplates.NANO_V14L,
    HargassnerMessageTemplates.NANO_V14M,
    HargassnerMessageTemplates.NANO_V14N,
    HargassnerMessageTemplates.NANO_V14N2,
    HargassnerMessageTemplates.NANO_V14O3,
]


class NanoPKConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hargassner Nano-PK."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(user_input[CONF_HOST], 23),
                    timeout=BRIDGE_TIMEOUT,
                )
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
            except (OSError, asyncio.TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input[CONF_UNIQUE_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_FORMAT): vol.In(TEMPLATES),
                vol.Optional(CONF_NAME, default="Hargassner"): str,
                vol.Optional(CONF_UNIQUE_ID, default="1"): str,
                vol.Optional(CONF_PARAMS, default=CONF_PARAMS_STANDARD): vol.In(
                    [CONF_PARAMS_STANDARD, CONF_PARAMS_FULL]
                ),
                vol.Optional(CONF_LANG, default=CONF_LANG_EN): vol.In(
                    [CONF_LANG_EN, CONF_LANG_DE, CONF_LANG_FR]
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_import(self, import_config: dict) -> FlowResult:
        """Handle import from YAML configuration."""
        await self.async_set_unique_id(import_config.get(CONF_UNIQUE_ID, "1"))
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=import_config.get(CONF_NAME, "Hargassner"),
            data=import_config,
        )
