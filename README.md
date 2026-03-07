# P2000 Alarmfase1 Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)][hacs]
[![Project Maintenance][maintenance_badge]](https://github.com/Malosaaa/ha-p2000)


This custom integration for Home Assistant allows you to scrape emergency messages from [alarmfase1.nl](https://www.alarmfase1.nl/) for a specific region and display them as sensors. It supports filtering by service type and provides geographical coordinates for map integration.
<br>


## Features
* ✅ **L1-Style Persistence**: Includes a built-in cache system.
* ✅ **Blaxing fast startup and entity control**: Assistant reboots—no more "Unknown" states on startup.
* ✅ **Latest live data**: Fetches the latest P2000 emergency messages from alarmfase1.nl.
* ✅ **Multiple regions**: Configure multiple regions by adding the integration multiple times.
* ✅ **Filter**: Filter messages by service type (Ambulance, Fire Department, Police, Other) via the Options flow.
* ✅ **Coordinates**: Includes coordinates (latitude and longitude) for displaying incidents on a map.
* ✅ **Diagnostics**: Provides diagnostic sensors for monitoring the integration's status.
* ✅ **Service Calls**: Includes services to manually trigger a refresh or clear the local cache via Developer Tools.
* ✅ **Cool animated card**: Very cool animated dashboard card that matches the emergency.

## 🛠 Services

| Service | Description |
| :--- | :--- |
| `p2000.manual_refresh` | Forces an immediate scrape of the website. |
| `p2000.clear_cache` | Deletes the local `.storage` cache file. |
| `p2000.clear_debugfile` | Deletes the local `debugfile`. |

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
    * `date` (of the message)
    * `time` (of the message)
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
    * `sensor.p2000_alarmfase1_<instance_name>_last_update`: Shows "OK" or "Error" for the last update.
    * `sensor.p2000_alarmfase1_<instance_name>_status`: Timestamp of the last successful data fetch

*(Replace `<instance_name>` with the name you provided during configuration, e.g., `maastricht`)*

## Map Integration

The main sensor provides `latitude` and `longitude` attributes, allowing you to display emergency incidents on a Home Assistant map card. The icon of the map marker will dynamically change based on the `service_type` of the message (e.g., ambulance icon, fire truck icon, police car icon).

## 🎨 Recommended Dashboard (Mushroom)

To get the look seen in the screenshots, you will need **[Mushroom Cards](https://github.com/piitaya/lovelace-mushroom)** and **[Card Mod](https://github.com/thomasloven/lovelace-card-mod)** (both available in HACS). 

*Note: Replace `yourplace` in the entity IDs below with your actual instance name.*

```yaml
type: custom:mushroom-legacy-template-card
entity: sensor.p2000_alarmfase1_yourplace_latest_message
fill_container: true
multiline_secondary: true
primary: "{{ states('sensor.p2000_alarmfase1_yourplace_latest_message') }}"
secondary: |
  📅 {{ state_attr(entity, 'date') }} | 🕒 {{ state_attr(entity, 'time') }}
  📍 {{ state_attr(entity, 'address') }}, {{ state_attr(entity, 'postalcode') }}
  💬 {{ state_attr(entity, 'message') }}
icon: >-
  {%- if 'Ambulance' in state_attr(entity, 'service_type') -%} mdi:ambulance {%-
  elif 'Politie' in state_attr(entity, 'service_type') -%} mdi:police-badge {%-
  elif 'Brandweer' in state_attr(entity, 'service_type') -%} mdi:fire-truck {%-
  elif 'Trauma' in state_attr(entity, 'service_type') -%} mdi:helicopter {%-
  else -%} mdi:alert-decagram {%- endif -%}
icon_color: >-
  {%- if 'Ambulance' in state_attr(entity, 'service_type') -%} yellow {%- elif
  'Politie' in state_attr(entity, 'service_type') -%} blue {%- elif 'Brandweer'
  in state_attr(entity, 'service_type') -%} red {%- elif 'Trauma' in
  state_attr(entity, 'service_type') -%} orange {%- else -%} grey {%- endif -%}
tap_action:
  action: url
  url_path: >-
    {% set lat = state_attr(entity, 'latitude') %} {% set lon =
    state_attr(entity, 'longitude') %} {% if lat and lon %}
    https://www.google.com/maps/search/?api=1&query={{ lat }},{{ lon }} {% else
    %} # {% endif %}
card_mod:
  style:
    mushroom-shape-icon$: |
      .shape {
        position: relative;
        overflow: visible !important;
        
        /* 1. Define the dynamic color for the spray and fog */
        {% if 'Ambulance' in state_attr(config.entity, 'service_type') %} --irrig-color: var(--rgb-yellow);
        {% elif 'Politie' in state_attr(config.entity, 'service_type') %} --irrig-color: var(--rgb-blue);
        {% elif 'Brandweer' in state_attr(config.entity, 'service_type') %} --irrig-color: var(--rgb-red);
        {% else %} --irrig-color: var(--rgb-grey);
        {% endif %}

        /* 2. Trigger the animations if alert is active */
        {% if '1' in states(config.entity) or 'Politie' in states(config.entity) %}
          --shape-animation: irrig-ultra 2s ease-in-out infinite;
          --irrig-heads-animation: irrig-heads 1.6s ease-out infinite;
          --irrig-fog-animation: irrig-fog 2s ease-in-out infinite;
          opacity: 1;
        {% else %}
          --shape-animation: none;
          --irrig-heads-animation: none;
          --irrig-fog-animation: none;
          opacity: 0.75;
        {% endif %}

        /* 3. Apply the jumping animation to the shape itself */
        animation: var(--shape-animation);
      }

      .shape::before,
      .shape::after {
        content: '';
        position: absolute;
        border-radius: inherit;
        inset: 0;
        pointer-events: none;
      }

      .shape::before {
        animation: var(--irrig-heads-animation);
      }

      .shape::after {
        animation: var(--irrig-fog-animation);
      }

      @keyframes irrig-ultra {
        0%   { transform: translateY(0) scale(1); }
        25%  { transform: translateY(-2px) scale(1.02); }
        50%  { transform: translateY(-4px) scale(1.03); }
        75%  { transform: translateY(-2px) scale(1.02); }
        100% { transform: translateY(0) scale(1); }
      }

      @keyframes irrig-heads {
        0% {
          box-shadow:
            -10px 10px 0 0 rgba(var(--irrig-color), 0),
            0 10px 0 0 rgba(var(--irrig-color), 0),
            10px 10px 0 0 rgba(var(--irrig-color), 0);
        }
        20% {
          box-shadow:
            -10px 4px 0 0 rgba(var(--irrig-color), 0.9),
            0 10px 0 0 rgba(var(--irrig-color), 0),
            10px 10px 0 0 rgba(var(--irrig-color), 0);
        }
        40% {
          box-shadow:
            -10px -2px 0 0 rgba(var(--irrig-color), 0.4),
            0 4px 0 0 rgba(var(--irrig-color), 0.9),
            10px 10px 0 0 rgba(var(--irrig-color), 0);
        }
        100% {
          box-shadow:
            -10px 10px 0 0 rgba(var(--irrig-color), 0),
            0 10px 0 0 rgba(var(--irrig-color), 0),
            10px 10px 0 0 rgba(var(--irrig-color), 0);
        }
      }

      @keyframes irrig-fog {
        50% {
          filter: blur(0.7px);
          box-shadow: 0 -14px 18px -8px rgba(var(--irrig-color), 0.45);
        }
      }
    .: |
      mushroom-shape-icon {
          --icon-size: 65px;
          display: flex;
          margin: -55px 0 10px -20px !important;
          padding-right: 10px;
        }
      ha-card {
        clip-path: inset(0 0 0 0 round var(--ha-card-border-radius, 12px));
        {% if '1' in states(config.entity) or 'Politie' in states(config.entity) %}
          {% set s = state_attr(config.entity, 'service_type') %}
          {% if 'Ambulance' in s %} background: rgba(var(--rgb-yellow), 0.1) !important;
          {% elif 'Politie' in s %} background: rgba(var(--rgb-blue), 0.1) !important;
          {% elif 'Brandweer' in s %} background: rgba(var(--rgb-red), 0.1) !important;
          {% else %} background: rgba(var(--rgb-red), 0.1) !important;
          {% endif %}
        {% endif %}
      }
grid_options:
  columns: 48
  rows: 2

```

[hacs]: https://hacs.xyz
[hacs_badge]: https://img.shields.io/badge/HACS-Custom
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
[hacs]: https://hacs.xyz
[hacs_badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[maintenance_badge]: https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge
