"""Coordinateur : lit /api/stats une fois par minute."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FrigateApi, FrigateApiError
from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)

type FrigateKerherveConfigEntry = ConfigEntry[FrigateKerherveCoordinator]


class FrigateKerherveCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Récupère les statistiques de Frigate."""

    def __init__(
        self, hass: HomeAssistant, entry: FrigateKerherveConfigEntry, api: FrigateApi
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.stats()
        except FrigateApiError as err:
            raise UpdateFailed(f"Frigate injoignable : {err}") from err
