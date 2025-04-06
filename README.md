# P2000 Alarmfase1 Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
This custom integration for Home Assistant allows you to scrape emergency messages from [alarmfase1.nl](https://www.alarmfase1.nl/) for a specific region and display them as sensors. It supports filtering by service type and provides geographical coordinates for map integration.

## Features

* Fetches the latest P2000 emergency messages from alarmfase1.nl.
* Configure multiple regions by adding the integration multiple times.
* Filter messages by service type (Ambulance, Fire Department, Police, Other) via the Options flow.
* Includes coordinates (latitude and longitude) for displaying incidents on a map.
* Provides diagnostic sensors for monitoring the integration's status.
* Uses Home Assistant's UI for configuration (Config Flow).

## Prerequisites

* Home Assistant instance.
* [HACS (Home Assistant Community Store)](https://hacs.xyz/) installed.

## Installation (Using HACS)

This integration is best installed via HACS. If you have HACS installed, you can add this repository as a **Custom Repository**.

1.  **Navigate to HACS:** Open Home Assistant and go to HACS in the sidebar.
2.  **Go to Integrations:** Click on "Integrations".
3.  **Add Custom Repository:** Click the three vertical dots (⋮) in the top-right corner and select "Custom repositories".
4.  **Enter Repository Details:**
    * In the "Repository" field, paste the URL of this GitHub repository:
      ```
      https://github.com/malosaaa/ha-p2000
      ```
    * In the "Category" dropdown, select **"Integration"**.
    * Click the "Add" button.
5.  **Install Integration:**
    * Close the "Custom repositories" dialog.
    * The "P2000 Alarmfase1" integration should now appear in your HACS Integrations list. Find it or search for it.
    * Click on the integration card.
    * Click the "Download" button (usually in the bottom right).
    * Confirm the download (select the version - usually the latest is recommended).
6.  **Restart Home Assistant:** After HACS finishes downloading, **you MUST restart Home Assistant** for the integration to be loaded. A prompt should appear, or you can do it manually via Developer Tools -> Server Management -> Restart.

## Configuration

Once installed via HACS and after restarting Home Assistant, you can add your desired region:

1.  **Navigate to Integrations:** Go to **Settings -> Devices & Services -> Integrations**.
2.  **Add Integration:** Click the "+ Add Integration" button (usually in the bottom right).
3.  **Search:** Search for "P2000 Alarmfase1" and click on it.
4.  **Enter Region Path:** You will be prompted to enter the **Region Path** for your area. You can find this on the [alarmfase1.nl](https://www.alarmfase1.nl/) website (e.g., `limburg-zuid/maastricht/`).
5.  **Enter Instance Name:** You will also be asked to provide an **Instance Name** (e.g., `maastricht`). This name will be used in the entity IDs (e.g., `sensor.p2000_alarmfase1_maastricht_latest_message`). Click Submit.
6.  **Done!** The integration will be set up for that region, and sensor entities will be created.
7.  **Add More Regions:** To monitor another region, simply repeat steps 2-6.

**Reconfiguring Options:**

You can change the scan interval, enabled sensors, and filters after setup:

1.  Go to **Settings -> Devices & Services -> Integrations**.
2.  Find the "P2000 Alarmfase1" integration entry corresponding to the instance name you want to change.
3.  Click the "CONFIGURE" button on that entry.
4.  Adjust the options as needed and click Submit. Home Assistant will reload the integration with the new settings.

## Available Entities

This integration creates the following entities for each configured region (instance):

* **`sensor.p2000_alarmfase1_<instance_name>_latest_message`**: This sensor provides the priority code of the latest matching emergency message. Its attributes contain detailed information:
    * `priority_code`
    * `datetime` (of the message)
    * `region`
    * `location`
    * `street`
    * `description` (full message text)
    * `latitude`
    * `longitude`
    * `service_type` (e.g., Ambulance, Fire Department, Police)
    * `matches_filter` (indicates if the latest scrape matches the configured filters)
    * `last_update_attempt` (timestamp of the last update attempt)
    * ... (other scraped data based on your options)

* **Diagnostic Sensors:**
    * `sensor.p2000_alarmfase1_<instance_name>_last_update_status`: Shows "OK" or "Error" for the last update.
    * `sensor.p2000_alarmfase1_<instance_name>_coordinator_last_update`: Timestamp of the last successful data fetch.
    * `sensor.p2000_alarmfase1_<instance_name>_consecutive_update_errors`: Number of consecutive update errors.

*(Replace `<instance_name>` with the name you provided during configuration, e.g., `maastricht`)*

## Map Integration

The main sensor provides `latitude` and `longitude` attributes, allowing you to display emergency incidents on a Home Assistant map card. The icon of the map marker will dynamically change based on the `service_type` of the message (e.g., ambulance icon, fire truck icon, police car icon).

## Options

The following options can be configured for each instance of the integration:

* **Scan Interval:** How often to check for new messages (in seconds).
* **Enabled Sensors:** Select which details from the scraped message should be included as attributes of the main sensor.
* **Filters:** Enable or disable filtering for specific service types (Ambulance, Fire Department, Police, Other).

## Troubleshooting

* **Integration not found in HACS:** Ensure you have added your repository as a custom repository in HACS settings and restarted Home Assistant after installation.
* **"Config flow could not be loaded":** Double-check the installation steps and restart Home Assistant. Review your Home Assistant logs for detailed error messages.
* **No entities created after configuration:** Check your Home Assistant logs for any errors related to the `p2000_alarmfase1` integration. Ensure the region path you entered is correct.
* **Sensor shows "Unavailable":** This might happen briefly after a restart. If it persists, check the diagnostic sensors and your Home Assistant logs for any update errors.
* **Map icons not showing:** Ensure the main sensor has valid `latitude` and `longitude` attributes and that the `service_type` is being correctly identified in the attributes.

If you encounter issues, please check the existing issues on GitHub first, and if your problem isn't listed, feel free to open a new issue here:
[https://github.com/malosaaa/ha-p2000/issues](https://github.com/malosaaa/ha-p2000/issues) 

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests to your GitHub repository.

## License

This project is licensed under the [Apache License 2.0](LICENSE).  

## Disclaimer

* This integration scrapes data from [alarmfase1.nl](https://www.alarmfase1.nl/). The developer of this integration is **not responsible** for the scraping process or any changes to the website that may break the integration.
* Users of this integration are solely responsible for their use and must **respect the terms of service of the alarmfase1.nl website.
* It is highly recommended to use a **reasonable and high scan interval** to avoid overloading the alarmfase1.nl website with excessive requests. You are responsible for configuring the scan interval appropriately.
* This integration is provided **"as is" for educational and personal use only**. The developer assumes no responsibility for any damages or issues arising from the use or misuse of this integration.
* This integration is not affiliated with or endorsed by alarmfase1.nl.

---

---
