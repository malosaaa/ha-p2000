"""API Client for scraping P2000 messages from alarmfase1.nl."""
import asyncio
import logging
import socket
import os
from datetime import datetime

import async_timeout
from aiohttp import ClientError, ClientSession
from bs4 import BeautifulSoup

from .const import BASE_URL, API_TIMEOUT, DEFAULT_SERVICE_TYPE

_LOGGER = logging.getLogger(__name__)

class ScraperApiError(Exception): pass
class ScraperApiConnectionError(ScraperApiError): pass
class ScraperApiParsingError(ScraperApiError): pass
class ScraperApiNoDataError(ScraperApiError): pass

class Alarmfase1ApiClient:
    """Scraper API Client."""

    def __init__(self, session: ClientSession):
        self._session = session
        self._base_url = BASE_URL
        self._local_dir = os.path.dirname(__file__)

    async def async_scrape_data(self, region_path: str) -> dict | None:
        url = f"{self._base_url}{region_path.strip('/')}/"
        headers = {"User-Agent": "HomeAssistant P2000_Alarmfase1 Integration"}
        
        try:
            async with async_timeout.timeout(API_TIMEOUT):
                response = await self._session.get(url, headers=headers)
                if response.status == 404:
                    raise ScraperApiNoDataError(f"Invalid region path (404): {region_path}")
                response.raise_for_status()
                html_content = await response.text()

                debug_path = os.path.join(self._local_dir, "p2000_debug.txt")
                try:
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                except Exception:
                    pass

        except Exception as exc:
            raise ScraperApiConnectionError(f"Connection error with {url}") from exc

        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Find the latest call block
            latest_call_div = soup.select_one("#calls .call") or soup.find("div", class_="call")
            if not latest_call_div:
                return None

            data = {}

            # 1. Main Title (Your original code used this for 'priority_code')
            title_tag = latest_call_div.find("b", itemprop="name")
            data["priority_code"] = title_tag.text.strip() if title_tag else "Geen titel"

            # 2. Raw Message Text
            msg_tag = latest_call_div.find("pre")
            data["message"] = msg_tag.text.strip() if msg_tag else "Geen bericht"

            # 3. Time Parsing (Using the new HTML ISO format)
            time_span = latest_call_div.find("span", itemprop="startDate")
            if time_span:
                data["raw_time_str"] = time_span.text.strip()
                iso_str = time_span.get("content")
                data["absolute_time_str"] = iso_str
                if iso_str:
                    try:
                        # Parse "2026-03-06T13:40"
                        parsed_dt = datetime.fromisoformat(iso_str)
                        # Split into clean time and date formats
                        data["time"] = parsed_dt.strftime("%H:%M")
                        data["date"] = parsed_dt.strftime("%Y-%m-%d")
                    except ValueError:
                        data["time"] = data["raw_time_str"]
                        data["date"] = "Onbekend"
            else:
                data["raw_time_str"] = None
                data["absolute_time_str"] = None
                data["time"] = "Onbekend"
                data["date"] = "Onbekend"

            # 4. Location Details (Directly from itemprop tags)
            city_tag = latest_call_div.find(itemprop="addressLocality")
            data["city"] = city_tag.text.strip() if city_tag else "Onbekend"

            postal_tag = latest_call_div.find(itemprop="postalCode")
            data["postalcode"] = postal_tag.text.strip() if postal_tag else "Geen postcode beschikbaar"

            street_tag = latest_call_div.find(itemprop="streetAddress")
            data["address"] = street_tag.text.strip() if street_tag else "Onbekend"

            # 5. Coordinates
            try:
                data["latitude"] = float(latest_call_div.get('latitude'))
            except (ValueError, TypeError):
                data["latitude"] = None
            try:
                data["longitude"] = float(latest_call_div.get('longitude'))
            except (ValueError, TypeError):
                data["longitude"] = None

            # 6. Service Type (Directly from the div attribute)
            data["service_type"] = latest_call_div.get("service", DEFAULT_SERVICE_TYPE)

            return data

        except Exception as exc:
            raise ScraperApiParsingError(f"Failed to parse HTML from {url}") from exc
