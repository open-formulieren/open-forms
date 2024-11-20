# RX Mission

The `docker-compose.rx-mission.yml` compose file is available to run a mock services intended
to replicate some Roxit interfaces. Currently only containing a mock product detail endpoint.

The compose file takes some serious creative liberty, and doesn't represent a real Roxit environment.
At the moment we cannot use a real Roxit products environment,
so this mock service shall have to do for the development and testing of #4796.

The data returned from `/product/<product_uuid>` is a stripped example provided by Roxit,
and very loosely depicts real products.

When development of the Roxit products environment is completed, this docker environment must be updated.

## docker compose

Start an instance in your local environment from the parent directory:

```bash
docker compose -f docker-compose.rx-mission.yml up -d
```

This starts a flask application at http://localhost:80/product/<product_uuid>.
To recognized `uuid's` can be found in the `rx-mission/fixtures/rx-mission-products.json` file.

## Load fixtures

The flask app uses the fixtures in `rx-mission/fixtures` as a simple database.
