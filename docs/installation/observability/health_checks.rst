.. _installation_observability_health_checks:

=============
Health checks
=============

Health checks are implemented/used in order to monitor the status of a service/container.
This is the information we get next to the relevant container's status and it can be ``healthy``,
``health: starting`` or ``unhealthy``. 

We try to have this kind of check for every service either inside the docker compose yml
file or in a separate script if this is necessary. Depending on the type of the service
we implement a "health check" in a different way. The following checks are available and
their status is visible by running:

.. code-block:: docker

       docker ps

- Celery
    - worker
        We are essentially implementing readiness and liveness probes for Celery workers using
        filesystem-based heartbeat and readiness files (/app/bin/check_celery_worker_liveness.py).
    - beat
        We are doing almost the same thing for Celery beat using filesystem-based heartbeat 
        files (/app/bin/check_celery_beat_liveness.py).
    - flower
        This check is made inside the docker compose yml file where we make a simple request
        to the default port.
- Redis
    The check here is done by using redis-cli (already part of the library's installation).
- Nginx
    This is done in the Nginx level where we define a separate endpoint for this along with
    the restrictions for accessing it (all the external access is denied).
- Django application (backend API)
    This is done by a separate endpoint (/api/v2/health) which just returns a HttpResponse
    with the status 204.
- ClamAV
    This is already part of th default image we use. The clamav:1.0.0 image itself defines
    a health check via HEALTHCHECK in its Dockerfile. This is happening by sending a ping
    to clamd on the default port (3310).