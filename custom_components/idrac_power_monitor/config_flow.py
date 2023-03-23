"""
Config flow for the iDrac Power Monitor Home Assistant integration.
"""

from __future__ import annotations
import logging
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant as hass
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, JSON_MODEL
from .idrac_rest import IdracRest, CannotConnect, InvalidAuth, RedfishConfig

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str
    }
)

@config_entries.HANDLERS.register(DOMAIN)
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iDrac REST."""

    VERSION = 1

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}
        info = None

        try:
            info = await self.validate_input(user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except RedfishConfig:
            errors["base"] = "redfish_config"
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception: %s", ex)
            errors["base"] = "unknown"

        if not errors and info:
            return self.async_create_entry(title=info["model_name"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors
        )

    async def validate_input(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate the user's input by creating an IdracRest object and checking for connection errors.

        :param data: The user's input data.
        :return: A dictionary containing the model_name key with the model name as its value.
        """
        rest_client = IdracRest(
            host=data[CONF_HOST],
            username=data[CONF_USERNAME],
            password=data[CONF_PASSWORD]
        )

        device_info = await hass.async_add_executor_job(
            self.hass, target=rest_client.get_device_info
        )
        model_name = device_info[JSON_MODEL]

        return {"model_name": model_name}
