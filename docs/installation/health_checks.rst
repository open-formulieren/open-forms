.. _installation_health_checks:

=======================
Container health checks
=======================

Open Forms is deployed as a collection of containers. Containers can be checked if
they're running as expected, and actions can be taken by the container runtime or
container orchestration (like Kubernetes and Docker) when that's not the case, like
restarting the container or removing it from the pool that serves traffic.

Health checks are responsible for detecting anomalies and reporting that a container is
not running as expected. They can take different forms, for example:

* running a script and checking the exit code of the process
* making an HTTP request to an endpoint which responds with a success or error status
  code
* opening a TCP connection to a particular port

This section of the documentation describes the recommended health checks to use that
are provided in Open Forms, or the health checks to implement in containers of third
party software typically used in an Open Forms deployment. You can incorporate these in
your infrastructure code (like Helm charts).

You can find code examples of these health checks in our `docker-compose.yml`_ on Github.

.. _docker-compose.yml: https://github.com/open-formulieren/open-forms/blob/main/docker-compose.yml

Open Forms containers
=====================

HTTP service
------------

The Open Forms web service listens on port 8000 inside the container and accepts HTTP
traffic. Three endpoints are exposed for health checks.

``http://localhost:8000/_healthz/livez/``
    The liveness endpoint - checks that HTTP requests can be handled. Suitable for
    liveness (and readiness) probes. This is the check with lowest overhead.

``http://localhost:8000/_healthz/``
    Endpoint that checks connections with database, caches, database migration state...

    Suitable for the startup probe. The most expensive check to run, as it checks all
    dependencies of the application.

``http://localhost:8000/_healthz/readyz/``
    The readiness endpoint - checks that requests can be handled and tests that the
    default cache (used by for sessions) and database connection function. Slightly
    more expensive than the liveness check, but it's a good candidate for the readiness
    probe.

.. tip:: Ensure the ``ALLOWED_HOSTS`` environment variable contains ``localhost``. See
    :ref:`installation_environment_config` for more details.

.. tip:: The executable ``maykin-common`` is available in the container which can be
   used to perform the health checks, as an alternative to HTTP probes.

   .. code-block:: bash

        maykin-common health-check
            --endpoint=http://localhost:8000/_healthz/livez/ \
            --timeout=3

.. versionadded:: 3.5.0

Celery workers
--------------

.. todo:: TODO

Celery beat
-----------

.. todo:: TODO

Celery flower
-------------

.. todo:: TODO

Third party containers
======================

Redis/Valkey
------------

The Redis and Valkey container images include a command line utility - ``redis-cli`` and
``valkey-cli`` which has a ``ping`` command to test connectivity to the server:

.. code-block:: bash

    redis-cli ping

The command exits with exit code ``0`` on success and exit code ``1`` on failure.

nginx
-----

nginx proxies HTTP traffic from the browser/client to the backend service. It also
serves static assets directly. The nginx config needs to be extended with a location
handler for the health checks. You should take care to namespace this so that you don't
get collissions with identifiers of forms that would be masked by this path.

Example nginx configuration snippet:

.. code-block:: nginx

    location = /_healthz/livez/ {
        access_log off;
        add_header Content-Type text/plain;
        # block outside traffic
        allow 127.0.0.1;
        allow ::1;
        deny all;
        return 200 "ok\n";
    }

We recommend this cheap check for both the liveness and readiness checks.

You can then wire up an HTTP probe or ``curl`` script to make a ``GET`` call to
``http://localhost:8080/_healthz/livez/``. Note the port number - often the nginx
unprivileged image will be used, which binds to 8080 by default, but check your
specific environment to confirm.

**Smart readiness probe**

You *may* want to consider proxying to the backend-service for the readiness check.

.. warning:: This can lead to cascading failures where first your backend-service
   becomes unavailable, which leads to nginx becoming unavailable and possible other
   dependent services.

.. tip:: Even if the backend is not available, nginx may still be performing useful work
   by serving static files.

Example nginx configuration snippet:

.. code-block:: nginx

    location = /_healthz/readyz/ {
        access_log off;
        # block outside traffic
        allow 127.0.0.1;
        allow ::1;
        deny all;

        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_set_header X-Scheme $scheme;
        proxy_pass   http://web:8000/_health/readyz/;
    }

ClamAV
------

ClamAV includes a healthcheck definition in its container image. On Kubernetes, these
are not used, instead probes are used.

The health check is implemented in ``clamdcheck.sh``, exiting with a non-zero exit code
when there are problems. It pings the default port (3310).

.. note:: On initial deploy, ClamAV will have to download the virus definitions database,
   which can take a long time. The built-in healthcheck only starts after 6 minutes.
   It's recommended to configure a startup probe on Kubernetes.

PostgreSQL
----------

.. warning:: Running the database as a container can bring certain scaling and disaster
   recovery challenges. We only provide this check for completeness sake.

PostgreSQL container images typically include the ``pg_isready`` binary, which tests
the database connection (accepting traffic on the specified host and port). It has a
non-zero exit code when the database is not ready.
