## Example configuration.yaml

```yaml
# Example configuration.yaml entry

n3rgy:
  name: 'Consumption Data'
  api_key: !secret api_key
  host: !secret host_url
  property_id: !secret property_id

```

## Configuration options

| Parameter | Optional | Description |
|:--------- | -------- | ----------- |
| `name` | Yes | Sensor name |
| `host` | No | The server URL used to call the SDK methods |
| `api_key` | No | The API key used for authentication with the server |
| `property_id` | No | The Property ID, which can be either an MPAN or MPRN |
