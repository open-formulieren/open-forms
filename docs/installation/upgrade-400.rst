===================================
Upgrade details to Open Forms 4.0.0
===================================

Open Forms 4.0 is a major version release that contains breaking changes.

.. contents:: Jump to
   :depth: 1
   :local:
   :backlinks: none

Removal of legacy OpenID Connect callback endpoints
====================================================

.. note:: Relevant for: devops, identity provider administrators.

The legacy plugin-specific OIDC callback endpoints have been removed. These were
introduced as a migration path in Open Forms 2.x and have been deprecated since then.

The following URL paths no longer exist:

* ``/digid-oidc/callback/``
* ``/digid-machtigen-oidc/callback/``
* ``/eherkenning-oidc/callback/``
* ``/eherkenning-bewindvoering-oidc/callback/``
* ``/org-oidc/callback/``

All OIDC identity providers must now redirect to ``https://<domain>/auth/oidc/callback/``.

The following environment variables are no longer read and can be removed from your
deployment configuration:

* ``USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS``
* ``USE_LEGACY_ORG_OIDC_ENDPOINTS``
* ``USE_LEGACY_OIDC_ENDPOINTS``

Removal of the UMD bundle (SDK)
===============================

.. note:: Relevant for: external integration developers.

Since Open Forms 3.1, we prefer ESM bundles over UMD bundles because they're smaller
and better suited for users with slow (mobile) network connections. The UMD bundle
support has now been removed.

**Impact**

If you are loading the Javascript assets from any of the following endpoints:

* ``/static/sdk/bundles/open-forms-sdk.js``
* ``/static/sdk/open-forms-sdk.js``

these URLs will no longer work. Instead, replace the ``.js`` extension with ``.mjs``:

* ``/static/sdk/bundles/open-forms-sdk.mjs``
* ``/static/sdk/open-forms-sdk.mjs``

Additionally, the global ``window.OpenForms`` no longer exists, and you must use
``import`` syntax to initialize the SDK, for example:

.. code-block:: html

    <link href="https://open-forms.example.com/static/sdk/bundles/open-forms-sdk.mjs" rel="modulepreload" />
    <div
        class="open-forms-sdk-root"
        id="openforms-container"
        data-sdk-module="https://open-forms.example.com/static/sdk/bundles/open-forms-sdk.mjs"
        data-form-id="123"
        data-base-url="https://open-forms.example.com/api/v2/"
        data-base-path="/my-form/"
        data-csp-nonce="POBdlO9C3gRmVC8l6/Facw=="
    ></div>
    <script type="module" src="/open-forms-sdk-wrapper.mjs"></script>

with the ``open-forms-sdk-wrapper.mjs`` example code:

.. code-block:: js

    /**
     * Given a form node on the page, extract the options from the data-* attributes and
     * initialize it.
     * @param  {HTMLDivElement} node The root node for the SDK where the form must be
     * rendered. It must have the expected data attributes.
     * @return {Void}
     */
    const initializeSDK = async node => {
      const {
        sdkModule,
        formId,
        baseUrl,
        basePath,
        cspNonce,
        sentryDsn = '',
        sentryEnv = '',
      } = node.dataset;
      const {OpenForm} = await import(sdkModule);

      // initialize the SDK
      const options = {
        baseUrl,
        formId,
        basePath,
        CSPNonce: cspNonce,
      };
      if (sentryDsn) options.sentryDSN = sentryDsn;
      if (sentryEnv) options.sentryEnv = sentryEnv;
      const form = new OpenForm(node, options);
      form.init();
    };

    const sdkNodes = document.querySelectorAll('.open-forms-sdk-root');
    sdkNodes.forEach(node => initializeSDK(node));
