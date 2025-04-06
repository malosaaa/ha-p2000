"""Diagnostics support for P2000 Scraper."""
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, DIAG_CONFIG_ENTRY, DIAG_OPTIONS, DIAG_COORDINATOR_DATA
from .coordinator import Alarmfase1DataUpdateCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: Alarmfase1DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    last_data = coordinator.data

    # Ensure datetime objects are converted to strings for JSON serialization
    if last_data and isinstance(last_data.get("time"), datetime):
        last_data = last_data.copy() # Avoid modifying coordinator's data
        last_data["time"] = last_data["time"].isoformat()

    diagnostics_data = {
        DIAG_CONFIG_ENTRY: {
             "entry_id": entry.entry_id,
             "title": entry.title,
             "data": dict(entry.data),
             "options": dict(entry.options),
             "unique_id": entry.unique_id,
        },
        DIAG_OPTIONS: dict(entry.options),
        DIAG_COORDINATOR_DATA: {
            "region_path": coordinator.region_path,
            "last_update_success": coordinator.last_update_success,
            "last_update_error": coordinator.last_update_error,
            "last_update_timestamp": coordinator.last_update_success_timestamp.isoformat() if coordinator.last_update_success_timestamp else None,
            "update_interval": coordinator.update_interval.total_seconds() if coordinator.update_interval else None,
            "consecutive_errors": coordinator.error_count,
            "data": last_data, # Include the last fetched data (with serialized datetime)
        }
    }

    return diagnostics_data