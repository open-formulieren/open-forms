.. _installation_upgrade_300:

===================================
Upgrade details to Open Forms 3.0.0
===================================


Open Forms 3.0 is a major version release that contains some breaking changes. As always
we try to limit the impact of breaking changes through automatic migrations, and this
release is no different, but there are some subtle changes in behaviour that you should
be aware of, as they may require additional manual actions.

.. contents:: Jump to
   :depth: 1
   :local:

Legacy OpenID Connect callback endpoints are now disabled by default
====================================================================

Before Open Forms 3.0, the legacy endpoints were used by default.

The following environment variables now default to ``False`` instead of ``True``:

* ``USE_LEGACY_OIDC_ENDPOINTS``
* ``USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS``
* ``USE_LEGACY_ORG_OIDC_ENDPOINTS``

To keep the old behaviour, make sure you deploy with:

.. code-block:: bash

    USE_LEGACY_OIDC_ENDPOINTS=True
    USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS=True
    USE_LEGACY_ORG_OIDC_ENDPOINTS=True

To use the new behaviour, you must ensure that
``https://open-formulieren.gemeente.nl/auth/oidc/callback/`` is listed in the allowed
**Redirect URI** values of your identity provider.

Removal of price logic
======================

Price logic rules are removed in favour of setting the submission price via a form
variable and normal logic rules. The conversion is automatic.

There is a slight change in behaviour. When no price logic rules matched the trigger
condition, the price set on the related product was used. This can lead to surprises
and wrong amounts being paid due to logical errors in the form itself.

The new behaviour will (deliberately) cause a crash that will show to the end-user
as "something unexpectedly went wrong", since we refuse to make any (likely wrong)
assumptions about the amount that needs to be paid. Crash information is visible
in the error monitoring if that's set up correctly.

.. note:: Existing, automatically converted forms are crash-free because we create an
   explicit fallback logic rule that mimicks the old behaviour.

Removed legacy "machtigen" context
==================================

Open Forms 2.7.0 revamped how mandates ("machtigingen") are captured when DigiD
Machtigen or eHerkenning Bewindvoering are used. We kept the old structure in place to
give some time to transition and are now removing this in favour of the new setup. For
the time being, the new setup still defaults to "Lax" mode, meaning it will continue to
work when some information is missing that is considered required. We recommend to opt
in to strict mode though, through the ``DIGID_EHERKENNING_OIDC_STRICT`` feature
flag/environment variable.

You are affected by this if you use the static variable ``auth.machtigen`` in your
registration backends. Instead, you should use the ``auth_context`` static variable.
Since Open Forms 2.7.0, the same data has been saved to both datastructures.

Form components/fields changes
==============================

Password component removed
--------------------------

The password component was deprecated a long time ago, and has now been removed. If you
need to replace it anywhere, use a regular textfield component instead, but you really
shouldn't be asking users for passwords.

Removed import conversions
==========================

For a number of changes, Open Forms ensured that old form exports could still be
imported and would automatically convert some data. Some of these conversion have been
removed.

Removal of objecttype URL conversion in the Objects API registration options
----------------------------------------------------------------------------

Since the UX improvments in Open Forms 2.8.0 you can select the object type in a
dropdown, and under the hood we save the unique identifier rather than the full API
resource URL (which you used to have to copy-paste in a text field). The usage of
hyperlinks for the object type is now also disallowed when importing a form.

Previously the hyperlinks would be converted to the expected format, and saved as such,
which was quite complex and not ideal for exports using the new format. We
recommend re-creating the exports on a newer version of Open Forms.

Removal of legacy translations conversion
-----------------------------------------

Old (from before Open Forms 2.4) form export files containing form field translations
in the legacy format are now ignored instead of converted to the new format. We
recommend re-creating the exports on a newer version of Open Forms.

StUF-ZDS payments extension conversion
--------------------------------------

The import conversion of StUF-ZDS plugin extensions, back to the default StUF-ZDS plugin,
has been removed. We recommend re-creating the exports on a newer version of Open Forms,
or manually changing the plugin to `stuf-zds-create-zaak` in the export files.

Removal of single registration conversion
-----------------------------------------

The legacy format (from before Open Forms 2.3) for registration backend will no longer be
converted to the current standard. When importing a form with this configuration,
the form will be created without registration backends.

``FormDefinition.name`` field is now read only
----------------------------------------------

The ``name`` field of a ``FormDefinition`` export is no longer written to the matching
active locale field (``name_nl`` or ``name_en``) during imports. Instead, the
``translations`` key is used. This affects forms that were exported before the
``translations`` key existed.  We recommend re-creating the exports on a newer version
of Open Forms.

Removal of ``formStep`` reference in form logic
-----------------------------------------------

The ``formStep`` key was deprecated in favour of ``formStepUuid`` and the conversion
code has been removed. This may affect form exports from before Open Forms 2.1.0. We
recommend re-creating the exports on a newer version of Open Forms.

Removal of cosign template tag patching
---------------------------------------

In Open Forms 2.3, the template tag ``{% cosign_information %}`` was introduced and
automatically added to confirmation templates during import if it was absent. This
automatic patching has now been removed. We recommend re-creating the exports on Open
Forms 2.3 or newer.

Removal of /api/v2/location/get-street-name-and-city endpoint
=============================================================

The /api/v2/location/get-street-name-and-city was deprecated for some time,
and is now removed in favor of the /api/v2/geo/address-autocomplete endpoint.

Legacy temporary file uploads no longer supported
=================================================

Before Open Forms 2.7.0, temporary file uploads (as created by the file upload form
component) would not be related to the submission they were uploaded in. We call these
legacy temporary file uploads, and support for them has been removed in Open Forms 3.0.

The setting ``TEMPORARY_UPLOADS_REMOVED_AFTER_DAYS`` controls how long file uploads are
kept. Ensure that this many days have passed since the last legacy upload before
upgrading to Open Forms 3.0, otherwise you will run into database errors during the
upgrade.

Deprecations in registration backends
=====================================

We've done extensive UX rework in the Objects API and ZGW API's registration backends -
you can now select the case and/or document types to use in dropdowns rather than having
to copy-paste the API resource URLs. The API resource URLs will continue to work and
are scheduled for removal in Open Forms 4.0 (no planned date for this yet), but we
recommend you to already migrate your forms to the new format:

* it has a better UX for the people configuring forms :)
* it automatically picks the correct version from the Catalogi API

Migrating is as simple as opening the registration options, selecting the catalogue to
use and then selecting the case type/document type to use and emptying the URL-field.
