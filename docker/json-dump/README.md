# JSON dump registration plugin

The `docker-compose.json-dump.yml` compose file is available to run a mock service intended
to simulate a receiving server to test the JSON dump registration backend plugin. It contains an
endpoint for sending json data (`json_plugin`) and testing the connection (`test_connection`).

The `json_plugin` endpoint returns a confirmation message that the data was received, together with the
received data. The `test_connection` endpoint just returns an 'OK' message.

## docker compose

Start an instance in your local environment from the parent directory:

```bash
docker compose -f docker-compose.json-dump.yml up -d
```

This starts a flask application at http://localhost:80/ with the endpoints `json_plugin` and `test_connection`.
