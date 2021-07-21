.. _installation_environment_config:

===================================
Environment configuration reference
===================================

Open Forms can be ran both as a Docker container or directly on a VPS or
dedicated server. It depends on other services, such as database and cache
backends, which can be configured through environment variables.

Available environment variables
===============================

Required settings
-----------------

* ``DJANGO_SETTINGS_MODULE``: which environment settings to use. Available options:

  - ``openforms.conf.docker``
  - ``openforms.conf.dev``
  - ``openforms.conf.ci``

* ``SECRET_KEY``: secret key that's used for certain cryptographic utilities. You
  should generate one via
  `miniwebtool <https://www.miniwebtool.com/django-secret-key-generator/>`_

* ``ALLOWED_HOSTS``: A comma separated (without spaces!) list of domains that
  serve the installation. Used to protect against ``Host`` header attacks.
  Defaults to ``*`` for the ``docker`` environment and defaults to
  ``127.0.0.1,localhost`` for the ``dev`` environment.

Common settings
---------------

* ``DB_HOST``: Hostname of the PostgreSQL database. Defaults to ``db`` for the
  ``docker`` environment, otherwise defaults to ``localhost``.

* ``DB_USER``: Username of the database user. Defaults to ``openforms``,

* ``DB_PASSWORD``: Password of the database user. Defaults to ``openforms``,

* ``DB_NAME``: Name of the PostgreSQL database. Defaults to ``openforms``,

* ``DB_PORT``: Port number of the database. Defaults to ``5432``.

* ``CELERY_BROKER_URL``: URL for the Redis task broker for Celery. Defaults
  to ``redis://127.0.0.1:6379/1``.

* ``CELERY_RESULT_BACKEND``: URL for the Redis result broker for Celery.
  Defaults to ``redis://127.0.0.1:6379/1``.

* ``SDK_BASE_URL``: URL for the retrieving Open Forms SDK files.
  Defaults to ``https://open-forms.test.maykin.opengem.nl/sdk``.

Email settings
--------------

* ``EMAIL_HOST``: Email server host. Defaults to ``localhost``.

* ``EMAIL_PORT``: Email server port. Defaults to ``25``.

* ``EMAIL_HOST_USER``: Email server username. Defaults to ``""``.

* ``EMAIL_HOST_PASSWORD``: Email server password. Defaults to ``""``.

* ``EMAIL_USE_TLS``: Indicates whether the email server uses TLS. Defaults to
  ``False``.

* ``DEFAULT_FROM_EMAIL``: The email address to use a default sender. Defaults
  to ``openforms@example.com``.

Cross-Origin Resource Sharing (CORS) settings
---------------------------------------------

See: https://github.com/adamchainz/django-cors-headers

* ``CORS_ALLOW_ALL_ORIGINS``: If ``True``, all origins will be allowed. Other
  settings restricting allowed origins will be ignored.Defaults to ``False``.

* ``CORS_ALLOWED_ORIGINS``: A list of origins that are authorized to make
  cross-site HTTP requests. Defaults to ``[]``.

* ``CORS_ALLOWED_ORIGIN_REGEXES``: A list of strings representing regexes that
  match Origins that are authorized to make cross-site HTTP requests. Defaults
  to ``[]``.

* ``CORS_EXTRA_ALLOW_HEADERS``: The list of non-standard HTTP headers that can
  be used when making the actual request. These headers are added to the
  internal setting ``CORS_ALLOW_HEADERS``. Defaults to ``[]``.

Log settings
------------

* ``SENTRY_DSN``: URL of the sentry project to send error reports to. Defaults
  to an empty string (ie. no monitoring). See `Sentry settings`_.

* ``ELASTIC_APM_SERVER_URL``: Server URL of Elastic APM. Defaults to
  ``None``. If not set, Elastic APM will be disabled by setting internal
  setting ``ELASTIC_APM["ENABLED"]`` to ``False`` and
  ``ELASTIC_APM["SERVER_URL"]`` to ``http://localhost:8200``. See
  `Elastic settings`_.

* ``ELASTIC_APM_SECRET_TOKEN``: Token for Elastic APM. Defaults to ``default``.
  See `Elastic settings`_.

* ``LOG_STD_OUT``: Write all log entries to ``stdout`` instead of log files.
  Defaults to ``True`` when using Docker and otherwise ``False``.

.. _`Sentry settings`: https://docs.sentry.io/
.. _`Elastic settings`: https://www.elastic.co/guide/en/apm/agent/python/current/configuration.html

DigiD/EHerkenning settings
--------------------------

