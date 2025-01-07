# Referentielijsten API

The `docker-compose.referentielijsten.yml` compose file is available to run an instance of Referentielijsten API.

## docker compose

Start an instance in your local environment from the parent directory:

```bash
docker compose -f docker-compose.referentielijsten.yml up -d
```

This brings up the admin at http://localhost:8004/admin/. You can log in with the `admin` / `admin`
credentials.

## Load fixtures

The fixtures in `referentielijsten/fixtures` are automatically loaded when the Referentielijsten container starts.

## Dump fixtures

Whenever you make changes in the admin for the tests, you need to dump the fixtures again so that
bringing up the containers the next time (or in other developers' environments) will still have the
same data.

Dump the fixtures with (in the `docker` directory):

```bash
docker compose -f docker-compose.referentielijsten.yml run referentielijsten-web.local \
    python src/manage.py dumpdata \
        --indent=4 \
        --output /app/fixtures/referentielijsten_fixtures.json \
        accounts \
        api
```

Depending on your OS, you may need to grant extra write permissions:

```bash
chmod o+rwx ./referentielijsten/fixtures
```
