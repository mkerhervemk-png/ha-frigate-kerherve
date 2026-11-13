"""Flux de configuration : une seule question, l'adresse de Frigate."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FrigateApi, FrigateApiError
from .const import CONF_URL, DEFAULT_URL, DOMAIN


class FrigateKerherveConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configuration de Frigate Kerherve."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            try:
                await FrigateApi(async_get_clientsession(self.hass), url).version()
            except FrigateApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="Frigate Kerherve", data={CONF_URL: url})
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_URL, default=(user_input or {}).get(CONF_URL, DEFAULT_URL)): str}
            ),
            errors=errors,
        )
