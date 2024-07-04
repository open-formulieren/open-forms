# Open Zaak

The `docker-compose.open-zaak.yml` compose file is available to run an instance of Open Zaak.

## docker compose

Start an instance in your local environment from the parent directory:

```bash
docker compose -f docker-compose.open-zaak.yml up -d
```

This brings up the admin at http://localhost:8003/admin/. You can log in with the `admin` / `admin`
credentials.

## Load fixtures

The fixtures in `open-zaak/fixtures` are automatically loaded when the Open Zaak container starts.
