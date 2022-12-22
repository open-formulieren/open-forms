.. _installation_redis:

===================
Redis configuration
===================

To prevent Celery tasks to be lost in the case where Redis crashes, it it advisable to run Redis with `AOF`_
(Append Only File) persistence enabled.

This is because Redis by default runs with snapshotting enabled.
This means that Redis saves the DB to disk if a certain number of write operations have been performed in a certain
period of time. By default, Redis will save the DB (see the default `redis.conf file`_ for more details):

* After 3600 seconds (an hour) if at least 1 change was performed
* After 300 seconds (5 minutes) if at least 100 changes were performed
* After 60 seconds if at least 10000 changes were performed

In Open Forms, Redis is used by Celery as both the broker and the results backend. If Redis crashes (for example because
it runs out of memory), all tasks that were queued and not picked up by a worker would be lost if no persistence is
enabled. This means that submissions might not be processed and sent to the registration backend.


.. _AOF: https://redis.io/docs/management/persistence/
.. _redis.conf file: https://redis.io/docs/management/config-file/
