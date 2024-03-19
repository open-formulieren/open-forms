# Open Zaak

The `docker-compose.open-zaak.yml` compose file is available to run an instance of Open Zaak.

## docker compose

Start an instance in your local environment from the parent directory:

```bash
docker compose -f docker-compose.open-zaak.yml up -d
```

This brings up the admin at http://localhost:8003/admin/.

## Load fixtures

Before re-recording the related VCR tests, you must load some fixtures:

```bash
cat open-zaak/fixtures/open_zaak_fixtures.json | docker compose -f docker-compose.open-zaak.yml exec -T openzaak-web.local src/manage.py loaddata --format=json -
```
