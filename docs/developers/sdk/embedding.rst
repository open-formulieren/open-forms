.. _developers_sdk_embedding:

===========================
Embedding the SDK in a page
===========================

The SDK can be embedded by loading the Javascript code and stylesheet.

Assuming the SDK is hosted on ``https://example.com/sdk/1.0.0/``, two resources need to be
loaded.

Loading static assets
=====================

1. The default stylesheet

    .. code-block:: html

        <link rel="stylesheet" href="https://example.com/sdk/1.0.0/open-forms-sdk.css" />

2. The Javascript code

    .. code-block:: html

        <script src="https://example.com/sdk/1.0.0/open-forms-sdk.js"></script>

Calling the SDK
===============

Once the Javascript is loaded, the module ``OpenForms`` is available. To initialize
a form, use the constructor and initialize the form:

.. code-block:: js

    const form = new OpenForms.OpenForm(element, options);
    form.init();

Where ``element`` is a valid DOM node and ``options`` an options Object, see
:ref:`developers_sdk_embedding_options`.

.. _developers_sdk_embedding_options:

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
    URLs relatively to this URL. If not provided, ``window.location.pathname`` is used.

``lang``:
    Optional language to use for internationalizing. By default, this is looked up from
    the ``lang`` attribute of the ``html`` element in the DOM - if this is not set, the
    default value of ``'nl'`` is used.

``sentryDSN``:
    A `Sentry DSN <https://docs.sentry.io/>`_ to monitor the SDK.

``sentryEnv``:
    The label of the Sentry environment to use, for example ``'production'``. Used in
    combination with ``sentryDSN``. Defaults to an empty string.

Full example
============

.. code-block:: html

    <!-- Load stylesheet and SDK bundle -->
    <link rel="stylesheet" href="https://example.com/sdk/1.0.0/open-forms-sdk.css" />
    <script src="https://example.com/sdk/1.0.0/open-forms-sdk.js"></script>

    <!-- Load a form and render it -->
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

Deploying the SDK
=================

The SDK is published as container image on
`Docker Hub <https://hub.docker.com/r/openformulieren/open-forms-sdk>`_, containing
the static Javascript and CSS assets:

* ``open-forms-sdk.js`` and
* ``open-forms-sdk.css``

When you're deploying the ``latest`` tag, these assets are available in the webroot,
e.g. ``http://localhost:8080/open-forms-sdk.js``.

When you're using a pinned version, such as ``1.0.0``, the assets are available in that
directory: ``http://localhost:8080/1.0.0/open-forms-sdk.js``.

The SDK follow semantic versioning.
