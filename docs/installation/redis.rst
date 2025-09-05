.. _installation_redis:

===================
Redis configuration
===================

.. note:: The intended audience for this documentation is DevOps engineers

.. contents:: Jump to
    :local:
    :backlinks: none

Introduction
============

`Redis`_ is an advanced key-value store and in-memory database. Open Forms uses Redis in
its architecture for distinct features:

* as a cache backend
* as message broker for asynchronous task processing (using Celery)
* as a result backend to store the outcome of the asynchronous task processing (Celery again)
* for distributed locks, required for the async task scheduling

Redis being an in-memory data store makes it susceptible to data loss in the event of
abrupt termination or power failures unless the default configuration is modified [#]_.

This section of the documentation offers solutions for a robust Redis infrastructure,
but first we need to identify the risks that need to be mitigated.

.. _Redis: https://redis.io/
.. [#] https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#redis

The table below provides a summary and the sections below elaborate on each feature.

================= ========================= =================== ==========================
Purpose           Description               Failure mode        Why it's bad
================= ========================= =================== ==========================
Cache backend     Improve performance       Data loss           Need to re-calculate results
Cache backend     Session store             Unavailability      Cannot login, cannot
                                                                start/fill out forms
Message broker    Coordinate tasks for      Data loss,          Scheduled tasks can be lost,
                  background workers        Unavailability      Cannot schedule new tasks
Result backend    Store background job      Data loss,          Submission confirmation
                  metadata and outcome      Unavailability      may not reach end user.
Distributed locks Prevent race conditions   Data loss           Identical tasks may be
                                                                scheduled multiple times
Distributed locks Prevent race conditions   Unavailability      Task doesn't get scheduled
================= ========================= =================== ==========================

Cache backend
-------------

The primary purpose of caches is improving performance by storing pre-computed results
for a set time so that re-calculation and/or re-fetching data can be avoided, which is
usually more expensive than reading from the cache.

Data loss in the cache layer is annoying, but not fatal, since it will automatically
rebuild over time when the Redis instance is available again. There may be temporary
degraded performance and users may have to log in again.

Message broker
--------------

The application schedules tasks to be executed by background workers. This stores task
metadata in Redis like which tasks and what arguments to apply for the task. Scheduled
tasks are removed when a worker executes it and confirms that the task has been
processed. Until a worker picks up the task, it only exists in Redis.

Data loss in the message broker is fatal - the scheduled task will be lost forever if
the Redis storage configuration is not tuned.

Result backend
--------------

A subset of background tasks are configured to store their result and execution progress
in the result backend. This is used to be able to poll the execution status from the
web application.

Data loss in the result backend is annoying, but not fatal. The crucial mutations applied
in tasks are persisted in the Postgres database. Error monitoring in task failures is
available via Sentry - losing tracebacks of failed tasks is not a major concern.
Additionally, we don't have complex workflows that rely on the task results to continue execution.

Distributed locks
-----------------

The following background tasks use a lock in Redis to prevent the same task from being
scheduled multiple times:

* Submission registration
* Updating the submission payment status in the registration backend
* Registering the appointment with the appointment backend

Data loss in the Redis instance that manages the lock(s) could lead to the same task
being scheduled multiple times. This is already exceptional, as the application needs to
be suffering from a race condition in the first place - the locking is a defense-in-depth
mechanism. Another failure mode is that difference processes see a different lock state,
e.g. because of replication lag.

Furthermore, the background tasks are built to be idempotent - executing a task again
after it was already completed is not supposed to produce a different result. There is
only a risk for such a situation if multiple workers are executing the same task at the
same time, creating another race condition.

Finally, if the Redis instance used for locks is not available, scheduling the task will
fail and show up in Sentry error monitoring. The tasks can be manually scheduled again,
and operations will continue as usual.

Conclusion
----------

The primary focus of attention is on the message broker for which durability is the
most important aspect. A highly available (HA) setup further increases robustness and
reduces the likelihood of tasks being dropped or lost, promoting self-healing
characteristics.

Cache backends benefit from a HA infrastructure by minimizing the risk of Redis not
being available or limiting the impact when a failure happens. Similarly, the result
backend can benefit from HA configurations.

For distributed locks, preventing data loss by tuning persistence configuration should
be sufficient.

Redis persistence
=================

By default, Redis has snapshotting enabled. This means that Redis saves the database
(DB) to disk if a certain number of write operations have been performed in a certain
period of time. Unless configured otherwise, Redis will save the DB (see the default
`redis.conf file`_ for more details):

* After 3600 seconds (an hour) if at least 1 change was performed
* After 300 seconds (5 minutes) if at least 100 changes were performed
* After 60 seconds if at least 10K changes were performed

If Redis is abruptly terminated and any changes have not been written to the DB, the
data will be lost. For Open-Forms, this means that Celery tasks that have been queued
and have not yet been picked up by a worker might be lost, locks no longer exists,
background tasks results are lost and cached data is lost.

.. warning::

    Ensure that you always have persistent volume mounts configured in container
    environments (like Kubernetes and Docker), otherwise container restarts will also
    lead to data loss, even if persistence is configured!

    The default Redis container images have a working directory of ``/data`` - you'll
    want to mount volumes there.

Enable Append Only File (`AOF`_)
--------------------------------

The Redis AOF persistence option is similar to Write Ahead Logs (WAL) in other databases.

    AOF persistence logs every write operation received by the server. These operations
    can then be replayed again at server startup, reconstructing the original dataset.
    Commands are logged using the same format as the Redis protocol itself.

    -- Redis documentation

By default, changes are persisted every second, reducing the window for data loss to
one second.

.. tip:: Enabling AOF is particularly beneficial if you're running a single instance
   without any HA configuration.

Recommended persistence mechanism
---------------------------------

The table below lists the recommended persistence mechanism.

================== ====== =============
Feature            AOF    RDB snapshots
================== ====== =============
cache                     ✅
message broker     ✅     ❌
result backend     ✅     ✅
distributed locks  ✅     ❌
================== ====== =============

Legend:

* ✅: suitable
* ❌: avoid, if possible
* blank: neutral

.. seealso:: See the `upstream <https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/>`_
   documentation for more options.

Relation to HA configurations
-----------------------------

Redis has some options for highly-available setups, which can help reduce the impact of
failures with data loss in the master(s). Ultimately, all options come down to
replication in terms of persistence robustness.

Each master node (handling writes) can be replicated by one or more replicas. Replication_
is asynchronous, but this can help reduce the data loss interval from 1-15 minutes to a
couple of seconds (depending on the replication lag). This means that data lost in the
master may have been replicated to a replica already, and recovery is possible.

`Redis Sentinel`_ relies on replication for the failover mechanism.

`Redis cluster`_ also relies on replication to be able to promote a replica to master
during failover.

It is still recommended to tune the persistence in the master and replica nodes
accordingly.

Other options
-------------

In theory, you can avoid the Redis persistence challenge entirely by using a
`different broker`_, for example RabbitMQ (see ``CELERY_BROKER_URL`` in the
:ref:`installation_environment_config`). However, this has not been tested by the Open
Forms development team and may bring other challenges.

.. _redis.conf file: https://redis.io/docs/latest/operate/oss_and_stack/management/config-file/
.. _AOF: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
.. _Replication: https://redis.io/docs/latest/operate/oss_and_stack/management/replication/
.. _Redis sentinel: https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/
.. _Redis cluster: https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/
.. _different broker: https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#configuration

Deployment strategies
=====================

You can employ one or multiple strategies to achieve a robust and performant setup.
Strategies are not mutually exclusive - you can combine ideas of one with principles of
another one.

In general, each strategy comes with a tradeoff between operational complexity and
impact in the event of failure.

Single master
--------------

The default example configuration uses a single Redis instance (example in
``docker-compose.yml``) to illustrate the machinery. At the minimum, you should
enable ``appendonly`` in such situations.

The big advantage is the simplicity of the setup - there is no Redis cluster to monitor
and manage. It is very well suited if you're deploying an Open Forms instance on a single
physical machine (VPS, VM or dedicated server), since hardware failures that would bring
down Redis will most likely also bring down the actual application and background
workers, beating the point of a HA Redis setup.

The major drawback is that you *do* have a single point of failure. In particular on
Kubernetes it is very simple to horizontally scale application and background workers
across multiple (hardware) nodes.

Run multiple Redis masters
--------------------------

Instead of sending everything to the same Redis instance, you can also opt to dedicate
a master for each individual aspect. Open Forms supports this by having separate
:ref:`environment variables <installation_environment_config>`.

This allows you to tune Redis configuration for each usage profile.

**Caches**

``CACHE_DEFAULT``
    The default cache, used for the majority of cache-related operations. E.g. a master
    with RDB snapshots.

``CACHE_AXES``
    Cache backend for brute forcing login attempts throttling. E.g. a master with RDB
    snapshots.

``CACHE_PORTALOCKER``
    Cache backend used for startup-phase locks. E.g. a master with no persistence
    configured at all.

**Message broker**

``CELERY_BROKER_URL``
    The message broker backend to use. You can also specify Redis Sentinels here. Here
    you really want an instance with AOF enabled.

**Result backend**

``CELERY_RESULT_BACKEND``
    The result backend to use. You can also specify Redis Sentinels here. E.g. a master
    or cluster with RDB snapshots.

**Distributed locks**

``CELERY_ONCE_REDIS_URL``
    Used for the distributed locks to avoid the same task being scheduled multiple
    times. By default, it falls back to ``CELERY_BROKER_URL``.

Deploy a HA-setup
-----------------

See :ref:`installation_redis_ha` below for the available options.

.. _installation_redis_ha:

High availability strategy
==========================

In highly available Redis setups you typically aim for:

* minimize downtime
* minimize data loss potential
* self-healing / automatic failover

Configuring and deploying such setups is outside of the scope of this documentation. We
do provide a reference Docker Compose setup in the repository for testing purposes - see
the ``docker`` subdirectory. On Kubernetes, we recommend using an operator to manage
your Redis cluster.

There seem to be essentially two available options:

* `Redis Sentinel`_ - a single master with one or more replicas and sentinel instances
  that monitor and manage the failover.
* `Redis cluster`_ - a multi-master solution with each master having one or more
  replicas. Data is sharded and the cluster manages failover.

More exotic setups with a proxy exposing a single entrypoint or commercial offerings by
cloud providers have not been explored.

Of the two options, Redis Sentinel is best supported and Redis Cluster has known
limitations difficulties. Open Forms therefore only officially supports Redis Sentinel.
Additionally, not all components of Open Forms have support for Sentinel.

================== ======== =======
Feature support    Sentinel Cluster
================== ======== =======
cache              ❌       ❌
message broker     ✅       ❌
result backend     ✅       ❌
distributed locks  ❌       ❌
================== ======== =======

.. note:: Sentinel support for cache may be added in the future.

Redis Sentinel
--------------

`Redis Sentinel`_ allows for automatic failover in case of a master failure and informs
clients of the failure. It is particularly suited for the message broker and result
backend use cases. When a replica is promoted to master, the sentinels will
automatically relay the new master address to Celery.

An outage at the Redis level should then not lead to service interruptions in Open Forms,
if the failover goes well.

To use Sentinel with Open Forms, you must configure a number of environment variables
correctly.

**Broker**

``CELERY_BROKER_URL``
    The sentinel protocol must be used instead of the Redis protocol. You should include
    the addresses of the sentinel instances, e.g.:

    .. code-block:: bash

       CELERY_BROKER_URL="sentinel://localhost:26379;sentinel://localhost:23680;sentinel://localhost:23681"

``REDIS_BROKER_SENTINEL_MASTER``
    Sentinels can monitor multiple masters and handle their failovers. You must specify
    the name of the ``master`` being used for the broker. Example:

    .. code-block:: bash

        REDIS_BROKER_SENTINEL_MASTER=broker

``CELERY_ONCE_REDIS_URL``
    Because this envvar defaults to the value of ``CELERY_BROKER_URL`` and sentinel is
    not supported for the distributed locks, you must set this to a fixed master instance:

    .. code-block:: bash

        CELERY_ONCE_REDIS_URL=redis://some-master-instance:6379/0

Optional environment variables are:

``REDIS_BROKER_SENTINEL_PASSWORD``
    Optional authentication password for the sentinel instances.

``REDIS_BROKER_SENTINEL_USERNAME``
    Optional authentication username for the sentinel instances.

**Result backend**

``CELERY_RESULT_BACKEND``
    The sentinel protocol must be used instead of the Redis protocol. You should include
    the addresses of the sentinel instances, e.g.:

    .. code-block:: bash

       CELERY_RESULT_BACKEND="sentinel://localhost:26379;sentinel://localhost:23680;sentinel://localhost:23681"

``REDIS_RESULT_BACKEND_SENTINEL_MASTER``
    Sentinels can monitor multiple masters and handle their failovers. You must specify
    the name of the ``master`` being used for the result backend. Example:

    .. code-block:: bash

        REDIS_RESULT_BACKEND_SENTINEL_MASTER=celeryresults

Optional environment variables are:

``REDIS_RESULT_BACKEND_SENTINEL_PASSWORD``
    Optional authentication password for the sentinel instances.

``REDIS_RESULT_BACKEND_SENTINEL_USERNAME``
    Optional authentication username for the sentinel instances.

Redis cluster
-------------

Redis cluster is currently not officially supported. Our sentiment is also that cluster
is more aimed at scaling and performance rather than being highly available.

Workarounds exist to make Celery work with Redis cluster, but ultimately they lead to
Celery workloads always being sent to the same instance in the cluster, creating a false
sense of security.

.. warning:: Some (managed) cloud offerings use cluster under the hood and may cause
   issues.

.. seealso:: Upstream references for issues/workarounds with Redis cluster:

    * https://github.com/celery/celery/issues/8276
    * https://github.com/celery/celery/issues/9436
    * https://github.com/celery/celery/issues/8968
    * https://github.com/celery/kombu/pull/1021
    * https://github.com/rcpch/national-paediatric-diabetes-audit/pull/714/files
