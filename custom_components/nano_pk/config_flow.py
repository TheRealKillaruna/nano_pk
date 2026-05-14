"""Config flow for Hargassner Nano-PK integration."""
import asyncio
import logging
import xml.etree.ElementTree as xml
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

FORMAT_OPTIONS = TEMPLATES + ["custom"]


class NanoPKConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hargassner Nano-PK."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        super().__init__()
        self._user_input = None
        self._reconfigure_entry = None

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
                if user_input[CONF_FORMAT] == "custom":
                    self._user_input = user_input
                    return await self.async_step_custom_xml()
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_FORMAT): vol.In(FORMAT_OPTIONS),
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

    async def async_step_custom_xml(self, user_input=None):
        """Handle custom XML message format input."""
        errors = {}

        if user_input is not None:
            custom_xml = user_input.get("custom_xml", "").strip()
            if not custom_xml.startswith("<DAQPRJ>"):
                errors["custom_xml"] = "invalid_xml"
            else:
                try:
                    xml.fromstring(custom_xml)
                except xml.ParseError:
                    errors["custom_xml"] = "invalid_xml"

            if not errors:
                if self._reconfigure_entry is not None:
                    new_data = {
                        **self._reconfigure_entry.data,
                        **self._user_input,
                        CONF_FORMAT: custom_xml,
                    }
                    return self.async_update_reload_and_abort(
                        self._reconfigure_entry, data=new_data
                    )
                full_input = {**self._user_input, CONF_FORMAT: custom_xml}
                return self.async_create_entry(
                    title=full_input[CONF_NAME],
                    data=full_input,
                )

        # Pre-fill with current custom XML when reconfiguring
        default_xml = ""
        if self._reconfigure_entry is not None:
            current = self._reconfigure_entry.data.get(CONF_FORMAT, "")
            if current not in TEMPLATES:
                default_xml = current

        data_schema = vol.Schema(
            {
                vol.Required("custom_xml", default=default_xml): str,
            }
        )

        return self.async_show_form(
            step_id="custom_xml",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input=None):
        """Handle reconfiguration of an existing entry."""
        errors = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

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
                if user_input[CONF_FORMAT] == "custom":
                    self._reconfigure_entry = entry
                    self._user_input = user_input
                    return await self.async_step_custom_xml()
                new_data = {**entry.data, **user_input}
                return self.async_update_reload_and_abort(entry, data=new_data)

        current_format = entry.data.get(CONF_FORMAT, "")
        format_default = current_format if current_format in FORMAT_OPTIONS else "custom"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str,
                vol.Required(CONF_FORMAT, default=format_default): vol.In(FORMAT_OPTIONS),
                vol.Optional(CONF_NAME, default=entry.data.get(CONF_NAME, "Hargassner")): str,
                vol.Optional(CONF_PARAMS, default=entry.data.get(CONF_PARAMS, CONF_PARAMS_STANDARD)): vol.In(
                    [CONF_PARAMS_STANDARD, CONF_PARAMS_FULL]
                ),
                vol.Optional(CONF_LANG, default=entry.data.get(CONF_LANG, CONF_LANG_EN)): vol.In(
                    [CONF_LANG_EN, CONF_LANG_DE, CONF_LANG_FR]
                ),
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
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
