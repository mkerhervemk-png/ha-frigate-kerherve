"""Capteur « problème » par caméra."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import PROBLEM_RECONNECTS, PROBLEM_STALLS
from .coordinator import FrigateKerherveConfigEntry
from .entity import FrigateKerherveEntity, to_float


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FrigateKerherveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crée un capteur de problème par caméra."""
    coordinator = entry.runtime_data
    async_add_entities(
        FrigateCameraProblem(coordinator, "camera_problem", camera)
        for camera in coordinator.data.get("cameras") or {}
    )


class FrigateCameraProblem(FrigateKerherveEntity, BinarySensorEntity):
    """Actif si la caméra ne donne plus d'image ou décroche trop souvent."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool | None:
        stats = self.camera_stats
        if not stats:
            return None
        return (
            (to_float(stats.get("camera_fps")) or 0) == 0
            or (to_float(stats.get("reconnects_last_hour")) or 0) >= PROBLEM_RECONNECTS
            or (to_float(stats.get("stalls_last_hour")) or 0) >= PROBLEM_STALLS
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        stats = self.camera_stats
        return {
            k: stats.get(k)
            for k in ("connection_quality", "reconnects_last_hour", "stalls_last_hour", "camera_fps")
        }
