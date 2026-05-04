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

NL Design System related changes
================================

.. note:: Relevant for: custom theme developers.

We frequently check our own markup and CSS code for opportunities to replace custom
implementations with existing NL Design System (community) components. As an organization
that uses NL DS, you benefit from this with more consistent appearance of the same
logical components in different places.

However, because Open Forms existed *before* NL DS was commonplace, this sometimes leads
to changes in appearance, because what used to be hardcoded CSS is now parametrized,
and we don't have any guarantees that the relevant design tokens are set.

Below you find a summary of components that were moved from custom CSS to existing
NL DS components that may require visual inspection/additional definitions in your
custom theme stylesheet(s).

Default design token values removal
-----------------------------------

Open Forms 3.1.0 added some default design token values for backwards compatibility
reasons. These have been removed. If you rely on them, make sure to define the tokens
explicitly:

* ``--utrecht-button-column-gap``
* ``--of-form-navigation-row-gap``
* ``--of-abort-button-color``

Cookie group
------------

On the cookie-list page ("Manage cookies", via the footer), the descriptions of a cookie
group are now rendered using the ``utrecht-paragraph`` component instead of our
hardcoded CSS. Additionally, the accept/decline buttons/status are now rendered using
the ``utrecht-button-group`` component. You may see changed spacings between content
and may want to define or override:

* ``--utrecht-paragraph-line-height: 1.5;`` for the spacing between text lines
* ``--utrecht-button-group-inline-gap: 20px;``

Cookie notice
-------------

The cookie notice/banner has been slightly revised. The styling that causes the banner
to only take up part of the viewport width is now scoped to the Open Formulieren theme,
meaning that you should include a similar rule if you have custom themes. This is an
ongoing effort to consistently deal with different viewports (mobile vs. desktop) in the
NL DS ecosystem.

The CSS rule to include is:

.. code-block:: css

    @media (min-width: 992px) {
      .cookie-notice {
        max-inline-size: 75vw;
      }
    }

Additionally, we now rely on ``--utrecht-document-line-height`` for the spacing of the
text content. To restore the old behaviour, include:

.. code-block:: css

    line-height: 1.5;

Removed deprecations
--------------------

The following fallbacks were deprecated and have been removed.

**``backtotop-link`` component**

* removed fallback to ``--utrecht-button-column-gap``, specify
  ``--of-backtotop-link-column-gap`` explicitly
* removed fallback to ``--utrecht-button-padding-block-end``, specify
  ``--of-backtotop-link-padding-block-end`` explicitly
* removed fallback to ``--utrecht-button-padding-block-start``, specify
  ``--of-backtotop-link-padding-block-start`` explicitly

Removal of the Elastic APM agent
================================

Elastic APM has historically been the mechanism to get some performance-related
telemetry from Open Forms into an observability platform. Since Open Forms 3.3 (released
9 months ago), we've been adding support for Open Telemetry as replacement, which is a
vendor-agnostic observability protocol and ecosystem.

You can remove any ``ELASTIC_APM_*`` related environment variables from your deployment
code, and if you haven't done so yet, recommend you to set up the necessary
:ref:`observability <installation_observability_index>` tooling. See
:ref:`installation_observability_otel_config` on how to configure Open Forms to produce
telemetry.
