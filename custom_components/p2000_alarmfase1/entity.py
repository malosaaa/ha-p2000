"""Base entity for P2000 Scraper."""
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, CONF_INSTANCE_NAME
from .coordinator import Alarmfase1DataUpdateCoordinator


class Alarmfase1BaseEntity(CoordinatorEntity[Alarmfase1DataUpdateCoordinator]):
    """Base class for P2000 Scraper entities."""

    _attr_has_entity_name = True # Use automatic naming based on device and entity name

    def __init__(self, coordinator: Alarmfase1DataUpdateCoordinator) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        # Use the instance name from config entry for device identification
        self._instance_name = coordinator.config_entry.data[CONF_INSTANCE_NAME]
        self._region_path = coordinator.region_path

        # Link entities for this configured instance to one device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)}, # Use config entry ID for uniqueness
            name=self._instance_name, # User-friendly name from config
            manufacturer=MANUFACTURER,
            model=f"Region: {self._region_path}",
            entry_type=None,
            configuration_url=f"https://www.alarmfase1.nl/{self._region_path.strip('/')}/",
        )

    @property
    def available(self) -> bool:
        """Return True if coordinator is available and has successfully updated."""
        # Data can be None if no messages found, but coordinator might still be available
        return self.coordinator.last_update_success