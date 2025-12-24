.. _installation_docker_compose:

============================
Install using Docker Compose
============================

This installation is meant for people who want to just try out Open Forms on 
their own machine.

A `Docker Compose`_ file is available to get the app up and running in minutes.
It contains 'convenience' settings, which means that no additional 
configuration is needed to run the app. Therefore, it should **not** be used 
for anything other than testing. For example, it includes:

* A default ``SECRET_KEY`` environment variable
* A predefined database with the environment variable 
  ``POSTGRES_HOST_AUTH_METHOD=trust``. This lets us connect to the database 
  without using a password.
* Debug mode is enabled.

.. _`WSL`: https://docs.microsoft.com/en-us/windows/wsl/

Prerequisites
=============

You will only need Docker tooling and nothing more:

* `Docker Engine`_ (Desktop or Server)
* `Docker Compose`_ (sometimes comes bundled with Docker Engine)

.. _`Docker Engine`: https://docs.docker.com/engine/install/
.. _`Docker Compose`: https://docs.docker.com/compose/install/


Getting started
===============

1. Download the project as ZIP-file:

   .. code:: bash

      $ wget https://github.com/open-formulieren/open-forms/archive/refs/heads/main.zip -O
      $ unzip main.zip
      $ cd open-forms-main

2. Start the docker containers with ``docker compose``. If you want to run the
   containers in the background, add the ``-d`` option to the command below:

   .. code:: bash

      docker compose up

      Creating network "open-forms-main_default" with the default driver
      Creating volume "open-forms-main_db" with default driver
      Creating volume "open-forms-main_private_media" with default driver
      Creating open-forms-main_db_1 ... done
      Creating open-forms-main_redis_1 ... done
      Creating open-forms-main_sdk_1 ... done
      Creating open-forms-main_web_1 ... done
      Creating open-forms-main_nginx_1 ... done
      Creating open-forms-main_celery_1 ... done
      Creating open-forms-main_celery-beat_1 ... done
      Creating open-forms-main_celery-flower_1 ... done
      ...

3. Create a super-user.

   .. code:: bash

      docker compose exec web src/manage.py createsuperuser

4. Navigate to ``http://127.0.0.1:8000/admin/`` and use the credentials created 
   above to log in.

5. To stop the containers, press *CTRL-C* or if you used the ``-d`` option:

   .. code:: bash

      docker compose stop

6. If you want to get newer versions, you need to ``pull`` because the 
   ``docker-compose.yml`` contains no explicit versions:

   .. code:: bash

      $ docker compose pull
