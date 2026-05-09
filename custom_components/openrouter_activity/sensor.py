"""Sensors for OpenRouter Activity integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_BASELINE_MONTH,
    ATTR_BASELINE_USED_CREDITS,
    COORDINATOR,
    DOMAIN,
)
from .coordinator import OpenRouterDataUpdateCoordinator


def _round2(value: float | None) -> float | None:
    """Round to 2 decimal places, or return None when no value available."""
    return round(value, 2) if value is not None else None


@dataclass(frozen=True, kw_only=True)
class OpenRouterSensorDescription(SensorEntityDescription):
    """Description of OpenRouter sensor."""

    value_fn: Any


SENSOR_DESCRIPTIONS: tuple[OpenRouterSensorDescription, ...] = (
    OpenRouterSensorDescription(
        key="total_credits",
        name="OpenRouter Total Credits",
        value_fn=lambda data: _round2(data.get("credits", {}).get("total_credits")),
        native_unit_of_measurement="USD",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash-multiple",
    ),
    OpenRouterSensorDescription(
        key="used_credits",
        name="OpenRouter Used Credits",
        value_fn=lambda data: _round2(data.get("credits", {}).get("total_usage")),
        native_unit_of_measurement="USD",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash-minus",
    ),
    OpenRouterSensorDescription(
        key="remaining_credits",
        name="OpenRouter Remaining Credits",
        value_fn=lambda data: round(
            max(
                float(data.get("credits", {}).get("total_credits", 0.0) or 0.0)
                - float(data.get("credits", {}).get("total_usage", 0.0) or 0.0),
                0.0,
            ),
            2,
        ),
        native_unit_of_measurement="USD",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash-check",
    ),
    OpenRouterSensorDescription(
        key="current_month_spend",
        name="OpenRouter Current Month Spend",
        value_fn=lambda data: _round2(data.get("monthly", {}).get("current_month_spend")),
        native_unit_of_measurement="USD",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:currency-usd",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenRouter sensors based on a config entry."""
    coordinator: OpenRouterDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    async_add_entities(
        OpenRouterActivitySensor(
            coordinator=coordinator,
            config_entry=entry,
            description=description,
        )
        for description in SENSOR_DESCRIPTIONS
    )


class OpenRouterActivitySensor(CoordinatorEntity[OpenRouterDataUpdateCoordinator], SensorEntity):
    """Representation of an OpenRouter activity sensor."""

    entity_description: OpenRouterSensorDescription

    def __init__(
        self,
        coordinator: OpenRouterDataUpdateCoordinator,
        config_entry: ConfigEntry,
        description: OpenRouterSensorDescription,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True

    @property
    def native_value(self) -> float | int | None:
        """Return sensor state."""
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        monthly = data.get("monthly", {})

        attrs: dict[str, Any] = {}

        if self.entity_description.key == "current_month_spend":
            attrs[ATTR_BASELINE_MONTH] = monthly.get(ATTR_BASELINE_MONTH)
            attrs[ATTR_BASELINE_USED_CREDITS] = monthly.get(ATTR_BASELINE_USED_CREDITS)
            attrs["current_total_usage"] = monthly.get("current_total_usage")

        return attrs