* ``SSL_CERTIFICATE_PATH``: Path to the TLS/SSL certificate on the server.
* ``SSL_KEY_PATH``: Path to the TLS/SSL key on the server.
* ``BASE_URL``: Base url on which open-forms is deployed.
* ``DIGID_METADATA``: This is the path to the metadata file provided by the Identity Provider.
* ``DIGID_SERVICE_ENTITY_ID``: The URL where the Identity Provider serves its metadata.
* ``DIGID_SERVICE_NAME_NL``: The name (in Dutch) of the Service Provider.
* ``DIGID_SERVICE_NAME_EN``: The name (in English) of the Service Provider.
* ``EHERKENNING_METADATA``: Path to the metadata file provided by the Identity Provider.
* ``EHERKENNING_SERVICE_ENTITY_ID``: Value that matches the ``entityID`` attribute in the ``md:EntityDescriptor`` tag of the Identity Provider metadata.
* ``EHERKENNING_ENTITY_ID``: It has the format ``urn:etoegang:DV:<OIN>:entities:<index>``. More information can be found `here <https://afsprakenstelsel.etoegang.nl/display/as/EntityID>`__.
* ``EHERKENNING_LOA``: LOA stands for 'Level Of Assurance'. The possible values can be found `here <https://afsprakenstelsel.etoegang.nl/display/as/Level+of+assurance>`__. Defaults to ``"urn:etoegang:core:assurance-class:loa3"``.
* ``EHERKENNING_OIN``: The OIN for the organisation. There is a OIN `catalogue <https://portaal.digikoppeling.nl/registers/>`_ that can be used to search for OINs.
* ``EHERKENNING_MAKELAAR_ID``: The OIN of the broker.
* ``EHERKENNING_PRIVACY_POLICY``: The URL for the privacy policy page.
* ``EHERKENNING_SERVICE_NAME_NL``: The Dutch name of the service that requires EHerkenning authentication.
* ``EHERKENNING_SERVICE_NAME_EN``: The English name of the service that requires EHerkenning authentication.
* ``EHERKENNING_SERVICE_DESCRIPTION_NL``: The description (in Dutch) of the service that requires EHerkenning authentication.
* ``EHERKENNING_SERVICE_DESCRIPTION_EN``: The description (in English) of the service that requires EHerkenning authentication.
* ``EHERKENNING_ORGANISATION_NAME_NL``: The Dutch name of the organisation that provides the service that requires EHerkenning authentication.
* ``EHERKENNING_ORGANISATION_NAME_EN``: The English name of the organisation that provides the service that requires EHerkenning authentication.

Other settings
--------------

* ``DEBUG``: Used for more traceback information on development environment.
  Various other security settings are derived from this setting! Defaults to
  ``True`` for the ``dev`` environment, otherwise defaults to ``False``.

* ``IS_HTTPS``: Used to construct absolute URLs and controls a variety of
  security settings. Defaults to the inverse of ``DEBUG``.

* ``DB_ENGINE``: Backend to use as database system. See
  `Django DATABASE settings`_ for a full list of backends. Only the default is
  supported but others might work. Defaults to ``django.db.backends.postgresql``

* ``CACHE_DEFAULT``: The default Redis cache location. Defaults to
  ``localhost:6379/0``.

* ``CACHE_AXES``: The Redis cache location for Axes (used to prevent brute
  force attacks). Defaults to ``localhost:6379/0``.

* ``ENVIRONMENT``: Short string to indicate the environment (test, production,
  etc.) Defaults to ``""``.

* ``GIT_SHA``: The Git commit hash belonging to the code running the instance.
  Defaults to the automatically determined commit hash, if the application is
  run from a checked out Git repository.

* ``VERSION_TAG``: The version of the application. If not provided, the
  ``GIT_SHA`` is used.

* ``EXTRA_VERIFY_CERTS``: a comma-separated list of paths to certificates to trust, empty
  by default. If you're using self-signed certificates for the services that Open Forms
  communicates with, specify the path to those (root) certificates here, rather than
  disabling SSL certificate verification. Example:
  ``EXTRA_VERIFY_CERTS=/etc/ssl/root1.crt,/etc/ssl/root2.crt``.

* ``CURL_CA_BUNDLE``: if this variable is set to an empty string, it disables SSL/TLS
  certificate verification. More information about why can be found on this
  `stackoverflow post <https://stackoverflow.com/a/48391751/7146757>`_. Even calls from
  Open Forms to any other service will be disabled, so this variable should be used with
  care to prevent unwanted side-effects.

.. _`Django DATABASE settings`: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-DATABASE-ENGINE

Specifying the environment variables
=====================================

There are two strategies to specify the environment variables:

* provide them in a ``.env`` file
* start the component processes (with uwsgi/gunicorn/celery) in a process
  manager that defines the environment variables

Providing a .env file
---------------------

This is the most simple setup and easiest to debug. The ``.env`` file must be
at the root of the project - i.e. on the same level as the ``src`` directory (
NOT *in* the ``src`` directory).

The syntax is key-value:

.. code::

   SOME_VAR=some_value
   OTHER_VAR="quoted_value"


Provide the envvars via the process manager
-------------------------------------------

If you use a process manager (such as supervisor/systemd), use their techniques
to define the envvars. The component will pick them up out of the box.
