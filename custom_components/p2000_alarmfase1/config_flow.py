"""Config flow for P2000 Scraper."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    Alarmfase1ApiClient,
    ScraperApiConnectionError,
    ScraperApiNoDataError,
    ScraperApiParsingError,
    ScraperApiError,
)
from .const import (
    DOMAIN,
    CONF_REGION_PATH,
    CONF_INSTANCE_NAME,
    CONF_SENSORS,
    CONF_FILTERS,
    SENSOR_SCHEMA,
    FILTER_SCHEMA,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# Schema for user input step
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_INSTANCE_NAME): str,
    vol.Required(CONF_REGION_PATH): str,
})


async def validate_input(hass, region_path: str) -> None:
    """Validate the user input allows us to connect and parse."""
    session = async_get_clientsession(hass)
    client = Alarmfase1ApiClient(session)
    # Perform a test scrape - raises exceptions on failure
    await client.async_scrape_data(region_path)


class P2000ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for P2000 Scraper."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            # Use region_path as unique ID for config entry to prevent duplicates
            unique_id = user_input[CONF_REGION_PATH].strip('/')
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            try:
                _LOGGER.info("Validating P2000 region path: %s", user_input[CONF_REGION_PATH])
                await validate_input(self.hass, user_input[CONF_REGION_PATH])
            except ScraperApiConnectionError:
                errors["base"] = "cannot_connect"
            except ScraperApiNoDataError:
                errors[CONF_REGION_PATH] = "invalid_region_path" # Specific error for 404 etc.
            except ScraperApiParsingError:
                errors["base"] = "parse_error" # Website structure might have changed
            except ScraperApiError:
                errors["base"] = "unknown_api_error"
            except Exception as e: # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during validation: %s", e)
                errors["base"] = "unknown"
            else:
                # Input validated, create entry with data, proceed to options flow
                # Store user input in data, options will be set in next step
                return self.async_create_entry(
                    title=user_input[CONF_INSTANCE_NAME], # Use user's name for title
                    data=user_input,
                    # Proceed to options flow by returning empty dict for options here
                    options={}
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    # Add Options Flow Handler for initial and subsequent configuration
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return P2000OptionsFlowHandler(config_entry)


class P2000OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for P2000 Scraper."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        # Load current options or provide defaults
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> config_entries.FlowResult:
        """Manage the main options step (sensor selection)."""
        if user_input is not None:
            # Store sensor selections from this step
            self.options[CONF_SENSORS] = user_input
            # Proceed to the next step (filter selection)
            return await self.async_step_filters()

        # Show form for sensor selection, pre-filled with current options
        # Use SENSOR_SCHEMA which has defaults built-in
        schema = self.add_suggested_values_to_schema(
            SENSOR_SCHEMA, self.options.get(CONF_SENSORS)
        )
        return self.async_show_form(step_id="init", data_schema=schema)


    async def async_step_filters(self, user_input: Optional[Dict[str, Any]] = None) -> config_entries.FlowResult:
        """Manage the filter selection step."""
        if user_input is not None:
            # Store filter selections and proceed to the scan interval step
            self.options[CONF_FILTERS] = user_input
            return await self.async_step_interval()

        # Show form for filter selection
        schema = self.add_suggested_values_to_schema(
            FILTER_SCHEMA, self.options.get(CONF_FILTERS)
        )
        return self.async_show_form(step_id="filters", data_schema=schema)

    async def async_step_interval(self, user_input: Optional[Dict[str, Any]] = None) -> config_entries.FlowResult:
        """Manage the scan interval setting."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            if not isinstance(scan_interval, int) or scan_interval < MIN_SCAN_INTERVAL:
                errors[CONF_SCAN_INTERVAL] = "interval_too_short"
            else:
                self.options[CONF_SCAN_INTERVAL] = scan_interval
                _LOGGER.debug("Updating options for %s: %s", self.config_entry.entry_id, self.options)
                # Create the entry with the combined options
                return self.async_create_entry(title="", data=self.options)

        # Show form for scan interval
        schema = vol.Schema({
            vol.Optional(CONF_SCAN_INTERVAL, default=self.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): int,
        })
        return self.async_show_form(step_id="interval", data_schema=schema, errors=errors)