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

Removal of /api/v2/location/get-street-name-and-city endpoint
=============================================================

The /api/v2/location/get-street-name-and-city was deprecated for some time,
and is now removed in favor of the /api/v2/geo/address-autocomplete endpoint.
