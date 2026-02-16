.. _installation_environment_config:

===================================
Environment configuration reference
===================================

Open Forms can be ran both as a Docker container or directly on a VPS or
dedicated server. It depends on other services, such as database and cache
backends, which can be configured through environment variables.

You also need to expose Open Forms through a web server acting as a reverse proxy, such
as nginx or your ingress solution on Kubernetes. See the
:ref:`installation_config_webserver` section for some configuration recommendations.

.. seealso::

    * :ref:`installation_security`

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

* ``BASE_URL``: The absolute base URL where the Open Forms (backend) is (publicly)
  accessible. The format must be
  ``http[s]://<hostname>[:<optional-port>]/[optional-path]``. This URL is used in
  various security mechanisms, in tooling to construct fully qualified absolute URLs
  (outside of regular HTTP requests) and serves as input for automatic configuration
  aspects such as the analytics configuration.

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

.. seealso:: For advanced Celery broker/result backend configurations, see
   :ref:`installation_redis`.

.. _email-settings:

Email settings
--------------

* ``MAILER_USE_BACKEND``: Configure the e-mail backend. Defaults to ``django.core.mail.backends.smtp.EmailBackend``. Set to ``django_o365mail.EmailBackend`` for sending via the Office365 Graph API.

* ``DEFAULT_FROM_EMAIL``: The email address to use a default sender. Defaults
  to ``openforms@example.com``.

**SMTP**

* ``EMAIL_HOST``: Email server host. Defaults to ``localhost``.

* ``EMAIL_PORT``: Email server port. Defaults to ``25``.

* ``EMAIL_HOST_USER``: Email server username. Defaults to ``""``.

* ``EMAIL_HOST_PASSWORD``: Email server password. Defaults to ``""``.

* ``EMAIL_USE_TLS``: Indicates whether the email server uses TLS. Defaults to
  ``False``.

* ``EMAIL_TIMEOUT``: How long to wait for blocking operations like the connection attempt, in seconds. Defaults to ``10``.

**Office365 Graph API**

* ``O365_MAIL_CLIENT_ID``: Application client ID for Office365 Graph API authentication. Defaults to ``""``.

* ``O365_MAIL_CLIENT_SECRET``: Application client secret for Office365 Graph API authentication. Defaults to ``""``.

* ``O365_MAIL_TENANT_ID``: Tenant ID where the application is registered. Defaults to ``""``.

* ``O365_MAIL_RESOURCE``: The email address/mailbox resource to use for sending emails. Optional - if not specified, the default mailbox for the authenticated user will be used. Defaults to ``""``.

* ``O365_MAIL_SAVE_TO_SENT``: Whether to save sent emails. Defaults to ``False``.

* ``O365_ACTUALLY_SEND_IN_DEBUG``: Whether to actually send emails when ``DEBUG`` is enabled. Defaults to ``False``.

.. _installation_config_cors:

Cross-Origin Resource Sharing (CORS) settings
---------------------------------------------

See: https://github.com/adamchainz/django-cors-headers

* ``CORS_ALLOWED_ORIGINS``: A list of origins that are authorized to make
  cross-site HTTP requests. Defaults to ``[]``. An example value would be:
  ``https://cms.example.org,https://forms.example.org``

* ``CSRF_TRUSTED_ORIGINS``: the list of trusted CSRF origins, e.g. ``https://cms.example.com``.
  When embedding forms on third party sites, these third party domains need to be added
  to the allowlist. The default value is taken from the ``CORS_ALLOWED_ORIGINS`` setting.
  See also `the Django documentation <https://docs.djangoproject.com/en/4.2/ref/settings/#csrf-trusted-origins>`_.

It is recommended to configure CORS explicitly by setting just ``CORS_ALLOWED_ORIGINS``.

**Other CORS-settings**

The settings below are available but should only be specified/used when you have
intricate knowledge of how they are used. While wildcards and regexes may seem
attractive options, we are currently limited by our framework in how
``CSRF_TRUSTED_ORIGINS`` can be specified (which must be an explicit list without
patterns or wildcards).

* ``CORS_ALLOW_ALL_ORIGINS``: If ``True``, all origins will be allowed. Other
  settings restricting allowed origins will be ignored.Defaults to ``False``.

* ``CORS_ALLOWED_ORIGIN_REGEXES``: A list of strings representing regexes that
  match Origins that are authorized to make cross-site HTTP requests. Defaults
  to ``[]``.

* ``CORS_EXTRA_ALLOW_HEADERS``: The list of non-standard HTTP headers that can
  be used when making the actual request. These headers are added to the
  internal setting ``CORS_ALLOW_HEADERS``. Defaults to ``[]``.


