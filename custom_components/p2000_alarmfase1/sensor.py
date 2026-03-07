"""Sensor platform for P2000 Scraper."""
import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    SCRAPED_DATA_KEYS,
    CONF_SENSORS,
    CONF_FILTERS,
    CONF_FILTER_AMBULANCE,
    CONF_FILTER_FIRE,
    CONF_FILTER_POLICE,
    CONF_FILTER_OTHER,
    CONF_INSTANCE_NAME,
    DEFAULT_ENABLED_SENSORS,
)
from .coordinator import Alarmfase1DataUpdateCoordinator
from .entity import Alarmfase1BaseEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the P2000 sensor platform."""
    coordinator: Alarmfase1DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create the main sensor representing the latest message
    entities = [P2000Sensor(coordinator)]

    # Add diagnostic sensors
    entities.extend([
        P2000DiagnosticSensor(coordinator, "status", "Status", "mdi:check-network-outline"),
        P2000DiagnosticSensor(coordinator, "last_update", "Laatste Update", "mdi:clock-check-outline"),
    ])

    async_add_entities(entities)


class P2000Sensor(Alarmfase1BaseEntity, SensorEntity):
    """Representation of the latest P2000 message sensor."""

    _attr_has_entity_name = False
    _attr_name = None

    def __init__(self, coordinator: Alarmfase1DataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.data[CONF_INSTANCE_NAME]}_latest_message"
        self._previous_data: dict | None = None
        self._message_matches_filter = True

    @property
    def state(self) -> StateType:
        """Return the state of the sensor."""
        data_to_use = self.coordinator.data if self._message_matches_filter else self._previous_data
        return data_to_use.get("priority_code") if data_to_use else None

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return the state attributes."""
        data_to_use = self.coordinator.data if self._message_matches_filter else self._previous_data
        if not data_to_use:
            return None

        enabled_sensors = self.coordinator.config_entry.options.get(CONF_SENSORS, {})
        attributes = {}
        for key in SCRAPED_DATA_KEYS:
            is_enabled = enabled_sensors.get(key, key in DEFAULT_ENABLED_SENSORS)

            if key != "priority_code" and is_enabled and key in data_to_use:
                value = data_to_use[key]
                if key == "latitude":
                    attributes[ATTR_LATITUDE] = value
                elif key == "longitude":
                    attributes[ATTR_LONGITUDE] = value
                elif isinstance(value, datetime):
                    attributes[key] = dt_util.as_local(value) if value else None
                else:
                    attributes[key] = value

        attributes["matches_filter"] = self._message_matches_filter
        attributes["last_update_attempt"] = dt_util.now()

        return attributes

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend based on service type."""
        data_to_use = self.coordinator.data if self._message_matches_filter else self._previous_data
        service_type = data_to_use.get("service_type") if data_to_use else None

        if service_type == "Ambulance":
            return "mdi:ambulance"
        if service_type == "Fire Department":
            return "mdi:fire-truck"
        if service_type == "Police":
            return "mdi:police-car"
        if service_type == "Trauma Heli":
            return "mdi:helicopter"
        if service_type == "KNRM / Water Rescue":
            return "mdi:lifebuoy"
        return "mdi:alert-circle-outline"

    def _matches_filters(self, data: dict | None) -> bool:
        """Check if the message data matches the configured filters."""
        if not data:
            return True

        filters = self.coordinator.config_entry.options.get(CONF_FILTERS, {})
        service_type = data.get("service_type")

        if service_type == "Ambulance" and not filters.get(CONF_FILTER_AMBULANCE, True):
            return False
        if service_type == "Fire Department" and not filters.get(CONF_FILTER_FIRE, True):
            return False
        if service_type == "Police" and not filters.get(CONF_FILTER_POLICE, True):
            return False
        
        if service_type not in ["Ambulance", "Fire Department", "Police"] and not filters.get(CONF_FILTER_OTHER, True):
            return False

        return True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        latest_data = self.coordinator.data
        self._message_matches_filter = self._matches_filters(latest_data)

        if self._message_matches_filter:
            self._previous_data = latest_data

        self.async_write_ha_state()


class P2000DiagnosticSensor(Alarmfase1BaseEntity, SensorEntity):
    """Representation of a clean P2000 Diagnostic Sensor."""
    
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: Alarmfase1DataUpdateCoordinator,
        data_key: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the diagnostic sensor."""
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_diag_{data_key}"
        self._attr_name = f"{coordinator.config_entry.data[CONF_INSTANCE_NAME]} {name}"
        self._attr_icon = icon
        self._attr_has_entity_name = False

    @property
    def native_value(self) -> StateType:
        """Return the state of the diagnostic sensor."""
        if self._data_key == "status":
            if self.coordinator.last_update_error:
                return f"Fout ({self.coordinator.error_count} mislukt)"
            return "OK"
            
        elif self._data_key == "last_update":
            ts = self.coordinator.last_update_success_timestamp
            if ts:
                try:
                    # Convert the raw computer timestamp into a clean Dutch format
                    dt = dt_util.parse_datetime(ts)
                    if dt:
                        # Ensures it looks like: 06-03-2026 14:30:00
                        return dt.strftime("%d-%m-%Y %H:%M:%S")
                except Exception:
                    pass
            # Fallback text just like the Weerplaza integration!
            return "Uit Cache (Wacht op timer)"
            
        return None

    @property
    def available(self) -> bool:
        """Diagnostics are always available if the coordinator exists."""
        return self.coordinator is not None
