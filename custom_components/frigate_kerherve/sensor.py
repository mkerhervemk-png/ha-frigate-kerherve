"""Capteurs de santé de Frigate."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FrigateKerherveConfigEntry, FrigateKerherveCoordinator
from .entity import FrigateKerherveEntity, to_float

MEASUREMENT = SensorStateClass.MEASUREMENT
DIAGNOSTIC = EntityCategory.DIAGNOSTIC


@dataclass(frozen=True, kw_only=True)
class FrigateSensorDescription(SensorEntityDescription):
    """Description d'un capteur : value_fn reçoit les stats (caméra ou serveur)."""

    value_fn: Callable[[dict[str, Any]], Any]


def _storage_percent(data: dict[str, Any]) -> float | None:
    storage = ((data.get("service") or {}).get("storage") or {}).get(
        "/media/frigate/recordings"
    ) or {}
    total, used = to_float(storage.get("total")), to_float(storage.get("used"))
    return round(used / total * 100, 1) if total and used is not None else None


def _inference(data: dict[str, Any]) -> float | None:
    speeds = [
        s
        for d in (data.get("detectors") or {}).values()
        if (s := to_float((d or {}).get("inference_speed"))) is not None
    ]
    return max(speeds) if speeds else None


def _system(key: str) -> Callable[[dict[str, Any]], float | None]:
    return lambda d: to_float(
        ((d.get("cpu_usages") or {}).get("frigate.full_system") or {}).get(key)
    )


def _embedding(key: str) -> Callable[[dict[str, Any]], float | None]:
    return lambda d: (
        None if (v := to_float((d.get("embeddings") or {}).get(key))) is None else round(v, 1)
    )


CAMERA_SENSORS: tuple[FrigateSensorDescription, ...] = (
    FrigateSensorDescription(
        key="connection_quality", value_fn=lambda c: c.get("connection_quality")
    ),
    FrigateSensorDescription(
        key="reconnects_last_hour",
        state_class=MEASUREMENT,
        value_fn=lambda c: c.get("reconnects_last_hour"),
    ),
    FrigateSensorDescription(
        key="stalls_last_hour",
        state_class=MEASUREMENT,
        value_fn=lambda c: c.get("stalls_last_hour"),
    ),
    FrigateSensorDescription(
        key="ffmpeg_cpu",
        native_unit_of_measurement=PERCENTAGE,
        state_class=MEASUREMENT,
        entity_category=DIAGNOSTIC,
        value_fn=lambda c: to_float(c.get("ffmpeg_cpu")),
    ),
    FrigateSensorDescription(
        key="camera_fps",
        native_unit_of_measurement="FPS",
        state_class=MEASUREMENT,
        entity_category=DIAGNOSTIC,
        value_fn=lambda c: to_float(c.get("camera_fps")),
    ),
)

SERVER_SENSORS: tuple[FrigateSensorDescription, ...] = (
    FrigateSensorDescription(
        key="system_cpu",
        native_unit_of_measurement=PERCENTAGE,
        state_class=MEASUREMENT,
        value_fn=_system("cpu"),
    ),
    FrigateSensorDescription(
        key="system_memory",
        native_unit_of_measurement=PERCENTAGE,
        state_class=MEASUREMENT,
        value_fn=_system("mem"),
    ),
    FrigateSensorDescription(
        key="storage_used",
        native_unit_of_measurement=PERCENTAGE,
        state_class=MEASUREMENT,
        value_fn=_storage_percent,
    ),
    FrigateSensorDescription(
        key="inference_speed",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=MEASUREMENT,
        entity_category=DIAGNOSTIC,
        value_fn=_inference,
    ),
    FrigateSensorDescription(
        key="face_recognition_speed",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=MEASUREMENT,
        entity_category=DIAGNOSTIC,
        value_fn=_embedding("face_recognition_speed"),
    ),
    FrigateSensorDescription(
        key="plate_recognition_speed",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=MEASUREMENT,
        entity_category=DIAGNOSTIC,
        value_fn=_embedding("plate_recognition_speed"),
    ),
    FrigateSensorDescription(
        key="object_description_speed",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=MEASUREMENT,
        entity_category=DIAGNOSTIC,
        value_fn=_embedding("object_description_speed"),
    ),
    FrigateSensorDescription(
        key="uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        suggested_display_precision=1,
        entity_category=DIAGNOSTIC,
        value_fn=lambda d: (d.get("service") or {}).get("uptime"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FrigateKerherveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crée les capteurs du serveur et de chaque caméra."""
    coordinator = entry.runtime_data
    entities: list[FrigateSensor] = [FrigateSensor(coordinator, d) for d in SERVER_SENSORS]
    entities += [
        FrigateSensor(coordinator, d, camera)
        for camera in coordinator.data.get("cameras") or {}
        for d in CAMERA_SENSORS
    ]
    async_add_entities(entities)


class FrigateSensor(FrigateKerherveEntity, SensorEntity):
    """Capteur de santé."""

    entity_description: FrigateSensorDescription

    def __init__(
        self,
        coordinator: FrigateKerherveCoordinator,
        description: FrigateSensorDescription,
        camera: str | None = None,
    ) -> None:
        super().__init__(coordinator, description.key, camera)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        source = self.camera_stats if self._camera else self.coordinator.data
        return self.entity_description.value_fn(source)
