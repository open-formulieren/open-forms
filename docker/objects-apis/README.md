# Open object API

The `docker-compose.objects-apis.yml` compose file is available to run an instance of Open Object
which provides API endpoints for objects and object types.

## docker compose

Start an instance in your local environment from the parent directory:

```bash
docker compose -f docker-compose.objects-apis.yml up -d
```

This brings up:

- Objects and Objecttypes (admin interface is accessible at http://localhost:8001/admin/).

You can log in with the `admin` / `admin` credentials.

## Load fixtures

The fixtures in `objects-apis/fixtures` are automatically loaded when the containers start.

## Dump fixtures

Whenever you make changes in the admin for the tests, you need to dump the fixtures again so that
bringing up the containers the next time (or in other developers' environments) will still have the
same data.

Dump the fixtures with (in the `docker` directory):

**Object types**

```bash
docker compose -f docker-compose.objects-apis.yml run open-object-web \
    python src/manage.py dumpdata \
        --indent=4 \
        --output /app/fixtures/001_objecttypes_api_fixtures.json \
        core.objecttype \
        core.objecttypeversion
```

**Objects**

```bash
docker compose -f docker-compose.objects-apis.yml run open-object-web \
    python src/manage.py dumpdata \
        --indent=4 \
        --output /app/fixtures/002_objects_api_fixtures.json \
        core.object \
        token \
        zgw_consumers
```

Depending on your OS, you may need to grant extra write permissions:

```bash
chmod -R o+rwx ./objects-apis/fixtures
```
