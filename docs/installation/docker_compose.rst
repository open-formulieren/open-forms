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

1. Create a folder to store everything in:

   .. code:: bash

      $ mkdir open-forms
      $ cd open-forms

2. Download the ``docker-compose.yml`` file:

   .. code:: bash

      $ wget https://raw.githubusercontent.com/open-formulieren/open-forms/master/docker-compose.yml

3. Start the docker containers with ``docker-compose``. If you want to run the 
   containers in the background, add the ``-d`` option to the command below.

   .. code:: bash

      $ docker-compose up

      Creating open-forms_db_1 ... done
      Creating open-forms_redis_1 ... done
      Creating open-forms_sdk_1 ... done
      Creating open-forms_web_1 ... done
      Creating open-forms_nginx_1 ... done
      Creating open-forms_celery_1 ... done
      Creating open-forms_celery-beat_1 ... done
      Creating open-forms_celery-flower_1 ... done
      ...

4. Create a super-user.

   .. code:: bash

      $ docker-compose exec web src/manage.py createsuperuser

5. Navigate to ``http://127.0.0.1:8000/admin/`` and use the credentials created 
   above to log in.
