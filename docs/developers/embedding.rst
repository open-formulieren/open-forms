.. _developers_embedding:

===============================
Embed forms in an existing site
===============================

The SDK can be embedded in existing sites by loading the Javascript code and stylesheet.

Assuming the SDK is hosted on ``https://openforms.example.com/static/sdk/``, two
resources need to be loaded.

.. note::

    The backend automatically redirects to the versioned SDK URLs. Before you
    embed a particular version of the SDK, please familiarize yourself with the
    :ref:`versioning policy <developers_versioning>`.

Loading static assets
=====================

1. The default stylesheet

    .. code-block:: html

        <link rel="stylesheet" href="https://openforms.example.com/static/sdk/open-forms-sdk.css" />

2. The Javascript code

    .. code-block:: html

        <script src="https://openforms.example.com/static/sdk/open-forms-sdk.js"></script>

.. note::

    We provide an EXPERIMENTAL npm package that you should be able to integrate in your
    own frontend toolchain, as an alternative to loading the assets directly in a page.

    .. code-block:: bash

        npm install --save @open-formulieren/sdk

Rendering the form
==================

Once the Javascript is loaded, the module ``OpenForms`` is available. To initialize
a form, use the constructor and initialize the form:

.. code-block:: js

    const form = new OpenForms.OpenForm(element, options);
    form.init();

Where ``element`` is a valid DOM node and ``options`` an options Object, see
:ref:`developers_embedding_options`.

.. _developers_embedding_options:

Available options
-----------------

``baseUrl``:
    Required. The API root of the Open Forms backend server. Note that this server must
    be configured to allow Cross Origin requests (CORS) from the domain where the SDK is
    used.

``formId``:
    Required. The UUID or slug of the form to embed. This can be obtained via the Open
    Forms admin interface.

``basePath``:
    Optional, but highly recommended. The SDK considers this as the base URL and builds all
    URLs relatively to this URL.

    If not provided, ``window.location.pathname`` is used.

    .. note::
        ``basePath`` only applies when using the default browser routing. If hash based routing
        is used (see ``useHashRouting`` below), the option will be silently ignored.

