"""API Client for scraping P2000 messages from alarmfase1.nl."""
import asyncio
import logging
import socket
from datetime import datetime
import locale # For parsing Dutch date/time strings

import async_timeout
from aiohttp import ClientError, ClientSession
from bs4 import BeautifulSoup

from .const import BASE_URL, API_TIMEOUT, SERVICE_TYPE_ICON_MAP, DEFAULT_SERVICE_TYPE

_LOGGER = logging.getLogger(__name__)

# --- Datetime Parsing Setup ---
# Attempt to set locale for Dutch month/day names. This might fail if locale not installed.
# A more robust solution might involve external libraries or manual mapping if this fails.
DUTCH_LOCALE = "nl_NL.UTF-8" # Common locale string for Dutch
try:
    locale.setlocale(locale.LC_TIME, DUTCH_LOCALE)
    _LOGGER.debug("Successfully set locale to %s for date parsing", DUTCH_LOCALE)
except locale.Error:
    _LOGGER.warning(
        "Could not set locale to %s for parsing Dutch dates/times. Parsing might fail.",
        DUTCH_LOCALE
    )
    # Fallback or manual parsing might be needed here
# Define the expected format from the 'title' attribute
# Example: "zondag 6 april 2025 14:55:01"
# %A = Full weekday name (locale-dependent)
# %d = Day of the month as a zero-padded decimal number.
# %B = Full month name (locale-dependent)
# %Y = Year with century as a decimal number.
# %H = Hour (24-hour clock) as a zero-padded decimal number.
# %M = Minute as a zero-padded decimal number.
# %S = Second as a zero-padded decimal number.
EXPECTED_DATETIME_FORMAT = "%A %d %B %Y %H:%M:%S"
# --- End Datetime Setup ---


class ScraperApiError(Exception):
    """Generic Scraper API Error."""

class ScraperApiConnectionError(ScraperApiError):
    """Scraper API Connection Error."""

class ScraperApiParsingError(ScraperApiError):
    """Scraper API Parsing Error (e.g., website structure changed)."""

class ScraperApiNoDataError(ScraperApiError):
    """Scraper API No Data Error (e.g., invalid region path or no messages)."""