Content Security Policy (CSP) settings
--------------------------------------

* ``CSP_REPORT_ONLY``: if ``True``, CSP only reports violations but does not block them.
  Defaults to ``False``, meaning the CSP is enforced.

* ``CSP_REPORTS_SAVE``: whether to save violation reports to the database. Defaults to
  ``False``.

* ``CSP_REPORTS_LOG``: whether to log violation reports. In containerized environments
  this will be logged to ``stdout``, otherwise to file. If monitoring (Sentry) is set
  up, reports will also be visible there through logging. Defaults to ``True``.

* ``CSP_REPORT_PERCENTAGE``: float between 0 and 1.0, expressing the percentage of
  violations that will be reported. Defaults to ``1.0`` (100%).

* ``CSP_EXTRA_DEFAULT_SRC``: A comma separated list of extra ``default-src`` directives.
  Defaults to empty list.

* ``CSP_EXTRA_IMG_SRC``: A comma separated list of extra ``img-src`` directives.
  Defaults to empty list.

See also the :ref:`developer documentation <developers_csp>` and
https://django-csp.readthedocs.io/en/latest/ for more information on CSP.

Logging, monitoring and Open Telemetry settings
-----------------------------------------------

* ``SENTRY_DSN``: URL of the sentry project to send error reports to. Defaults
  to an empty string (i.e. no monitoring). See `Sentry settings`_.

* ``SDK_SENTRY_DSN``: URL of the sentry project for the SDK to send error reports to. Defaults
  to an empty string (i.e. no monitoring). This is a **public** Sentry DSN. See `Sentry settings`_.

* ``SDK_SENTRY_ENVIRONMENT``: the environment label for the SDK to group events. Defaults
  to ``ENVIRONMENT``.

* ``ELASTIC_APM_SERVER_URL``: Server URL of Elastic APM. Defaults to
  ``None``. If not set, Elastic APM will be disabled by setting internal
  setting ``ELASTIC_APM["ENABLED"]`` to ``False`` and
  ``ELASTIC_APM["SERVER_URL"]`` to ``http://localhost:8200``. See
  `Elastic settings`_.

* ``ELASTIC_APM_SECRET_TOKEN``: Token for Elastic APM. Defaults to ``default``.
  See `Elastic settings`_.

* ``LOG_STD_OUT``: Write all log entries to ``stdout`` instead of log files.
  Defaults to ``True`` when using Docker and otherwise ``False``.

* ``LOG_REQUESTS``: When enabled, all incoming requests are logged. Enabled by default.

**Open Telemetry**

Open Forms uses the official Python SDK which should adhere to the environment variables
`specification <https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/>`_.

There is one custom setting for integration with container runtimes:

* ``_OTEL_ENABLE_CONTAINER_RESOURCE_DETECTOR``: set to ``true`` when deploying with
  Docker engine or similar to enable container resource detection. On Kubernetes, it's
  recommended to enable the `kubernetes attributes processor`_ and leave this setting off.

See :ref:`installation_observability_otel_config` for recommended environment variable
configuration.

.. _`Sentry settings`: https://docs.sentry.io/
.. _`Elastic settings`: https://www.elastic.co/guide/en/apm/agent/python/current/configuration.html
.. _`kubernetes attributes processor`: https://opentelemetry.io/docs/platforms/kubernetes/collector/components/#kubernetes-attributes-processor

Processing of submissions
-------------------------

Submissions are :ref:`processed <developers_backend_core_submissions>` in the background after the
end-user has submitted the form data. This can fail because of external factors, and
Open Forms has an automatic-retry mechanism.

The following settings allow you to tweak the parameters of this mechanism.

* ``RETRY_SUBMISSIONS_INTERVAL``: the interval (in seconds) of retrying. Defaults to
  every 300s (5 min).

* ``RETRY_SUBMISSIONS_TIME_LIMIT``: the time limit from when the submission was
  submitted that automatic retries will continue. After this time limit has elapsed,
  there are no automatic retries anymore, but manual retries are still available.
  Defaults to ``48`` hours.

Other settings
--------------

* ``MAX_FILE_UPLOAD_SIZE``: configure the maximum allowed file upload size. See
  :ref:`installation_file_uploads` for more details. The default is ``50M``.

* ``DEBUG``: Used for more traceback information on development environment.
  Various other security settings are derived from this setting! Defaults to
  ``True`` for the ``dev`` environment, otherwise defaults to ``False``.

