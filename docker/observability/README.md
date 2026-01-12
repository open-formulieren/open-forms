# Observability stack

The config files in this directory go together with `docker-compose.observability.yml` and provide a
reference for a potential observability stack.

**Disclaimer**

The chosen vendors/technologies here merely serve as an example - it's simply a stack we're somewhat
comfortable with. Open Forms itself is vendor agnostic and the principles demonstrated apply to
competing vendors too.

## Bringing up the services

From the root of the repository:

```bash
docker compose up -d
docker compose -f docker/docker-compose.observability.yml up
```

You can now navigate to:

- http://localhost:3000 for Grafana
- http://localhost:3100/ready for Loki readiness
- http://localhost:3100/metrics for Loki metrics
- http://localhost:9090 for the Prometheus web interface

## Logging

For log scraping, parsing and querying we've set up Promtail as scraper, Loki as storage and Grafana
as visualization tool.

### Sample queries

In the Grafana menu, navigate to "Explore" to create ad-hoc queries.

**Web service logs**

```logql
{job="docker", app="openforms"} | json | __error__ = ""
```

This ignores logs that cannot be parsed as JSON (such as container/server startup logs).

**Logs for a single request**

You can filter application logs based on a request ID:

```logql
{job="docker", app="openforms"} | json | __error__ = "" | request_id=`1e9e1b9d-4d34-4657-99e4-88673d824724`
```

## Metrics

Metrics can be sent using OTLP to the collector at http://localhost:4317 (gRPC).

The `maykin_common.otel` module takes care of setting everything up, just make sure to set the
environment variable `OTEL_SDK_DISABLED=false` in development (it's disabled by default).

The collector ingests the metrics, and they are then scraped by Prometheus. They're also printend to
stdout.

## Traces

Traces can be sent using OTLP to the collector at http://localhost:4317 (gRPC).

The `maykin_common.otel` module takes care of setting everything up, just make sure to set the
environment variable `OTEL_SDK_DISABLED=false` in development (it's disabled by default).

The collector ingests the traces and they are then exported to Grafana Tempo. They're also
printed to stdout.
