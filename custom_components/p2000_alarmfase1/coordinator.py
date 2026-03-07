"""DataUpdateCoordinator for P2000 Scraper."""
import logging
from datetime import timedelta, datetime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import Alarmfase1ApiClient, ScraperApiError, ScraperApiNoDataError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class Alarmfase1DataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching P2000 data."""

    def __init__(self, hass, name, client, region_path, update_interval, cache=None, initial_data=None):
        self.client = client
        self.region_path = region_path
        self.cache = cache
        
        # Prime the coordinator with cached data
        self.data = initial_data
        self.last_data = initial_data
        
        self._error_count = 0
        self._last_update_error = False
        self.last_update_success_timestamp = datetime.now().isoformat() if initial_data else None

        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from alarmfase1.nl."""
        try:
            data = await self.client.async_scrape_data(self.region_path)
            
            if data:
                self.last_data = data
                self.last_update_success_timestamp = datetime.now().isoformat()
                self._error_count = 0
                self._last_update_error = False
                
                # Save to disk cache
                if self.cache:
                    await self.cache.save(data)
                
                return data
            
            return self.last_data

        except ScraperApiNoDataError:
            _LOGGER.debug("No new messages for %s", self.region_path)
            return self.last_data

        except Exception as err:
            self._error_count += 1
            self._last_update_error = True
            _LOGGER.warning("Update failed for %s, using last known data: %s", self.region_path, err)
            
            if self.last_data:
                return self.last_data
            raise UpdateFailed(f"Error fetching P2000 data: {err}")

    @property
    def error_count(self) -> int:
        return self._error_count

    @property
    def last_update_error(self) -> bool:
        return self._last_update_error