* ``IS_HTTPS``: Used to construct absolute URLs and controls a variety of
  security settings. Defaults to the inverse of ``DEBUG``.

  .. warning::

     We strongly recommended setting IS_HTTPS=False in local dev environments
     **only**. Deploying over HTTP instead of HTTPS makes you prone to man-in-the-middle
     attacks. Any instance reachable from *other* computers should only be deployed with
     HTTPS.

  The value of ``IS_HTTPS`` is used for the default values of:

      * ``LANGUAGE_COOKIE_SECURE``
      * ``LANGUAGE_COOKIE_SAMESITE``
      * ``SESSION_COOKIE_SECURE``
      * ``SESSION_COOKIE_SAMESITE``
      * ``CSRF_COOKIE_SECURE``
      * ``CSRF_COOKIE_SAMESITE``

  The idea is that any cookies automatically receive the ``Secure`` attribute when we're
  known to be in an HTTPS context. For non-HTTPS contexts this is disabled as it would
  otherwise break the application's functionality.

  Similarly, the ``SameSite`` attribute controls how cookies are restricted to domains
  other than the domain where the backend is deployed. In an HTTPS context it is set
  to ``None``, in an HTTP context it is set to ``Lax`` by default.

* ``USE_X_FORWARDED_HOST``: whether to grab the domain/host from the
  ``X-Forwarded-Host`` request header or not. This header is typically set by reverse
  proxies (such as nginx, traefik, Apache...). Default ``False`` - this is a header
  that can be spoofed and you need to ensure you control it before enabling this.

* ``DB_ENGINE``: Backend to use as database system. See
  `Django DATABASE settings`_ for a full list of backends. Only the default is
  supported but others might work. Defaults to ``django.db.backends.postgresql``

* ``CACHE_DEFAULT``: The default Redis cache location. Defaults to
  ``localhost:6379/0``.

* ``CACHE_AXES``: The Redis cache location for Axes (used to prevent brute
  force attacks). Defaults to ``localhost:6379/0``.

* ``ENVIRONMENT``: Short string to indicate the environment (test, production,
  etc.) Defaults to ``""``.

* ``SHOW_ENVIRONMENT``: Display environment information in the header in the admin.
  Defaults to ``True``. Environment information is only displayed to logged in users.

* ``ENVIRONMENT_LABEL``: Environment information to display, defaults to the value of
  ``ENVIRONMENT``. Only displayed when ``SHOW_ENVIRONMENT`` is set to ``True``. You can
  set this to strings like ``OpenGem PROD`` or simply ``PROD``, depending on your needs.

* ``ENVIRONMENT_BACKGROUND_COLOR``: CSS color value for the environment information
  background color. Defaults to ``orange``, example values can be specified in HEX
  format too, e.g.: ``#FF0000`` for red.

* ``ENVIRONMENT_FOREGROUND_COLOR``: CSS color value for the environment information
  text color. Defaults to ``black``. Follows the same rules as
  ``ENVIRONMENT_BACKGROUND_COLOR``.

* ``GIT_SHA``: The Git commit hash belonging to the code running the instance.
  Defaults to the automatically determined commit hash, if the application is
  run from a checked out Git repository.

* ``RELEASE``: The version of the application. If not provided, the
  ``GIT_SHA`` is used.

* ``SDK_RELEASE``: The version of the SDK bundled. By default, this is sourced from the
  ``.sdk-release`` file and should only be overridden if you're doing things in custom
  Docker images. The value is used to know which SDK JS/CSS files to include on the form
  detail page.

* ``USE_OIDC_FOR_ADMIN_LOGIN``: If enabled, the admin login page will automatically
  redirect to the OpenID Connect provider. You typically want to enable this if you
  enable :ref:`Organization accounts <configuration_authentication_oidc>`. Defaults
  to ``False``.

* ``SESSION_EXPIRE_AT_BROWSER_CLOSE``: Controls if sessions expire at browser close.
  This applies to both the session of end-users filling out forms and staff using the
  administrative interface. Enabling this forces users to log in every time they open
  their browser. Defaults to ``False``.

* ``EXTRA_VERIFY_CERTS``: A comma-separated list of paths to certificates to trust, empty
  by default. If you're using self-signed certificates for the services that Open Forms
  communicates with, specify the path to those (root) certificates here, rather than
  disabling SSL certificate verification. Example:
  ``EXTRA_VERIFY_CERTS=/etc/ssl/root1.crt,/etc/ssl/root2.crt``.

* ``SELF_CERTIFI_DIR``: Temporary directory where the generated bundle of
  ``EXTRA_VERIFY_CERTS`` will be stored.