class Alarmfase1ApiClient:
    """Scraper API Client."""

    def __init__(self, session: ClientSession):
        """Initialize the API client."""
        self._session = session
        self._base_url = BASE_URL

    def _parse_timestamp(self, timestamp_str: str | None) -> datetime | None:
        """Attempt to parse the Dutch timestamp string."""
        if not timestamp_str:
            return None
        try:
            # Use locale-dependent parsing
            return datetime.strptime(timestamp_str, EXPECTED_DATETIME_FORMAT)
        except ValueError as e:
            _LOGGER.warning("Failed to parse timestamp string '%s' with format '%s': %s",
                            timestamp_str, EXPECTED_DATETIME_FORMAT, e)
            return None
        except NameError:
            _LOGGER.warning("Could not parse timestamp string '%s' due to potential locale issues.", timestamp_str)
            return None


    def _infer_service_type(self, icon_tag: BeautifulSoup | None, priority_text: str | None, message_text: str | None) -> str:
        """Infer service type from the icon's class attribute and text content."""
        if not icon_tag or not icon_tag.has_attr('class'):
            # Try to infer from text if no icon
            if priority_text:
                if "Politie" in priority_text:
                    return "Police"
                if "Ambulance" in priority_text:
                    return "Ambulance"
                if "Brandweer" in priority_text:
                    return "Fire Department"
            if message_text:
                if "politie" in message_text.lower():
                    return "Police"
                if "ambulance" in message_text.lower():
                    return "Ambulance"
                if "brandweer" in message_text.lower():
                    return "Fire Department"
            return DEFAULT_SERVICE_TYPE

        icon_classes = icon_tag['class'] # Returns a list of classes
        for class_fragment, service_type in SERVICE_TYPE_ICON_MAP.items():
            # Check if any class contains the fragment (e.g., 'fa-ambulance' contains 'ambulance')
            if any(class_fragment in cls for cls in icon_classes):
                return service_type

        # If no icon match, try to infer from text as a fallback
        if priority_text:
            if "Politie" in priority_text:
                return "Police"
            if "Ambulance" in priority_text:
                return "Ambulance"
            if "Brandweer" in priority_text:
                return "Fire Department"
        if message_text:
            if "politie" in message_text.lower():
                return "Police"
            if "ambulance" in message_text.lower():
                return "Ambulance"
            if "brandweer" in message_text.lower():
                return "Fire Department"

        return DEFAULT_SERVICE_TYPE


    async def async_scrape_data(self, region_path: str) -> dict | None:
        """Fetch and parse P2000 data for a given region path."""
        url = f"{self._base_url}{region_path.strip('/')}/" # Ensure trailing slash
        _LOGGER.debug("Requesting P2000 data from: %s", url)
        headers = {"User-Agent": "HomeAssistant P2000_Alarmfase1 Integration"} # Be a good citizen

        try:
            async with async_timeout.timeout(API_TIMEOUT):
                response = await self._session.get(url, headers=headers)
                # Allow 404 as it might mean an invalid region path
                if response.status == 404:
                    _LOGGER.warning("Received 404 for %s, likely invalid region path.", url)
                    raise ScraperApiNoDataError(f"Invalid region path (404): {region_path}")
                response.raise_for_status() # Raise HTTPError for other bad responses (e.g., 5xx)
                html_content = await response.text()

        except asyncio.TimeoutError as exc:
            _LOGGER.error("Timeout occurred while requesting P2000 data for %s", region_path)
            raise ScraperApiConnectionError(f"Timeout connecting to {url}") from exc
        except (ClientError, socket.gaierror) as exc:
            _LOGGER.error("Communication error occurred while requesting P2000 data for %s: %s", region_path, exc)
            raise ScraperApiConnectionError(f"Communication error with {url}") from exc

        _LOGGER.debug("Parsing HTML content from %s", url)
        try:
            soup = BeautifulSoup(html_content, 'lxml') # Use lxml for speed
            latest_call_div = soup.select_one("#calls .call")

            if not latest_call_div:
                _LOGGER.warning("Could not find the latest call div ('#calls .call') on %s", url)
                # This could mean no calls listed, or structure changed
                # Return None or empty dict? Let's return None to signal potential issue
                return None # Or raise ScraperApiNoDataError("No message div found")

            data = {}

            # --- Extract individual fields with error checking ---
            def get_text(element):
                return element.text.strip() if element else None

            def get_attr(element, attr):
                return element.get(attr) if element else None

            # Priority Code
            prio_element = latest_call_div.select_one("h2 > a > b")
            data["priority_code"] = get_text(prio_element)

            # Message
            msg_element = latest_call_div.select_one("pre")
            data["message"] = get_text(msg_element)

            # Time (Absolute and Raw)
            time_span = latest_call_div.select_one("h2 > span")
            data["raw_time_str"] = get_text(time_span) # e.g., "xx minuten geleden"
            data["absolute_time_str"] = get_attr(time_span, 'title') # e.g., "zondag 6 april..."
            data["time"] = self._parse_timestamp(data["absolute_time_str"])

            # Location Info (nested within spans/paragraphs - adjust selectors if needed)
            loc_p = latest_call_div.select_one("span > p:nth-child(2)") # Parent paragraph
            if loc_p:
                # City
                city_element = loc_p.select_one("a:nth-child(2) > span")
                data["city"] = get_text(city_element)
                # Address
                addr_element = loc_p.select_one("span") # The span containing street?
                data["address"] = get_text(addr_element)
                # Postal Code
                post_element = loc_p.select_one("a:nth-child(3) > span")
                data["postalcode"] = get_text(post_element)
            else:
                data["city"] = None
                data["address"] = None
                data["postalcode"] = None

            # Lat/Lon
            try:
                data["latitude"] = float(get_attr(latest_call_div, 'latitude')) if get_attr(latest_call_div, 'latitude') else None
            except (ValueError, TypeError):
                data["latitude"] = None
            try:
                data["longitude"] = float(get_attr(latest_call_div, 'longitude')) if get_attr(latest_call_div, 'longitude') else None
            except (ValueError, TypeError):
                data["longitude"] = None

            # Service Type
            icon_element = latest_call_div.select_one("h2 > a > i")
            data["service_type"] = self._infer_service_type(icon_element, data.get("priority_code"), data.get("message"))

            _LOGGER.debug("Successfully parsed data for %s: %s", region_path, data)
            return data

        except Exception as exc:
            _LOGGER.exception("Error parsing P2000 data for %s: %s", region_path, exc)
            raise ScraperApiParsingError(f"Failed to parse HTML from {url}") from exc