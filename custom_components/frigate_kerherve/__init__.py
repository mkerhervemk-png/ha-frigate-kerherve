"""Frigate Kerherve : santé des caméras et services de configuration, en complément de l'intégration Frigate officielle."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import FrigateApi, FrigateApiError
from .const import CONF_URL, DOMAIN
from .coordinator import FrigateKerherveConfigEntry, FrigateKerherveCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def _api(hass: HomeAssistant) -> FrigateApi:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return entry.runtime_data.api
    raise ServiceValidationError("Frigate Kerherve n'est pas configuré ou pas chargé")


async def _call(hass: HomeAssistant, method: str, path: str, json: Any = None) -> Any:
    try:
        return await _api(hass).request(method, path, json=json, timeout=60)
    except FrigateApiError as err:
        raise HomeAssistantError(f"Frigate : {err}") from err


def _wrap(data: Any) -> ServiceResponse:
    return data if isinstance(data, dict) else {"result": data}


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Enregistre les services."""

    async def set_config(call: ServiceCall) -> ServiceResponse:
        body = {
            "requires_restart": 1 if call.data["requires_restart"] else 0,
            "config_data": call.data["config_data"],
        }
        return _wrap(await _call(hass, "PUT", "config/set", body))

    async def get_config(call: ServiceCall) -> ServiceResponse:
        data = await _call(hass, "GET", "config")
        for key in [k for k in call.data.get("path", "").split(".") if k]:
            if not isinstance(data, dict) or key not in data:
                raise ServiceValidationError(f"Clé introuvable dans la config : {key}")
            data = data[key]
        return _wrap(data)

    async def restart(call: ServiceCall) -> None:
        await _call(hass, "POST", "restart")

    async def list_faces(call: ServiceCall) -> ServiceResponse:
        return _wrap(await _call(hass, "GET", "faces"))

    async def delete_faces(call: ServiceCall) -> ServiceResponse:
        return _wrap(
            await _call(
                hass, "POST", f"faces/{call.data['name']}/delete", {"ids": call.data["ids"]}
            )
        )

    async def classify_face(call: ServiceCall) -> ServiceResponse:
        return _wrap(
            await _call(
                hass,
                "POST",
                f"faces/train/{call.data['name']}/classify",
                {"training_file": call.data["training_file"]},
            )
        )

    opt = SupportsResponse.OPTIONAL
    hass.services.async_register(
        DOMAIN,
        "set_config",
        set_config,
        vol.Schema(
            {
                vol.Required("config_data"): dict,
                vol.Optional("requires_restart", default=True): cv.boolean,
            }
        ),
        supports_response=opt,
    )
    hass.services.async_register(
        DOMAIN,
        "get_config",
        get_config,
        vol.Schema({vol.Optional("path", default=""): cv.string}),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(DOMAIN, "restart", restart, vol.Schema({}))
    hass.services.async_register(
        DOMAIN, "list_faces", list_faces, vol.Schema({}), supports_response=SupportsResponse.ONLY
    )
    hass.services.async_register(
        DOMAIN,
        "delete_faces",
        delete_faces,
        vol.Schema(
            {
                vol.Required("name"): cv.string,
                vol.Required("ids"): vol.All(cv.ensure_list, [cv.string]),
            }
        ),
        supports_response=opt,
    )
    hass.services.async_register(
        DOMAIN,
        "classify_face",
        classify_face,
        vol.Schema(
            {vol.Required("name"): cv.string, vol.Required("training_file"): cv.string}
        ),
        supports_response=opt,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: FrigateKerherveConfigEntry) -> bool:
    """Démarre le coordinateur et les capteurs."""
    api = FrigateApi(async_get_clientsession(hass), entry.data[CONF_URL])
    coordinator = FrigateKerherveCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FrigateKerherveConfigEntry) -> bool:
    """Décharge l'entrée."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
