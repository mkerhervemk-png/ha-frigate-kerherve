"""Base des entités Frigate Kerherve."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FrigateKerherveCoordinator


def to_float(value: Any) -> float | None:
    """Convertit en nombre (Frigate renvoie certains pourcentages en texte)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class FrigateKerherveEntity(CoordinatorEntity[FrigateKerherveCoordinator]):
    """Entité rattachée au serveur Frigate ou à une caméra."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: FrigateKerherveCoordinator, key: str, camera: str | None = None
    ) -> None:
        super().__init__(coordinator)
        entry_id = coordinator.config_entry.entry_id
        self._camera = camera
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry_id}_{camera or 'server'}_{key}"
        if camera:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{entry_id}_{camera}")},
                name=f"Frigate santé {camera}",
                manufacturer="Frigate",
            )
        else:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, entry_id)},
                name="Frigate santé",
                manufacturer="Frigate",
                sw_version=(coordinator.data.get("service") or {}).get("version"),
            )

    @property
    def camera_stats(self) -> dict[str, Any]:
        """Statistiques de la caméra de l'entité."""
        return (self.coordinator.data.get("cameras") or {}).get(self._camera) or {}
