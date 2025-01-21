.. _installation_redis:

===================
Redis configuration
===================

.. note:: The intended audience for this documentation is DevOps engineers

In Open-Forms, `Redis`_ is used as cache, as message broker (for Celery) and as a backend for Celery to store the results
of the tasks.

Redis is an in-memory data-store, which means that it is susceptible to data loss in the event of abrupt termination or
power failures unless the default configuration is modified [#]_.

.. _Redis: https://redis.io/
.. [#] https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#redis

Configuring Redis as robust message broker
==========================================

By default, Redis runs with snapshotting enabled.
This means that Redis saves the DB (database) to disk if a certain number of write operations have been performed in a
certain period of time. By default, Redis will save the DB (see the default `redis.conf file`_ for more details):

* After 3600 seconds (an hour) if at least 1 change was performed
* After 300 seconds (5 minutes) if at least 100 changes were performed
* After 60 seconds if at least 10000 changes were performed

.. _redis.conf file: https://redis.io/docs/latest/operate/oss_and_stack/management/config-file/

If Redis is abruptly terminated and any changes have not been written to the DB, the data will be lost. For Open-Forms,
this means that Celery tasks that have been queued and have not yet been picked up by a worker might be lost.

The easiest workaround for this problem is to enable `AOF`_ (Append Only File) persistence in Redis. From the Redis
documentation:


    AOF persistence logs every write operation received by the server. These operations can then be replayed again at
    server startup, reconstructing the original dataset. Commands are logged using the same format as the Redis protocol
    itself.

By default, changes are persisted every second. This means that the window for data loss is reduced to 1 s.

Other (more complex) solutions are also possible, but out-of-scope for this documentation. For example:

* Run HA (High Availability) with `Redis sentinel`_.
* Run a `Redis cluster`_ instead of a single node.
* Run Redis with `replication`_.
* Run Celery with a `different broker`_, for example RabbitMQ (see ``CELERY_BROKER_URL``
  in the :ref:`installation_environment_config`).


.. _Redis sentinel: https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/
.. _AOF: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
.. _Redis cluster: https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/
.. _replication: https://redis.io/docs/latest/operate/oss_and_stack/management/replication/
.. _different broker: https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#configuration

Deploying multiple Redis instances
==================================

By default, Open-Forms uses a single Redis instance that is shared for cache, Celery message broker and Celery backend
for storing results.

By adding AOF persistence for the message broker, it is possible that the performance of the cache or results
backend degrades. This may be because the cache/results backend may lead to many writes to the append-only file.

If you observe this problem, you may consider deploying a Redis instance for each individual use case (cache,
message broker, results backend). These can be configured through the environment variables
``CACHE_<suffix>``, ``CELERY_BROKER_URL`` and ``CELERY_RESULT_BACKEND`` (see :ref:`installation_environment_config`
for more details on these environment variables). Using this strategy, different Redis configuration files can be
used for each instance to tune them for the intended usage:

* cache: default snapshotting is okay, cache data loss is not an issue
* message broker: AOF-configuration recommended
* result store: AOF-configuration recommended
