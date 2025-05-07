# Generic JSON registration plugin

The `docker-compose.generic-json.yml` compose file is available to run a mock service intended
to simulate a receiving server to test the Generic JSON registration plugin. It contains an
endpoint for sending JSON data (`json_plugin`) and testing the connection (`test_connection`).

The `json_plugin` endpoint returns a confirmation message that the data was received, together with the
received data. The `test_connection` endpoint just returns an 'OK' message.

## docker compose

Start an instance in your local environment from the parent directory:

```bash
docker compose -f docker-compose.generic-json.yml up -d
```

This starts a flask application at http://localhost:80/ with the endpoints `json_plugin` and `test_connection`.