``useHashRouting``:
    Whether hash based routing should be used. Defaults to ``false``. This option is useful when embedding
    Open Forms with a CMS. If the SDK is hosted at ``https://example.com/basepath?cms_query=1``, the resulting URL
    would be ``https://example.com/basepath?cms_query=1#/startpagina`` (SDK specific query parameters would come
    at the end of the URL).

    .. warning::
        This is a last resort solution - preferably the backend where you embed the form would set up "wildcard" routes to
        ensure that refreshing the page works, e.g. ``/some-path/<form-id>/*`` should just load the CMS page for a specific form.

``CSPNonce``:
    Recommended. The page's CSP Nonce value if inline styles are blocked by your
    `Content Security Policy <https://content-security-policy.com/nonce/>`_. The Open
    Forms SDK renders HTML in a number of places that may contain inline styles (as the
    result of a WYSYWIG editor). If a nonce is provided, the inline styles receive the
    value. Otherwise the styles will be blocked. This is not required if you have
    ``style-src 'unsafe-inline'`` as part of your policy.

``lang``:
    Optional language to use for internationalizing. By default, this is looked up from
    the ``lang`` attribute of the ``html`` element in the DOM - if this is not set, the
    default value of ``'nl'`` is used.

``onLanguageChange``:
    Optional function to call on language changes. By default, the SDK reloads the
    content and changes the active language of the form. When using ``onLanguageChange``,
    your function will be executed on language change, instead of the default logic.

    The new active language will be passed as an argument to the ``onLanguageChange``
    function as a two-letter identifier.

``sentryDSN``:
    Optional `Sentry DSN <https://docs.sentry.io/>`_ to monitor the SDK.

``sentryEnv``:
    The label of the Sentry environment to use, for example ``'production'``. Used in
    combination with ``sentryDSN``. Defaults to an empty string. Should be filled if
    ``sentryDSN`` is used but it's not required.

Content Security Policy (CSP)
-----------------------------

When you are embedding the SDK on your page, it must behave according to your Content
Security Policy.

Certain components have :ref:`specific CSP requirements <developers_csp_sdk_embedding>`.

Examples
========

Let's assume these examples are hosted on: ``example.com/some-cms-page``

Minimal example
---------------

.. code-block:: html

    <html>
    <head>
        <!-- Required for icons used by Open Forms -->
        <meta charset="utf-8">

        <!-- Load stylesheet and SDK bundle -->
        <link rel="stylesheet" href="https://openforms.example.com/sdk/1.0.0/open-forms-sdk.css" />
        <script src="https://openforms.example.com/sdk/1.0.0/open-forms-sdk.js"></script>
    </head>

    <body>
        <!-- Load an Open Forms form and render it -->
        <div
            id="openforms-root"
            data-base-url="https://openforms.example.com/api/v1/"
            data-form-id="0d2f5453-8987-43dd-952e-aad3dd8f2318"
            data-base-path="/some-cms-page"
        ></div>
        <script>
            var targetNode = document.getElementById('openforms-root');
            var form = new OpenForms.OpenForm(targetNode, targetNode.dataset);
            form.init();
        </script>
    </body>
    </html>

Full example
------------

.. code-block:: html

    <!-- Optional to render Open Forms in the proper language -->
    <html lang="nl">
    <head>
        <!-- Required for icons used by Open Forms -->
        <meta charset="utf-8">

        <!-- Load stylesheet and SDK bundle -->
        <link rel="stylesheet" href="https://openforms.example.com/sdk/1.0.0/open-forms-sdk.css" />
        <script src="https://openforms.example.com/sdk/1.0.0/open-forms-sdk.js"></script>
    </head>

    <body>
        <!-- Load an Open Forms form and render it -->
        <div
            id="openforms-root"
            data-base-url="https://openforms.example.com/api/v1/"
            data-form-id="0d2f5453-8987-43dd-952e-aad3dd8f2318"
            data-base-path="/some-cms-page"
            data-csp-nonce="OSUzOHNqqL9HzWU0CVSC/w\u003D\u003D"
            data-lang="nl"
            data-sentry-dsn="https://a45b81b258d462ae4ec474c10b6430cb@sentry.example.com/1"
            data-sentry-env="example"
        ></div>
        <script nonce="OSUzOHNqqL9HzWU0CVSC/w==">
            var targetNode = document.getElementById('openforms-root');
            var form = new OpenForms.OpenForm(targetNode, targetNode.dataset);
            form.init();
        </script>
    </body>
    </html>

More examples
-------------

See (on Github) the directory ``docker/embedding`` README file for working examples of
different embedding cases. These should be easy to bring up with ``docker compose``, provided
you have a backend instance ready to go.

Backend configuration
=====================

To enable embedding the SDK on domains other than the domain where the backend is
deployed, you need to appropriately :ref:`configure <installation_environment_config>`
a number of settings.

.. warning::

    Embedding with cross-site requests in an HTTP context is not possible, as it
    requires the ``SameSite=None`` attribute to be set, which in turn requires the
    ``Secure`` attribute. See the `MDN documentation about SameSite`_.


* ``IS_HTTPS``: set this to ``True`` to get all the correct defaults.
* ``CORS_ALLOWED_ORIGINS`` see the section below on CORS.
* ``CSRF_TRUSTED_ORIGINS`` see the section below on CORS.

Cross Origin Resource Sharing (CORS)
------------------------------------

Note that the backend must be configured to allow cross origin requests from the domains
that embed the SDK. See the :ref:`CORS configuration reference <installation_config_cors>`
for details.

Additionally, you need to configure your infrastructure to allow CORS requests for the
font-files. An example nginx rule looks like this:

.. code-block:: nginx

    location ~* ^/static/.*\.(eot|ttf|woff|woff2|svg)$ {
        add_header Access-Control-Allow-Origin *;  # this header is crucial
        # delegate to uwsgi backend
        proxy_pass http://open-forms-backend:8000;
    }

Failing to configure this will result in the font files not being loaded and the UI
looking weird. Icons may also be broken.

The domain embedding the forms must also expose the ``Referer`` header to the API, via
the `Referrer Policy`_ response headers. The strictest possible
value is ``strict-origin-when-cross-origin``.


.. _Referrer Policy: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy
.. _MDN documentation about SameSite: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie#samesitesamesite-value

Deploying the SDK
=================

.. note:: These assets are bundled in the backend image too, so you typically do not
   need to deploy the SDK assets separately. You can point to
   ``https://openforms.example.com/static/sdk/`` for convenience.

The SDK is published as container image on
`Docker Hub <https://hub.docker.com/r/openformulieren/open-forms-sdk>`_, containing
the static Javascript and CSS assets:

* ``open-forms-sdk.js`` and
* ``open-forms-sdk.css``

When you're deploying the ``latest`` tag, these assets are available in the webroot,
e.g. ``http://localhost:8080/open-forms-sdk.js``.

When you're using a pinned version, such as ``1.0.0``, the assets are available in that
directory: ``http://localhost:8080/1.0.0/open-forms-sdk.js``.

The SDK follows semantic versioning.
