## CONFIGURATION

**n3rgy** can be configured on the integrations menu or in configuration.yaml

### Config flow

In Configuration/Integrations click on the **<+>** button, select **n3rgy** and configure the options on the form.

### Example configuration.yaml

Add **n3rgy** sensor in your `configuration.yaml`.

```yaml
# Example configuration.yaml entry

n3rgy:
  name: 'Consumption Data'
  host: !secret host_url
  api_key: !secret api_key
  property_id: !secret property_id

```

Optional arguments:

```yaml
n3rgy:
  name: 'Consumption Data'
  ...
  environment: true    # live environment enabled
  start: 202102080130  # start date/time (FORMAT: YYYYMMDDHHmm)
  end: 202102091125    # end date/time (FORMAT: YYYYMMDDHHmm)

```

### CONFIGURATION PARAMETERS

| Parameter | Optional | Description |
|:--------- | -------- | ----------- |
| `name` | Yes | Sensor name |
| `host` | No | The server URL used to call the SDK methods |
| `api_key` | No | The API key used for authentication with the server |
| `property_id` | No | The Property ID, which can be either an MPAN or MPRN |
| `environment` | Yes | Live environment flag (default: `false`) |
| `start` | Yes | Start date/time of the period in the format YYYYMMDDHHmm |
| `end` | Yes | End date/time of the period in the format YYYYMMDDHHmm |