* ``CACHE_PORTALOCKER``: Redis URL for file locks. Defaults to ``localhost:6379/0``.

* ``DEFAULT_TIMEOUT_REQUESTS``: The default timeout duration (in seconds) when calling
  external APIs/services. Defaults to ``10.0``. Requests taking longer than this
  duration are aborted and errors bubble up. Specific calls may use an explicitly
  provided timeout, which is not affected by this setting.

* ``CURL_CA_BUNDLE``: If this variable is set to an empty string, it disables SSL/TLS
  certificate verification. More information about why can be found on this
  `stackoverflow post <https://stackoverflow.com/a/48391751/7146757>`_. Even calls from
  Open Forms to any other service will be disabled, so this variable should be used with
  care to prevent unwanted side-effects.

* ``BEAT_SEND_EMAIL_INTERVAL``: the interval (in seconds) of sending queued e-mails,
  defaults to ``20``.

* ``SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS``: Configure how many days the URL to the submission report is usable.

* ``TEMPORARY_UPLOADS_REMOVED_AFTER_DAYS``: Configure how many days before unclaimed temporary uploads are removed.

* ``OPENFORMS_LOCATION_CLIENT``: The client to be used for auto filling a street name and city
  when given a postcode and house number.  Defaults to our internal BAG configuration.

* ``ENABLE_THROTTLING``: Enable or disable request throttling (to protect against (D)DOS, for example). Default enabled.

* ``THROTTLE_RATE_ANON``: Default throttle rate for anonymous users (this includes the
  end-users filling out (embedded) forms using the SDK!). Defaults to ``2500/hour``. Note
  that if throttling is disabled altogether, this configuration parameter has no effect.

* ``THROTTLE_RATE_USER``: Default throttle rate for authenticated users (typicall users
  logged in to the admin interface). Defaults to ``15000/hour``. Note that if throttling
  is disabled altogether, this configuration parameter has no effect.

* ``THROTTLE_RATE_POLLING``: Throttle rate for endpoints that are polled frequently. If
  you're authenticated as staff user, the throttling is bypassed completely. Defaults
  to ``50000/hour``. Note that if throttling is disabled altogether, this configuration
  parameter has no effect.

* ``NUM_PROXIES``: The number of application proxies that the API runs behind. See the
  `upstream documentation <https://www.django-rest-framework.org/api-guide/settings/#num_proxies>`_
  for more context. Defaults to ``1``.

* ``FORMS_EXPORT_REMOVED_AFTER_DAYS``: The number of days after which zip files of exported forms should be deleted.
  Defaults to 7 days.

* ``SUBPATH``: A string with a prefix for all URL paths, for example ``/openforms``. Typically used at the infrastructure level to route to a particular application on the same (sub)domain. Defaults to empty string meaning that Open Forms is hosted at the root (``/``).

* ``SENDFILE_BACKEND``: which backend to use to serve the content of non-public files. The value depends on the
  reverse proxy solution used with Open Forms. For available backends, see the `django-sendfile documentation`_.
  Defaults to ``sendfile.backends.nginx``.

  .. note:: Open Forms only considers nginx to be in scope. You can deviate from using nginx, but we cannot offer any
    support on other backends.

.. _django-sendfile documentation: https://django-sendfile2.readthedocs.io/en/stable/backends.html

.. _`Django DATABASE settings`: https://docs.djangoproject.com/en/4.2/ref/settings/#engine

.. _installation_environment_config_feature_flags:

Feature flags
=============

Open Forms sometimes supports a layered approach for feature flags, where some
behaviours can be enabled at deploy-time through environment variables already. If
this option is not available, you can still enable/disable the feature flag in the
admin interface, via **Admin** > **Configuration** > **Flag states**.

Feature flags are usually documented in the relevant module that they apply to. Below
you can find a list of feature flags that can be set through their matching environment
variables, linking to the description of their behaviour in their respective module.

* :ref:`ZGW_APIS_INCLUDE_DRAFTS <configuration_registration_objects_feature_flags>` -
  set to ``True`` to allow unpublished types to be used in the ZGW APIs.

* ``DIGID_EHERKENNING_OIDC_STRICT``: Enable strict claim processing/validation when
  using :ref:`configuration_authentication_oidc_digid`,
  :ref:`configuration_authentication_oidc_eherkenning` or
  :ref:`configuration_authentication_oidc_machtigen`. Defaults to ``False``.

  .. versionadded:: 2.7.0
     A formal and more complete authentication context data model is used - existing
     installations likely do not provide all this information yet.

Specifying the environment variables
====================================

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
