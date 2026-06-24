"""Config flow for Stiga G1200 BLE integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_MAC, LOGGER

class StigaBleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Stiga G1200 BLE."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            mac = user_input[CONF_MAC]
            
            # Ensure unique entry per MAC
            await self.async_set_unique_id(mac.lower())
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Stiga Mower ({mac})", 
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MAC): cv.string,
                }
            ),
            errors=errors,
        )
