# Objects APIs

The `docker-compose.objects-apis.yml` compose file is available to run an instance of the Objects and Objecttypes API.

## docker compose

Start an instance in your local environment from the parent directory:

```bash
docker compose -f docker-compose.objects-apis.yml up -d
```

Create a superuser:

```bash
docker compose -f docker-compose.objects-apis.yml exec objecttypes-web src/manage.py createsuperuser
docker compose -f docker-compose.objects-apis.yml exec objects-web src/manage.py createsuperuser
```

This brings up:
- Objecttypes (admin interface is accessible at http://localhost:8001/admin/).
- Objects (admin interface is accessible at http://localhost:8002/admin/).

## Load fixtures

Before re-recording the related VCR tests, you must load some fixtures:

```bash
cat objects-apis/fixtures/objecttypes_api_fixtures.json | docker compose -f docker-compose.objects-apis.yml exec -T objecttypes-web src/manage.py loaddata --format=json -
cat objects-apis/fixtures/objects_api_fixtures.json | docker compose -f docker-compose.objects-apis.yml exec -T objects-web src/manage.py loaddata --format=json -
```
