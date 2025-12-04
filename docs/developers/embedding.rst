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

2. Preload the Javascript code

    .. code-block:: html

        <link href="https://openforms.example.com/static/sdk/open-forms-sdk.mjs" rel="modulepreload" />

Rendering the form
==================

Once the Javascript is loaded, the module ``OpenForms`` is available. To initialize
a form, use the constructor and initialize the form:

.. code-block:: html

    <script type="module" nonce="[CSP-NONCE]">
        import {OpenForm} from 'https://openforms.example.com/static/sdk/open-forms-sdk.mjs';

        const form = new OpenForm(element, options);
        form.init();
    </script>

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
        This is a last resort solution - preferably the backend where you embed the form
        would set up "wildcard" routes to ensure that refreshing the page works, e.g.
        ``/some-path/<form-id>/*`` should just load the CMS page for a specific form.

        See :ref:`developers_embedding_cms_guidelines` for more details.

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

    Two parameters are passed as arguments to the ``onLanguageChange`` function:

        1. The new active language as a two-letter identifier
        2. The initial data reference (if applicable)

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
        <link rel="stylesheet" href="https://openforms.example.com/static/sdk/open-forms-sdk.css" />
        <link rel="modulepreload" href="https://openforms.example.com/static/sdk/open-forms-sdk.mjs" />
    </head>

    <body>
        <!-- Load an Open Forms form and render it -->
        <div
            id="openforms-root"
            data-base-url="https://openforms.example.com/api/v1/"
            data-form-id="0d2f5453-8987-43dd-952e-aad3dd8f2318"
            data-base-path="/some-cms-page"
        ></div>
        <script type="module">
            import {OpenForm} from 'https://openforms.example.com/static/sdk/open-forms-sdk.mjs';

            var targetNode = document.getElementById('openforms-root');
            var form = new OpenForm(targetNode, targetNode.dataset);
            form.init();
        </script>
    </body>
    </html>

Advanced example
----------------

.. code-block:: html

    <!-- Optional to render Open Forms in the proper language -->
    <html lang="nl">
    <head>
        <!-- Required for icons used by Open Forms -->
        <meta charset="utf-8">

        <!-- Load stylesheet and SDK bundle -->
        <link rel="stylesheet" href="https://openforms.example.com/static/sdk/open-forms-sdk.css" />
        <link rel="modulepreload" href="https://openforms.example.com/static/sdk/open-forms-sdk.mjs" />
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
            import {OpenForm} from 'https://openforms.example.com/static/sdk/open-forms-sdk.mjs';

            var targetNode = document.getElementById('openforms-root');
            var form = new OpenForm(targetNode, targetNode.dataset);
            form.init();
        </script>
    </body>
    </html>

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

.. _developers_embedding_cms_guidelines:

Third party CMS guidelines
==========================

When embedding forms on other web pages, those web pages are typically kept in a
content management system (CMS). This tends to create some URL routing challenges,
as the page ID is usually defined in the URL and retrieved from a database.

The embedded forms on a page (by default) have their own nested URL routes/locations,
relative to the page where it's loaded. For example, a CMS contact page could be hosted
at ``https://example.com/contact-us``. The embedded form on that page would then manage
the form-specific URLs, e.g.:

* ``https://example.com/contact-us/startpagina``
* ``https://example.com/contact-us/stap/uw-gegevens``
* ``https://example.com/contact-us/stap/uw-vraag``
* ``https://example.com/contact-us/stap/bevestiging``

This works fine *as long as the user doesn't refresh their browser* (e.g. by hitting
F5), because when they do that, the CMS server usually tries to find that exact page,
but those URLs are not known/managed by the CMS solution, so the user gets an 404 error
saying the page wasn't found.

The most elegant solution here is for the CMS provider to support "catch-all" or
"wildcard" routes that match on a part of the URL. In this example, such a catch-all
route would look like:

* ``https://example.com/contact-us/*``

Every sub-route of that page would load the "Contact us" page, and the form is smart
enough to figure out which part of the form is requested, allowing the user to continue
in their form.

If that is not possible, the "hash-routing" alternative is available, but it has a
massive drawback that "anchors" on the page break the form navigation. You could have
a table-of-contents with an anchor to ``#address`` for example, but that is not
understood by the embedded form, yet it tries to use it.
