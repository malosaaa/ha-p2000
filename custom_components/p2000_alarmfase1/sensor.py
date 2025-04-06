"""Sensor platform for P2000 Scraper."""
import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util # Use Home Assistant's timezone functions

from .const import (
    DOMAIN,
    SCRAPED_DATA_KEYS,
    CONF_SENSORS,
    CONF_FILTERS,
    CONF_FILTER_AMBULANCE,
    CONF_FILTER_FIRE,
    CONF_FILTER_POLICE,
    CONF_FILTER_OTHER,
    CONF_INSTANCE_NAME,  # Add this line
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
        P2000DiagnosticSensor(coordinator, "last_update_status", "Last Update Status"),
        P2000DiagnosticSensor(coordinator, "last_update_time", "Coordinator Last Update", SensorDeviceClass.TIMESTAMP),
        P2000DiagnosticSensor(coordinator, "consecutive_errors", "Consecutive Update Errors"),
    ])


    async_add_entities(entities)


class P2000Sensor(Alarmfase1BaseEntity, SensorEntity):
    """Representation of the latest P2000 message sensor."""

    # Use device name provided by user, set entity name to None for default HA naming
    _attr_has_entity_name = False # Sensor will be named after the device
    _attr_name = None # Use device name

    def __init__(self, coordinator: Alarmfase1DataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        # Set unique ID based on config entry ID for the main sensor
        self._attr_unique_id = f"{coordinator.config_entry.data[CONF_INSTANCE_NAME]}_latest_message"
        self._previous_data: dict | None = None # Store previous data if filtered
        self._message_matches_filter = True # Assume matches initially

    @property
    def state(self) -> StateType:
        """Return the state of the sensor (Priority Code of latest matching message)."""
        # Return priority code from the latest data that passed the filter
        data_to_use = self.coordinator.data if self._message_matches_filter else self._previous_data
        return data_to_use.get("priority_code") if data_to_use else None

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return the state attributes."""
        # Return attributes from the latest data that passed the filter
        data_to_use = self.coordinator.data if self._message_matches_filter else self._previous_data
        if not data_to_use:
            return None

        # Get enabled sensors from options
        enabled_sensors = self.coordinator.config_entry.options.get(CONF_SENSORS, {})
        attributes = {}
        for key in SCRAPED_DATA_KEYS:
            # Include attribute if it's enabled in options AND exists in data
            # Exclude priority_code as it's the main state
            if key != "priority_code" and enabled_sensors.get(key, False) and key in data_to_use:
                value = data_to_use[key]
                # Use standard Home Assistant attribute constants if applicable
                if key == "latitude":
                    attributes[ATTR_LATITUDE] = value
                elif key == "longitude":
                    attributes[ATTR_LONGITUDE] = value
                elif isinstance(value, datetime):
                    # Ensure datetime is timezone-aware using HA helpers
                    attributes[key] = dt_util.as_local(value) if value else None
                else:
                    attributes[key] = value

        attributes["matches_filter"] = self._message_matches_filter # Indicate if the *very latest* scrape matches
        attributes["last_update_attempt"] = dt_util.now() # Timestamp of the last coordinator update attempt

        return attributes

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend based on service type."""
        # Use icon from the latest data that passed the filter
        data_to_use = self.coordinator.data if self._message_matches_filter else self._previous_data
        service_type = data_to_use.get("service_type") if data_to_use else None

        if service_type == "Ambulance":
            return "mdi:ambulance"
        if service_type == "Fire Department":
            return "mdi:fire-truck"
        if service_type == "Police":
            return "mdi:police-car" # Or mdi:police-badge
        if service_type == "Trauma Heli":
            return "mdi:helicopter"
        if service_type == "KNRM / Water Rescue":
            return "mdi:lifebuoy"
        return "mdi:alert-circle-outline" # Default alert icon


    def _matches_filters(self, data: dict | None) -> bool:
        """Check if the message data matches the configured filters."""
        if not data: # No data available
            return True # Treat as matching so sensor doesn't get stuck

        filters = self.coordinator.config_entry.options.get(CONF_FILTERS, {})
        service_type = data.get("service_type")

        if service_type == "Ambulance" and not filters.get(CONF_FILTER_AMBULANCE, True):
            return False
        if service_type == "Fire Department" and not filters.get(CONF_FILTER_FIRE, True):
            return False
        if service_type == "Police" and not filters.get(CONF_FILTER_POLICE, True):
            return False
        # Handle 'Other' category - matches if CONF_FILTER_OTHER is true and type isn't handled above
        if service_type not in ["Ambulance", "Fire Department", "Police"] and \
            not filters.get(CONF_FILTER_OTHER, True):
            return False

        return True # Matches if no filter rules applied or if the type is allowed


    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        latest_data = self.coordinator.data
        self._message_matches_filter = self._matches_filters(latest_data)

        if self._message_matches_filter:
            # If current message matches filter, store it as previous for next time
            self._previous_data = latest_data
        # If it doesn't match, _previous_data remains unchanged, holding the last matching message

        # Always update HA state to reflect changes (even if only attributes like last_update_attempt change)
        self.async_write_ha_state()


class P2000DiagnosticSensor(Alarmfase1BaseEntity, SensorEntity):
    """Representation of a P2000 Diagnostic Sensor."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: Alarmfase1DataUpdateCoordinator,
        data_key: str,
        name: str,
        device_class: SensorDeviceClass | None = None
    ) -> None:
        """Initialize the diagnostic sensor."""
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_diag_{data_key}"
        # Manually set name, ignoring _attr_has_entity_name from base
        self._attr_name = f"{coordinator.config_entry.data[CONF_INSTANCE_NAME]} {name}"
        self._attr_device_class = device_class
        self._attr_has_entity_name = False # Override base

    @property
    def native_value(self) -> StateType:
        """Return the state of the diagnostic sensor."""
        if self._data_key == "last_update_status":
            return "OK" if not self.coordinator.last_update_error else "Error"
        elif self._data_key == "last_update_time":
            # This is the timestamp of the coordinator's last *successful* run
            return self.coordinator.last_update_success_timestamp
        elif self._data_key == "consecutive_errors":
            return self.coordinator.error_count
        return None # Removed the 'last_message_scraped_time' part

    # Diagnostics are always available if the coordinator exists.
    # Override base availability which depends on last_update_success
    @property
    def available(self) -> bool:
        return self.coordinator is not None