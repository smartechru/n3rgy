# Smart Energy Data

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub](https://img.shields.io/github/license/smartechru/n3rgy)](LICENSE)

[![GitHub Release (latest by date)](https://img.shields.io/github/v/release/smartechru/n3rgy)](https://github.com/smartechru/n3rgy/releases)
![GitHub Release Date](https://img.shields.io/github/release-date/smartechru/n3rgy)

[![Maintenance](https://img.shields.io/badge/Maintained%3F-Yes-brightgreen.svg)](https://github.com/smartechru/n3rgy/graphs/commit-activity)
[![GitHub Issues](https://img.shields.io/github/issues/smartechru/n3rgy)](https://github.com/smartechru/n3rgy/issues)

The `n3rgy` component is a Home Assistant custom sensor which provides access to historic energy consumption data and tariff information.

## TABLE OF CONTENTS

* [Installation](#installation)
  * [Manual Installation](#manual-installation)
  * [Installation via HACS](#installation-via-hacs)
* [Configuration](#configuration)
  * [Config Flow](#config-flow)
  * [Configuration Parameters](#configuration-parameters)
* [State](#state)

## INSTALLATION

### MANUAL INSTALLATION

1. Download the `n3rgy.zip` file from the [latest release](https://github.com/smartechru/n3rgy/releases/latest).
2. Unpack the release and copy the `custom_components/n3rgy` directory into the `custom_components` directory of your Home Assistant installation.
3. Configure the `n3rgy` sensor.
4. Restart Home Assistant.

### INSTALLATION VIA HACS

1. Ensure that [HACS](https://custom-components.github.io/hacs/) is installed.
2. Search for and install the "n3rgy" integration.
3. Configure the `n3rgy` sensor.
4. Restart Home Assistant.

## CONFIGURATION

`n3rgy` can be configured on the integrations menu or in configuration.yaml

### CONFIG FLOW

In Configuration/Integrations click on the + button, select "n3rgy" and configure the options on the form.

### configuration.yaml

Add `n3rgy` sensor in your `configuration.yaml`.

```yaml
# Example configuration.yaml entry

n3rgy:
  name: 'Consumption Data'
  api_key: !secret api_key
  host: !secret host_url
  property_id: !secret property_id

```

### CONFIGURATION PARAMETERS

| Parameter | Optional | Description |
|:--------- | -------- | ----------- |
| `name` | Yes | Sensor name |
| `host` | No | The server URL used to call the SDK methods |
| `api_key` | No | The API key used for authentication with the server |
| `property_id` | No | The Property ID, which can be either an MPAN or MPRN |


## STATE

Returns values for the consumption of the specified utility (e.g. electricity, gas) at the property identified by the given MPxN. Unless otherwise specified using optional parameters, returns the consumption values for every half-hour of the previous day. Accepts as optional parameters a start date/time, an end date/time, and granularity (either halfhourly or daily).
