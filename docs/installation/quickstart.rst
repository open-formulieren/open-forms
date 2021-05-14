.. _quickstart:

=======================
Quickstart installation
=======================

A ``docker-compose-quickstart.yml`` file is available to get the app up and 
running in minutes. It contains 'convenience' settings, which means that no 
additional configuration is needed to run the app. Therefore, it should *not* 
be used for anything else than testing. For example, it includes:

* A default ``SECRET_KEY`` environment variable
* A predefined database with the environment variable 
  ``POSTGRES_HOST_AUTH_METHOD=trust``. This lets us connect to the database 
  without using a password.
* Debug mode is enabled.

Getting started with Docker
---------------------------

1. Download the ``docker-compose`` file:

   .. tabs::

      .. group-tab:: Linux

         .. code:: shell

            $ wget https://raw.githubusercontent.com/open-formulieren/open-forms/master/docker-compose-quickstart.yml -O docker-compose.yml

      .. group-tab:: Windows (Powershell 3)

         .. code:: shell

            PS> wget https://raw.githubusercontent.com/open-formulieren/open-forms/master/docker-compose-quickstart.yml -Odocker-compose.yml

2. Start the docker containers with ``docker-compose``. If you want to run the containers in the background, add the ``-d`` flag to the command below.

    .. code:: shell

        $ docker-compose up

3. Create a super-user.

    .. code:: shell

        $ docker-compose exec web src/manage.py createsuperuser

4. Navigate to ``http://127.0.0.1:8000`` and use the credentials created above
   to log in.
