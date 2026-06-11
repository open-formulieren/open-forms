===================================
Upgrade details to Open Forms 4.0.0
===================================

Open Forms 4.0 is a major version release that contains breaking changes.

.. contents:: Jump to
   :depth: 1
   :local:
   :backlinks: none

Removal of JCC SOAP appointment plugin
======================================

The JCC plugin for appointments in Open Forms has stopped working as of Jan. 1st 2026 due
to JCC shutting down their SOAP service.

This has been replaced (since Open Forms v3.5) with their RESTful API service.

Removal of the unused HaalCentraal version 1.3
==============================================

.. note:: Relevant for: form designers/administrators.

HaalCentraal BRP Personen bevragen 1.3 was never in production so this is not available
any more in Open Forms. The only supported version is v2 by default.

In case v1.3 was used, the prefill configuration of components may require updating (fix
plugin + attribute), as this cannot be done automatically.

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

Change default to use OF-generated public reference
===================================================

.. note:: Relevant for: form designers/administrators.

The default way to generate public references for the ZGW APIs registration plugin has changed.
Previously, Open Forms always used case numbers as the submission public references.
Since Open Forms 3.5, both options have been available, but the default remained the ZGW API-generated
case numbers. The default is now switched to Open Forms-generated public references.

Logic engine rework
===================

.. note:: Relevant for: devops, form designers

The support for legacy logic evaluation has been removed, which means all forms will use the new logic evaluation.
Since Open Forms will now automatically assign all logic rules to the relevant form steps, it is also no longer
possible to specify a "trigger from step" for a logic rule.

TODO: this should probably a separate page describing the logic engine in more detail
For more information about the new logic evaluation, please refer to the
:ref:`detailed release notes of 3.5.0 <installation_upgrade_350>`.

.. warning::

    Before upgrading, all existing forms should be converted to the new logic evaluation. This can be done on a
    per-form basis, or in bulk using the following management command. Any forms which contain cycles in their
    logic rules need to be resolved manually. The output of the management command will include relevant form
    details if this is the case.

    .. code-block:: bash

        python /app/src/manage.py enable_new_logic_evaluation_for_all_forms

Clearing of values
------------------

TODO

Removal of legacy ZGW URLs support in registration plugins
==========================================================

The support for direct URL references to the Catalogi API for document types
("informatieobjecttype") and case types is removed. Open Forms 3.5 provides a migration
tool to convert these URLs into their indirect references that are more portable across
different environments (like from staging -> production).

ZGW APIs registration
---------------------

With the legacy URL support removal, the support for a "default catalogue" on the API
group level is also obsoleted. Open Forms 4.0 automatically moves this configuration
into all relevant form registration backend options where it's not configured yet.

This still has some impact though:

* users of setup-configuration may need to update their YAML assets that would populate
  the catalogue domain/RSIN.
* form exports pre 4.0 will not import cleanly into 4.0 environments, it's recommended
  to upgrade the source instance to 4.0 and re-generate the exports. Most notably, the
  registration backend options must contain:

  - an API group reference.
  - a catalogue reference (domain + RSIN) combination.

File component specific overrides
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before Open Forms 4.0, you could configure a specific document type, organization RSIN,
confidentiality level and/or title to use in the registration tab of the file component.

In 4.0, this has been moved into the variables tab, where you can configure these
options for each configured registration backend. This means the document type dropdown
now automatically filters valid options based on the specified catalogue and case type.

The old, component-specific configuration is no longer used. Importing of form exports
created on versions older than 4.0 will do a best-effort attempt to convert this.

Objects API registration
------------------------

With the legacy URL support removal, the support for a "default catalogue" and default
document type references on the API group level are also obsoleted. Open Forms 4.0
automatically moves this configuration into all relevant form registration backend
options where it's not configured yet.

This still has some impact though:

* users of setup-configuration may need to update their YAML assets that would populate
  the catalogue domain/RSIN and document type references.
* form exports pre 4.0 may not import cleanly into 4.0 environments, it's recommended
  to upgrade the source instance to 4.0 and re-generate the exports. If you have
  document types configured, make sure the form exports contain:

  - a catalogue reference (domain + RSIN) combination.
  - the document type references for each configuration option

File component specific overrides
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before Open Forms 4.0, you could configure a specific document type, organization RSIN,
confidentiality level and/or title to use in the registration tab of the file component.

In 4.0, this has been moved into the variables tab, where you can configure these
options for each configured registration backend. This means the document type dropdown
now automatically filters valid options based on the specified catalogue.

The old, component-specific configuration is no longer used. Importing of form exports
created on versions older than 4.0 will do a best-effort attempt to convert this.

Migration steps
---------------

For a successful migration, you need to start preparing already on your existing
instance which must be at least on version 3.5.4. Newer patches are always recommended.

On 3.5.x
~~~~~~~~

**Migration tool**

A DevOps engineer or other technical (system) administrator must execute a command line
script to migrate legacy URLs to the combination of ``(catalogueDetails, description)``
for document type references:

.. code-block:: bash

    # in a container/pod
    python src/manage.py migrate_catalogi_api_urls --no-dry-run

The output of the command will report which changes were made, and if any problems were
encountered. If problems are encountered, a functional administrator must edit the
affected forms in the admin interface to resolve the issues, after which the migration
tool can be run again.

Repeat these steps until no more problems are reported.

**Check script**

We're providing (currently in development) a check script that reports file components
in forms that have conflicting catalogue specifications compared to the registration
backends used in the forms.

You should run this script and resolve the problems in the admin interface. As long as
problems are reported, the update to Open Forms 4.0 is blocked.

On 4.0.x
~~~~~~~~

4.0 requires that the migration tool has been run successfully and that configuration is
consistent. This is automatically checked when you try to upgrade, and if problems are
detected, the upgrade is blocked so that you can safely roll back to 3.5 to address the
issues.

If no problems are detected, some automatic migrations will take place. You don't have
to do anything for this:

* Catalogue configuration specified on API groups will be moved into the registration
  backend options.
* Document type configuration specified on the API groups will be moved into the
  registration backend options.
* Document options (document type, organization RSIN, title, confidentiality level...)
  will be moved from the file component configuration into the relevant registration
  backend options.
