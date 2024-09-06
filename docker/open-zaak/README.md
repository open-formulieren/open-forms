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

## Dump fixtures

Whenever you make changes in the admin for the tests, you need to dump the fixtures again so that
bringing up the containers the next time (or in other developers' environments) will still have the
same data.

Dump the fixtures with (in the `docker` directory):

```bash
docker compose -f docker-compose.open-zaak.yml run openzaak-web.local \
    python src/manage.py dumpdata \
        --indent=4 \
        --output /app/fixtures/open_zaak_fixtures.json \
        authorizations.applicatie \
        vng_api_common.jwtsecret \
        config.featureflags \
        catalogi
```

Depending on your OS, you may need to grant extra write permissions:

```bash
chmod o+rwx ./open-zaak/fixtures
```
