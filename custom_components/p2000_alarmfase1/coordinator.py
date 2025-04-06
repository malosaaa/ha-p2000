"""DataUpdateCoordinator for P2000 Scraper."""
import logging
from datetime import timedelta, datetime

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import Alarmfase1ApiClient, ScraperApiError, ScraperApiNoDataError
from .const import DOMAIN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class Alarmfase1DataUpdateCoordinator(DataUpdateCoordinator[dict | None]):
    """Class to manage fetching P2000 data."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        client: Alarmfase1ApiClient,
        region_path: str,
        update_interval: timedelta,
    ):
        """Initialize the coordinator."""
        self.client = client
        self.region_path = region_path
        self._error_count = 0
        self._last_update_error = False
        self.last_update_success_timestamp = None
        self.last_data = None  # Initialize variable to store the last successful data

        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )

    @property
    def error_count(self) -> int:
        """Return the number of consecutive errors."""
        return self._error_count

    @property
    def last_update_error(self) -> bool:
        """Return if the last update resulted in an error."""
        return self._last_update_error

    async def _async_update_data(self) -> dict | None:
        """Fetch data from API endpoint."""
        _LOGGER.debug("Fetching P2000 data for %s", self.region_path)
        try:
            # Returns dict on success, None if no message div found
            data = await self.client.async_scrape_data(self.region_path)

            if data is not None:
                self.last_update_success_timestamp = dt_util.now()
                if data == self.last_data:
                    _LOGGER.debug("Data has not changed since last update for %s", self.region_path)
                    return self.last_data  # Return the old data to signal no update

                self.last_data = data  # Store the new data
            elif self.last_data is not None:
                _LOGGER.debug("No data found, keeping last known data for %s", self.region_path)
                return self.last_data # Keep the last known data if no new data is found

            self._error_count = 0
            self._last_update_error = False
            return data
        except ScraperApiNoDataError:
            # Valid scenario if region has no messages, don't treat as failure
            _LOGGER.debug("No data/message found for %s, likely no current messages.", self.region_path)
            self._error_count = 0
            self._last_update_error = False
            if self.last_data is not None:
                return self.last_data # Keep the last known data
            return None # Or return None if there was no previous data
        except ScraperApiError as err:
            self._error_count += 1
            self._last_update_error = True
            _LOGGER.error("Error communicating with/parsing alarmfase1.nl for %s: %s", self.region_path, err)
            # Raise UpdateFailed so entities know update failed
            raise UpdateFailed(f"Error fetching/parsing data: {err}") from err