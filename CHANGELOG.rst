=========
Changelog
=========

2.6.4 (2024-04-16)
==================

Bugfix release

* [#4151] Fixed backend validation error being triggered for radio/select/selectboxes
  components that get their values/options from another variable.
* [#4052] Fixed payment (reminder) emails being sent more often than intended.
* [#4124] Fixed forms being shown multiple times in the admin list overview.
* [#4156] Fixed the format of order references sent to payment providers. You can now
  provide your own template.
* Fixed some bugs in the form builder:

    - Added missing error message codes (for translations) for the selectboxes component.
    - Fixed the "client-side logic" to take the correct data type into account.
    - Fixed the validation tab not being marked as invalid in some validation error
      situations.

* Upgraded some dependencies with their latest (security) patches.
* [#4172] Fixed a crash while running input validation on date fields when min/max date
  validations are specified.
* [#4141] Fixed a crash in the Objects API registration when using periods in component
  keys.

2.6.3 (2024-04-10)
==================

Bugfix release following feeback on 2.6.2

* [#4126] Fixed incorrect validation of components inside repeating groups that are
  conditionally visible (with frontend logic).
* [#4134] Fixed form designer admin crashes when component/variable keys are edited.
* [#4131] Fixed bug where component validators all had to be valid rather than at least
  one.
* [#4140] Added deploy configuration parameter to not send hidden field values to the
  Objects API during registration, restoring the old behaviour. Note that this is a
  workaround and the correct behaviour (see ticket #3890) will be enforced from Open
  Forms 2.7.0 and newer.
* [#4072] Fixed not being able to enter an MFA recovery token.
* [#4143] Added additional backend validation: now when form step data is being saved (
  including pausing a form), the values are validated against the component
  configuration too.
* [#4145] Fixed the payment status not being registered correctly for StUF-ZDS.

2.5.6 (2024-04-10)
==================

Hotfix release for StUF-ZDS users.

* [#4145] Fixed the payment status not being registered correctly for StUF-ZDS.

2.6.2 (2024-04-05)
==================

Bugfix release - not all issues were fixed in 2.6.1.

* Fixed various more mismatches between frontend and backend input validation:

    - [DH#671] Fixed conditionally making components required/optional via backend logic.
    - Fixed validation of empty/optional select components.
    - [#4096] Fixed validation of hidden (with ``clearOnHide: false``) radio components.
    - [DH#667] Fixed components inside a repeating group causing validation issues when
      they are nested inside a fieldset or columns.

* [#4061] Fixed not all form components being visible in the form builder when other
  components can be selected.
* [#4079] Fixed metadata retrieval for DigiD failing when certificates signed by the G1
  root are used.
* [#4103] Fixed incorrect appointment details being included in the submission PDF.
* [#4099] Fixed a crash in the form designer when editing (user defined) variables and
  the template-based Objects API registration backend is configured.
* Update image processing library with latest security fixes.
* [DH#673] Fixed wrong datatype for field empty value being sent in the Objects API
  registration backend when the field is not visible.
* [DH#673] Fixed fields hidden because the parent fieldset or column is hidden not being
  sent to the Objects API. This is a follow up of #3890.

2.5.5 (2023-04-03)
==================

Hotfix release for appointments bug

* [#4103] Fixed incorrect appointment details being included in the submission PDF.
* [#4079] Fixed metadata retrieval for DigiD failing when certificates signed by the G1
  root are used.
* [#4061] Fixed not all form components being visible in the form builder when other
  components can be selected.
* Updated dependencies to their latest security releases.

2.6.1 (2024-03-28)
==================

Hotfix release

A number of issues were discovered in 2.6.0, in particular related to the additional
validation performed on the backend.

* [#4065] Fixed validation being run for fields/components that are (conditionally)
  hidden. The behaviour is now consistent with the frontend.
* [#4068] Fixed more backend validation issues:

    * Allow empty string as empty value for date field.
    * Don't reject textfield (and derivatives) with multiple=True when
      items inside are null (treat them as empty value/string).
    * Allow empty lists for edit grid/repeating group when field is
      not required.
    * Skip validation for layout components, they never get data.
    * Ensure that empty string values for optional text fields are
      allowed (also covers derived fields).
    * Fixed validation error being returned that doesn't point to
      a particular component.
    * Fixed validation being run for form steps that are (conditionally) marked as
      "not applicable".

* [#4069] Fixed a crash in the form designer when navigating to the variables tab if you
  use any of the following registration backends: email, MS Graph (OneDrive/Sharepoint)
  or StUF-ZDS.

2.6.0 "Traiectum" (2024-03-25)
==============================

Open Forms 2.6.0 is a feature release.

.. epigraph::

   Traiectum is the name of a Roman Fort in Germania inferior, what is currently
   modern Utrecht. The remains of the fort are in the center of Utrecht.

Upgrade notes
-------------

* Ensure you upgrade to (at least) Open Forms 2.5.2 before upgrading to 2.6.

* ⚠️ The ``CSRF_TRUSTED_ORIGINS`` setting now requires items to have a scheme. E.g. if
  you specified this as ``example.com,cms.example.com``, then the value needs to be
  updated to ``https://example.com,https://cms.example.com``.

  Check (and update) your infrastructure code/configuration for this setting before
  deploying.

* The Objects API registration backend can now update the payment status after
  registering an object. For this feature to work, the minimum version of the Objects
  API is now ``v2.2`` (raised from ``v2.0``). If you don't make use of payments or don't
  store payment information in the object, you can likely keep using older versions, but
  this is at your own risk.

* The ``TWO_FACTOR_FORCE_OTP_ADMIN`` and ``TWO_FACTOR_PATCH_ADMIN`` environment variables
  are removed, you can remove them from your infrastructure configuration. Disabling MFA
  in the admin is no longer possible. Note that the OpenID Connect login backends do not
  require (additional) MFA in the admin and we've added support for hardware tokens
  (like the YubiKey) which make MFA less of a nuisance.

Major features
--------------

**📄 Objects API contract**

We completely revamped our Objects API registration backend - there is now tight
integration with the "contract" imposed by the selected object type. This makes it
much more user friendly to map form variables to properties defined in the object type.

The existing template-based approach is still available, giving you plenty of time to
convert existing forms. It is not scheduled for removal yet.

**👔 Decision engine (DMN) support**

At times, form logic can become very complex to capture all the business needs. We've
added support for evaluation of "Decision models" defined in a decision evaluation
engine, such as Camunda DMN. This provides a better user experience for the people
modelling the decisions, centralizes the definitions and gives more control to the
business, all while simplifying the form logic configuration.

Currently only Camunda 7 is supported, and using this feature requires you to have
access to a Camunda instance in your infrastructure.

**🔑 Multi-factor rework**

We've improved the login flow for staff users by making it more secure *and* removing
friction:

* users of OIDC authentication never have to provide a second factor in Open Forms
* you can now set up an automatic redirect to the OIDC-provider, saving a couple of
  clicks
* users logging in with username/password can now use hardware tokens (like YubiKey),
  as an alternative one-time-password tokens (via apps like Google/Microsoft
  Authenticator)

**🔓 Added explicit, public API endpoints**

We've explicitly divided up our API into public and private parts, and this is reflected
in the URLs. Public API endpoints can be used by CMS integrations to present lists of
available forms, for example. Public API endpoints are subject to semantic versioning,
i.e. we will not introduce breaking changes without bumping the major version.

Currently there are public endpoints for available form categories and available forms.
The existing, private, API endpoints will continue to work for the foreseeable future
to give integrations time to adapt. The performance of these endpoints is now optimized
too.

The other API endpoints are private unless documented otherwise. They are *not* subject
to our semantic versioning policy anymore, and using these is at your own risk. Changes
will continue to be documented in the release notes.

Detailed changes
----------------

The 2.6.0-alpha.0 changes are included as well, see the earlier changelog entry.

**New features**

* [#3688] Objects API registration rework

    - Added support for selecting an available object type/version in a dropdown instead
      of copy-pasting a URL.
    - The objecttype definition (JSON-schema) is processed and will be used for validation.
    - Registration configuration is specified on the "variables" tab for each available
      (built-in or user-defined) variable, where you can select the appropriate object
      type property in a dropdown.
    - Added the ability to explicitly map a file upload variable into a specific object
      property for better data quality.
    - Ensured that the legacy format is still available (100% backwards compatible).

* [#3855] Improved user experience of DMN integration

    - The available input/output parameters can now be selected in a dropdown instead of
      entering them manually.
    - Added robustness in case the DMN engine is not available.
    - Added caching of DMN evaluation results.
    - Automatically select the only option if there's only one.

* Added documentation on how to configure Camunda for DMN.
* Tweaked the dark-mode styling of WYSIWYG editors to better fit in the page.
* [#3164] Added explicit timeout fields to services so they can be different from the
  global default.
* [#3695] Improved login screen and flow

    - Allow opt-in to automatically redirect to OIDC provider.
    - Support WebAuthn (like YubiKey) hardware tokens.

* [#3885] The admin form list now keeps track of open/collapsed form categories.
* [#3957] Updated the eIDAS logo.
* [#3825] Added a well-performing public API endpoint to list available forms, returning
  only minimal information.
* [#3825] Added public API endpoint to list available form categories.
* [#3879] Added documentation on how to add services for the service fetch feature.
* [#3823] Added more extensive documentation for template filters, field regex validation
  and integrated this documentation more into the form builder.
* [#3950] Added additional values to the eHerkenning CSP-header configuration.
* [#3977] Added additional validation checks on submission completion of the configured
  formio components in form steps.
* [#4000] Deleted the 'save and add another' button in the form designer to maintain safe
  blood pressure levels for users who accidentally clicked it.

**Bugfixes**

* [#3672] Fixed the handling of object/array variable types in service fetch configuration.
* [#3890] Fixed visually hidden fields not being sent to Objects API registration backend.
* [#1052] Upgraded DigiD/eHerkenning library.
* [#3924] Fixed updating of payment status when the "registration after payment is
  received" option is enabled.
* [#3909] Fixed a crash in the form designer when you use the ZGW registration plugin
  and remove a variable that is mapped to a case property ("Zaakeigenschap").
* [#3921] Fixed not all (parent/sibling) components being available for selection in the
  form builder.
* [#3922] Fixed a crash because of invalid prefill configuration in the form builder.
* [#3958] Fixed the preview appearance of read-only components.
* [#3961] Reverted the merged KVK API services (basisprofiel, zoeken) back into separate
  configuration fields. API gateways can expose these services on different endpoints.
* [#3705] Fixed the representation of timestamps (again).
* [#3975,#3052] Fixed legacy service fetch configuration being picked over the intended
  format.
* [#3881] Fixed updating a re-usable form definition in one form causing issues in other
  forms that also use this same form definition.
* [#4022] Fix crash on registration handling of post-payment registration. The patch for
  #3924 was bugged.
* [#2827] Worked around an infinite loop when assigning the variable ``now`` to a field
  via logic.
* [#2828] Fixed a crash when assigning the variable ``today`` to a variable via logic.

**Project maintenance**

* Removed the legacy translation handling which became obsolete with the new form builder.
* [#3049] Upgraded the Django framework to version 4.2 (LTS) to guarantee future
  security and stability updates.
* Bumped dependencies to pull in their latest security/patch updates.
* Removed stale data migrations, squashed migrations and cleaned up old squashed migrations.
* [#851] Cleaned up ``DocumentenClient`` language handling.
* [#3359] Cleaned up the registration flow and plugin requirements.
* [#3735] Updated developer documentation about pre-request clients.
* [#3838] Divided the API into public and private API and their implied versioning
  policies.
* [#3718] Removed obsolete translation data store.
* [#4006] Added utility to detect KVK integration via API gateway.
* [#3931] Remove dependencies on PyOpenSSL.

2.5.4 (2024-03-19)
==================

Hotfix release to address a regression in 2.5.3

* [#4022] Fix crash on registration handling of post-payment registration. The patch for
  #3924 was bugged.

2.5.3 (2024-03-14)
==================

Bugfix release

* [#3863] Fixed the generated XML for StUF-BG requests when retrieving partners/children.
* [#3920] Fixed not being able to clear some dropdows in the new form builder (advanced
  logic, WYSIWYG content styling).
* [#3858] Fixed a race condition that would manifest during parallel file uploads,
  leading to permission errors.
* [#3864] Fixed handling of StUF-BG responses where one partner is returned.
* [#1052] Upgraded DigiD/eHerkenning library.
* [#3924] Fixed updating of payment status when the "registration after payment is
  received" option is enabled.
* [#3921] Fixed not all (parent/sibling) components being available for selection in the
  form builder.
* [#3922] Fixed a crash because of invalid prefill configuration in the form builder.
* [#3975,#3052] Fixed legacy service fetch configuration being picked over the intended
  format.
* [#3881] Fixed updating a re-usable form definition in one form causing issues in other
  forms that also use this same form definition.

2.4.6 (2024-03-14)
==================

Bugfix release

* [#3863] Fixed the generated XML for StUF-BG requests when retrieving partners/children.
* [#3858] Fixed a race condition that would manifest during parallel file uploads,
  leading to permission errors.
* [#3864] Fixed handling of StUF-BG responses where one partner is returned.
* [#1052] Upgraded DigiD/eHerkenning library.
* [#3975,#3052] Fixed legacy service fetch configuration being picked over the intended
  format.
* [#3881] Fixed updating a re-usable form definition in one form causing issues in other
  forms that also use this same form definition.

2.3.8 (2024-03-14)
==================

Bugfix release

* [#3863] Fixed the generated XML for StUF-BG requests when retrieving partners/children.
* [#3858] Fixed a race condition that would manifest during parallel file uploads,
  leading to permission errors.
* [#3975,#3052] Fixed legacy service fetch configuration being picked over the intended
  format.
* [#3881] Fixed updating a re-usable form definition in one form causing issues in other
  forms that also use this same form definition.

2.6.0-alpha.0 (2024-02-20)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

Warnings
--------

**Objects API**

The Objects API registration backend can now update the payment status after registering
an object - this depends on a version of the Objects API with the PATCH method fixes. At
the time of writing, such a version has not been released yet.

.. todo:: At release time (2.6.0), check if we need to gate this functionality behind a
   feature flag to prevent issues.

If you would like information about the payment to be sent to the Object API registration
backend when the user submits a form, you can add a ``payment`` field to the
``JSON content template`` field in the settings for the Object API registration backend.
For example, if the ``JSON content template`` was:

.. code-block::

   {
     "data": {% json_summary %},
     "type": "{{ productaanvraag_type }}",
     "bsn": "{{ variables.auth_bsn }}",
     "pdf_url": "{{ submission.pdf_url }}",
     "submission_id": "{{ submission.kenmerk }}",
     "language_code": "{{ submission.language_code }}"
   }

It could become:

.. code-block::

  {
     "data": {% json_summary %},
     "type": "{{ productaanvraag_type }}",
     "bsn": "{{ variables.auth_bsn }}",
     "pdf_url": "{{ submission.pdf_url }}",
     "submission_id": "{{ submission.kenmerk }}",
     "language_code": "{{ submission.language_code }}"
     "payment": {
         "completed": {% if payment.completed %}true{% else %}false{% endif %},
         "amount": {{ payment.amount }},
         "public_order_ids":  {{ payment.public_order_ids }}
     }
  }

**Two factor authentication**

The ``TWO_FACTOR_FORCE_OTP_ADMIN`` and ``TWO_FACTOR_PATCH_ADMIN`` environment variables
are removed. Disabling MFA in the admin is no longer possible. Note that the OpenID
Connect login backends do not require (additional) MFA in the admin and we've added
support for hardware tokens (like the YubiKey) which make MFA less of a nuisance.

Detailed changes
----------------

**New features**

* [#713] Added JSON-template support for payment status update in the Objects API.
* [#3783] Added minimal statistics for form submissions in the admin.
* [#3793] Reworked the payment reference number generation to include the submission
  reference.
* [#3680] Removed extraneous authentication plugin configuration on cosign V2 component.
* [#3688] Added plumbing for improved objects API configuration to enforce data-constracts
  through json-schema validation. This is very work-in-progress.
* [#3730] Added DMN-capabilities to our logic engine. You can now evaluate a Camunda
  decision definition and use the outputs for further form logic control.
* [#3600] Added support for mapping form variables to case properties in the ZGW API's
  registration backend.
* [#3049] Reworked the two-factor solution. You can now enforce 2FA for username/password
  accounts while not requiring this when authenticating through OpenID Connect.
* Added support for WebAuthn-compatible 2FA hardware tokens.
* [#2617] Reworked the payment flow to only enter payment mode if the price is not zero.
* [#3727] Added validation for minimum/maximum number of checked options in the selectboxes
  component.
* [#3853] Added support for the KVK-Zoeken API v2.0. V1 is deprecated and will be shut
  down this year.

**Bugfixes**

* [#3809] Fixed a crash when viewing a non-existing submission via the admin.
* [#3616] Fixed broken PDF template for appointment data.
* [#3774] Fixed dark-mode support in new form builder.
* [#3382] Fixed translation warnings for date and datetime placeholders in the form
  builder.
* [CVE-2024-24771] Fixed (non-exploitable) multi-factor authentication weakness.
* [#3623] Fixed some OpenID Connect compatibility issues with certain providers.
* [#3863] Fixed the generated XML for StUF-BG requests when retrieving partners/children.
* [#3864] Fixed handling of StUF-BG responses where one partner is returned.
* [#3858] Fixed a race condition that would manifest during parallel file uploads,
  leading to permission errors.
* [#3822] Fixed searching in form versions admin.

**Project maintenance**

* Updated to Python 3.10+ typing syntax
* Update contributing documentation regarding type annotations.
* [#3806] Added email field to customer detail fields for demo appointments plugin.
* Updated CI action versions to use the latest NodeJS version.
* [#3798] Removed unused ``get_absolute_url`` in the form definition model.
* Updated to black version 2024.
* [#3049] More preparations to upgrade to Django 4.2 LTS.
* [#3616] Added docker-compose setup for testing SDK embedding.
* [#3709] Improved documentation for embedding forms.
* [#3239] Removed logic rule evaluation logging as it was incomplete and not very usable.
* Cleaned up some test helpers after moving them into libraries.
* Upgraded external librariesto their newest (security) releases.


2.5.2 (2024-02-06)
==================

Bugfix release

This release addresses a security weakness. We believe there was no way to actually
exploit it.

* [CVE-2024-24771] Fixed (non-exploitable) multi-factor authentication weakness.
* [SDK#642] Fixed DigiD error message via SDK patch release.
* [#3774] Fixed dark-mode support in new form builder.
* Upgraded dependencies to their latest available security releases.

2.4.5 (2024-02-06)
==================

Bugfix release

This release addresses a security weakness. We believe there was no way to actually
exploit it.

* [CVE-2024-24771] Fixed (non-exploitable) multi-factor authentication weakness.
* [SDK#642] Fixed DigiD error message via SDK patch release.
* Upgraded dependencies to their latest available security releases.

2.3.7 (2024-02-06)
==================

Bugfix release

This release addresses a security weakness. We believe there was no way to actually
exploit it.

* [CVE-2024-24771] Fixed (non-exploitable) multi-factor authentication weakness.
* [SDK#642] Fixed DigiD error message via SDK patch release.
* Upgraded dependencies to their latest available security releases.

2.5.1 (2024-01-30)
==================

Hotfix release to address an upgrade problem.

* Included missing UI code for GovMetric analytics.
* Fixed a broken migration preventing upgrading to 2.4.x and newer.
* [#3616] Fixed broken PDF template for appointment data.

2.4.4 (2024-01-30)
==================

Hotfix release to address an upgrade problem.

* Bump packages to their latest security releases
* [#3616] Fixed broken PDF template for appointment data.
* Fixed a broken migration preventing upgrading to 2.4.x.

2.5.0 "Noaberschap" (2024-01-24)
================================

Open Forms 2.5.0 is a feature release.

.. epigraph::

   Noaberschap of naoberschap bunt de gezamenleke noabers in ne kleine sociale,
   oaverweagend agrarische samenleaving. Binnen den noaberschap besteet de noaberplicht.
   Dit höldt de verplichting in, dat de noabers mekare bi-j mot stoan in road en doad as
   dat neudig is. Et begrip is veural bekand in den Achterhook, Twente Salland en
   Drenthe, moar i-j kunt et eavenens in et westen van Duutslaand vinden (Graofschap
   Bentheim en umgeaving).

   -- definition in Achterhoeks, Dutch dialect

Upgrade procedure
-----------------

* ⚠️ Ensure you upgrade to Open Forms 2.4.0 before upgrading to the 2.5 release series.

* ⚠️ Please review the instructions in the documentation under **Installation** >
  **Upgrade details to Open Forms 2.5.0** before and during upgrading.

* We recommend running the ``bin/report_component_problems.py`` script to diagnose any
  problems in existing form definitions. These will be patched up during the upgrade,
  but it's good to know which form definitions will be touched in case something looks
  odd.

* Existing instances need to enable the new formio builder feature flag in the admin
  configuration.

Major features
--------------

**🏗️ Form builder rework**

We have taken lessons from the past into account and decided to implement our form
builder from the ground up so that we are not limited anymore by third party limitations.

The new form builder looks visually (mostly) the same, but the interface is a bit snappier
and much more accessible. Most importantly for us, it's now easier to change and extend
functionalities.

There are some further implementation details that have not been fully replaced yet,
but those do not affect the available functionality. We'll keep improving on this topic!

**🌐 Translation improvements**

Doing the form builder rework was crucial to be able to improve on our translation
machinery of form field components. We've resolved the issues with translations in
fieldsets, repeating groups and columns *and* translations are now directly tied to
the component/field they apply too, making everything much more intuitive.

Additionally, in the translations table we are now able to provide more context to help
translators in providing the correct literals.

**💰 Payment flow rework**

Before this version, we would always register the submission in the configured backend
and then send an update when payment is fulfilled. Now, you can configure to only
perform the registration after payment is completed.

On top of that, we've updated the UI to make it more obvious to the end user that payment
is required.

**🏡 BRK integration**

We've added support for the Basiregistratie Kadaster Haal Centraal API. You can now
validate that the authenticated user (DigiD) is "zaakgerechtigd" for the property at
a given address (postcode + number and suffixes).

**🧵 Embedding rework**

We have overhauled our embedding and redirect flows between backend and frontend. This
should now properly support all features when using hash based routing. Please let us
know if you run into any edge cases that don't work as expected yet!

**🧩 More NL Design System components**

We've restructured page-scaffolding to make use of NL Design System components, which
makes your themes more reusable and portable accross different applications.


Detailed changes
----------------

The 2.5.0-alpha.0 changes are included as well, see the earlier changelog entry.

**New features**

* Form designer

    * [#3712] Replaced the form builder with our own implementation. The feature flag is
      now on by default for new instances. Existing instances need to toggle this.
    * [#2958] Converted component translations to the new format used by the new form
      builder.
    * [#3607] Added a new component type ``addressNL`` to integrate with the BRK.
    * [#2710] Added "initials" to StufBG prefill options.

* Registration plugins

    * [#3601], ZGW plugin: you can now register (part of) the submission data in the
      Objects API, and it will be related to the created Zaak.

      ⚠️ This requires a compatible version of the Objects API, see the
      `upstream issue <https://github.com/maykinmedia/objects-api/issues/355>`_.

* [#3726] Reworked the payment flow to make it more obvious that payment is required.
* [#3707] group synchronization/mapping can now be disabled with OIDC SSO.
* [#3201] Updated more language to be B1-level.
* [#3702] Simplified language in co-sign emails.
* [#180] Added support for GovMetric analytics.
* [#3779] Updated the menu structure following user feedback about the form building
  experience.
* [#3731] Added support for "protocollering" headers when using the BRP Personen
  Bevragen API.

**Bugfixes**

* [#3656] Fixed incorrect DigiD error messages being shown when using OIDC-based plugins.
* [#3705] Fixed the ``__str__`` datetime representation of submissions to take the timezone
  into account.
* [#3692] Fixed crash when using OIDC DigiD login while logged into the admin interface.
* [#3704] Fixed the family members component not retrieving the partners when using
  StUF-BG as data source.
* Fixed 'none' value in CSP configugration.
* [#3744] Fixed conditionally marking a postcode component as required/optional.
* [#3743] Fixed a crash in the admin with bad ZGW API configuration.
* [#3778] Ensured that the ``content`` component label is consistently *not* displayed
  anywhere.
* [#3755] Fixed date/datetime fields clearing invalid values rather than showing a
  validation error.

**Project maintenance**

* [#3626] Added end-to-end tests for submission resume flows.
* [#3694] Upgraded to React 18.
* Removed some development tooling which was superceded by Storybook.
* Added documentation for a DigiD/eHerkenning LoA error and its solution.
* Refactored the utilities for dealing with JSON templates.
* Removed (EOL) 2.1.x from CI configuration.
* [#2958] Added formio component Hypothesis search strategies.
* Upgraded to the latest ``drf-spectacular`` version.
* [#3049] Replaced the admin array widget with another library.
* Upgraded libraries to have their latest security fixes.
* Improved documentation for the release process.
* Documented typing philosophy in contributing guidelines.
* Modernized dev-tooling configuration (isort, flake8, coverage).
* Squashed forms and config app migrations.

2.4.3 (2024-01-12)
==================

Periodic bugfix release

* [#3656] Fixed incorrect DigiD error messages being shown when using OIDC-based plugins.
* [#3692] Fixed crash when using OIDC DigiD login while logged into the admin interface.
* [#3744] Fixed conditionally marking a postcode component as required/optional.

  .. note:: We cannot automatically fix existing logic rules. For affected forms, you
     can remove and re-add the logic rule action to modify the 'required' state.

* [#3704] Fixed the family members component not retrieving the partners when using
  StUF-BG as data source.
* [#2710] Added missing initials (voorletters) prefill option for StUF-BG plugin.
* Fixed failing docs build by disabling/changing some link checks.

2.3.6 (2024-01-12)
==================

Periodic bugfix release

* [#3656] Fixed incorrect DigiD error messages being shown when using OIDC-based plugins.
* [#3692] Fixed crash when using OIDC DigiD login while logged into the admin interface.
* [#3744] Fixed conditionally marking a postcode component as required/optional.

  .. note:: We cannot automatically fix existing logic rules. For affected forms, you
     can remove and re-add the logic rule action to modify the 'required' state.

* [#3704] Fixed the family members component not retrieving the partners when using
  StUF-BG as data source.
* [#2710] Added missing initials (voorletters) prefill option for StUF-BG plugin.
* Fixed failing docs build by disabling/changing some link checks.

2.5.0-alpha.0 (2023-12-15)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

Upgrade procedure
-----------------

⚠️ Ensure you upgrade to Open Forms 2.4.0 before upgrading to the 2.5 release series.

⚠️ Please review the instructions in the documentation under **Installation** >
**Upgrade details to Open Forms 2.5.0** before and during upgrading.

Detailed changes
----------------

**New features**

* [#3178] Replaced more custom components with NL Design System components for improved
  themeing. You can now use design tokens for:

  * ``utrecht-document``
  * ``utrecht-page``
  * ``utrecht-page-header``
  * ``utrecht-page-footer``
  * ``utrecht-page-content``

* [#3573] Added support for sending geo (Point2D) coordinates as GeoJSON to the Objects API.
* Added CSP ``object-src`` directive to settings (preventing embedding by default).
* Upgraded the version of the new (experimental) form builder.
* [#3559] Added support for Piwik PRO Tag Manager as an alternative for Piwik PRO Analytics.
* [#3403] Added support for multiple themes. You can now configure a default theme and
  specify form-specific styles to apply.
* [#3649] Improved support for different vendors of the Documenten API implementation.
* [#3651] The suffix to a field label for optional fields now uses simpler language.
* [#3005] Submission processing can now be deferred until payment is completed (when
  relevant).

**Bugfixes**

* [#3362] We've reworked and fixed the flow to redirect from the backend back to the
  form in the frontend, fixing the issues with hash-based routing in the process.
  Resuming forms after pausing, cosign flows... should now all work properly when you
  use hash-based routing.
* [#3548] Fixed not being able to remove the MS Graph service/registration configuration.
* [#3604] Fixed a regression in the Objects API and ZGW API's registration backends. The
  required ``Content-Crs`` request header was no longer sent in outgoing requests after
  the API client refactoring.
* [#3625] Fixed crashes during StUF response parsing when certain ``nil`` values are
  present.
* Updated the CSP ``frame-ancestors`` directive to match the ``X-Frame-Options``
  configuration.
* [#3605] Fixed unintended number localization in StUF/SOAP messages.
* [#3613] Fixed submission resume flow not sending the user through the authentication
  flow again when they authenticated for forms that have optional authentication. This
  unfortunately resulted in hashed BSNs being sent to registration backends, which we
  can not recover/translate back to the plain-text values.
* [#3641] Fixed the DigiD/eHerkenning authentication flows aborting when the user
  changes connection/IP address.
* [#3647] Fixed a backend (logic check) crash when non-parsable time, date or datetime
  values are passed. The values are now ignored as if nothing was submitted.

**Project maintenance**

* Deleted dead/unused CSS.
* Upgraded dependencies having new patch/security releases.
* [#3620] Upgraded storybook to v7.
* Updated the Docker image workflow, OS packages are now upgraded during the build and
  image vulnerability scanning added to the CI pipeline.
* Fixed generic type hinting of registry.
* [#3558] Refactored the CSP setting generation from analytics configuration mechanism
  to be more resilient.
* Ensured that we send tracebacks to Sentry on DigiD errors.
* Refactored card component usage to use the component from the SDK.
* Upgraded WeasyPrint for PDF generation.
* [#3049] Replaced deprecated calls to ``ugettext*``.
* Fixed a deprecation warning when using new-style middlewares.
* [#3005] Simplified/refactored the task orchestration for submission processing.
* Require OF to be minimum of 2.4 before upgrading to 2.5.
* Removed original source migrations that were squashed in Open Forms 2.4.
* Replaced some (vendored) code with their equivalent library versions.
* Upgraded the NodeJS version from v16 to v20.

2.3.5 (2023-12-12)
==================

Periodic bugfix release

* [#3625] Fixed crashes during StUF response parsing when certain ``nil`` values are
  present.
* [#3605] Fixed unintended number localization in StUF/SOAP messages.
* [#3613] Fixed submission resume flow not sending the user through the authentication
  flow again when they authenticated for forms that have optional authentication. This
  unfortunately resulted in hashed BSNs being sent to registration backends, which we
  can not recover/translate back to the plain-text values.

2.4.2 (2023-12-08)
==================

Periodic bugfix release

* [#3625] Fixed crashes during StUF response parsing when certain ``nil`` values are
  present.
* Updated CSP ``frame-ancestors`` directive to be consistent with the ``X-Frame-Options``
  configuration.
* [#3605] Fixed unintended number localization in StUF/SOAP messages.
* [#3613] Fixed submission resume flow not sending the user through the authentication
  flow again when they authenticated for forms that have optional authentication. This
  unfortunately resulted in hashed BSNs being sent to registration backends, which we
  can not recover/translate back to the plain-text values.
* [#3647] Fixed a backend (logic check) crash when non-parsable time, date or datetime
  values are passed. The values are now ignored as if nothing was submitted.

2.4.1 (2023-11-14)
==================

Hotfix release

* [#3604] Fixed a regression in the Objects API and ZGW API's registration backends. The
  required ``Content-Crs`` request header was no longer sent in outgoing requests after
  the API client refactoring.

2.3.4 (2023-11-09)
==================

Hotfix release

* Upgraded bundled SDK version
* [#3585] Fixed a race condition when trying to send emails that haven't been saved to
  the DB yet.
* [#3580] Fixed incorrect attributes being sent in ZWG registration backend when
  creating the rol/betrokkene.

2.4.0 "Miffy" (2023-11-09)
==========================

Open Forms 2.4.0 is a feature release.

.. epigraph::

   **Miffy** (or "Nijntje" in Dutch) is a fictional rabbit appearing in a series of
   picture books authored by Dick Bruna. Both are famous Utrecht citizens. You can find
   Miffy in a number of places, such as the "Nijntje Pleintje" (Miffy Square) and a set
   of pedestrian traffic lights in the shape of the rabbit in the city center.

Upgrade procedure
-----------------

⚠️ Ensure you upgrade to Open Forms 2.3.0 before upgrading to the 2.4 release series.

To keep the codebase maintainable and follow best pratices, we've done some considerable
cleanups in the code that may require some special attention. We've collected the
details for this release in a separate documentation page.

⚠️ Please review the instructions in the documentation under **Installation** >
**Upgrade details to Open Forms 2.4.0** before and during upgrading.

Major features
--------------

***️ (Experimental) Suwinet plugin**

We now support retrieving data for a logged in user (with BSN) through Suwinet. This
feature is in experimental/preview mode, so we rely on your feedback on how to further
develop and improve this.

**📅 Appointments**

Our Qmatic appointments plugin now also supports multiple customer/multiple products
flows, matching the JCC feature set.

**🧩 More NL Design System components**

We continue bridging the gap between our custom UI-components and available NL DS
components. Our buttons and links now no longer require OF-specific tokens and we've
removed a whole bunch of styling code that got in the way when building your own theme.

More will come in the future!

Detailed changes
----------------

The 2.4.0-alpha.0 changes are included as well, see the earlier changelog entry.

**New features**

* Form designer

    * [#586] Added support for Suwinet as a prefill plugin.
    * [#3188] Added better error feedback when adding form steps to a form with
      duplicate keys.
    * [#3351] The family members component can now be used to retrieve partner
      information instead of only the children (you can select children, partners or
      both).
    * [#2953] Added support for durations between dates in JSON-logic.
    * [#2952] Form steps can now initially be non-applicable and dynamically be made
      applicable.

* [#3499] Accepting/declining cookies in the notice now no longer refreshes the page.
* [#3477] Added CSP ``form-action`` directives, generated via the DigiD/eHerkenning
  and Ogone configuration.
* [#3524] The behaviour when retrieving family members who don't have a BSN is now
  consistent and well-defined.
* [#3566] Replaced custom buttons with utrecht-button components.

**Bugfixes**

* [#3527] Duplicated form steps in a form are now blocked at the database level.
* [#3448] Fixed emails not being sent with a subject line > 70 characters.
* [#3448] Fixed a performance issue when upgrading the underlying email sending library
  if you have many (queued) emails.
* [#2629] Fixed array variable inputs in the form designer.
* [#3491] Fixed slowdown in the form designer when created a new or loading an existing
  form when many reusable form definitions exist.
* [#3557] Fixed a bug that would not display the available document types when
  configuring the file upload component.
* [#3553] Fixed a crash when validating a ZWG registration backend when no default
  ZGW API group is set.
* [#3537] Fixed validator plugin list endpoint to properly converting camelCase params
  into snake_case.
* [#3467] Fixed crashes when importing/copying forms with ``null`` in the prefill
  configuration.
* [#3580] Fixed incorrect attributes being sent in ZWG registration backend when
  creating the rol/betrokkene.

**Project maintenance**

* Upgraded various dependencies with the most recent (security) releases.
* [#2958] Started the rework for form field-level translations, the backend can now
  handle present and future formats.
* [#3489] All API client usage is updated to a new library, which should lead to a
  better developer experience and make it easier to get better performance when making
  (multiple) API calls.
* Bumped pip-tools for latest pip compatibility.
* [#3531] Added a custom migration operation class for formio component transformations.
* [#3531] The time component now stores ``minTime``/``maxTime`` in the ``validate``
  namespace.
* Contributed a number of library extensions back to the library itself.
* Squashed the variables app migrations.
* [#2958] Upgraded (experimental) new form builder to 0.8.0, which uses the new
  translations format.
* Fixed test suite which didn't take DST into account.
* [#3449] Documented the (new) co-sign flow.

2.3.3 (2023-10-30)
==================

Periodic bugfix release

* [#3279] Added robustness to the admin that retrieves data from external APIs.
* [#3527] Added duplicated form steps detection script and added it to the upgrade check
  configuration.
* [#3448] Applied mail-queue library patches ahead of their patch release.
* [#3557] Fixed a bug that would not display the available document types when
  configuring the file upload component.
* Bumped dependencies to their latest security fixes.

2.4.0-alpha.0 (2023-10-02)
==========================

Upgrade procedure
-----------------

.. warning::

    Ensure you upgrade to Open Forms 2.3.0 before upgrading to the 2.4 release series.


Detailed changes
----------------

**New features**

* [#3185] Added Haal Centraal: HR prefill plugin to official extensions build.
* [#3051] You can now schedule activation/deactivation of forms.
* [#1884] Added more fine-grained custom errors for time field components.
* More fields irrelevant to appointment forms are now hidden in the form designer.
* [#3456] Implemented multi-product and multi-customer appointments for Qmatic.
* [#3413] Improved UX by including direct hyperlinks to the form in co-sign emails (
  admins can disable this behaviour).
* [#3328] Qmatic appointments plugin now support mTLS.
* [#3481] JSON-data sent to the Objects API can now optionally be HTML-escaped for when
  downstream systems fail to do so.
* [#2688] Service-fetch response data is now cached & timeouts are configurable on the
  configuration.
* [#3443] You can now provide custom validation error messages for date fields
* [#3402] Added tracing information to outgoing emails so we can report on failures.
* [#3402] Added email digest to report (potential) observed problems, like email
  delivery failures.

**Bugfixes**

* [#3139] Fixed form designers/admins not being able to start forms in maintenance mode.
* Fixed the version of openapi-generator.
* Bumped to latest Django patch release.
* [#3447] Fixed flash of unstyled form visible during DigiD/eHerkenning login flow.
* [#3445] Fixed not being able to enter more decimals for latitude/longitude in the map
  component configuration.
* [#3423] Fixed import crash with forms using service fetch.
* [#3420] Fixed styling of cookie overview page.
* [#3378] Fixed copying forms with logic that triggers from a particular step crashing
  the logic tab.
* [#3470] Fixed form names with slashes breaking submission generation.
* [#3437] Improved robustness of outgoing request logging solution.
* Included latest SDK bugfix release.
* [#3393] Fixed duplicated form field label in eHerkenning configuration.
* [#3375] Fixed translation warnings being shown for optional empty fields.
* [#3187] Fixed UI displaying re-usable form definitions that are already in the form.
* [#3422] Fixed logic tab crashes when variables/fields are deleted and added a generic
  error boundary with troubleshooting information.
* [#3308] Fixed new installations having all-English default messages for translatable
  default content.
* [#3492] Fixed help text referring to old context variable.
* [#3437] Made request logging solution more robust to prevent weird crashes.
* [#3279] Added robustness to admin pages making requests to external hosts.

**Project maintenance**

* [#3190] Added end-to-end tests for DigiD and eHerkenning authentication flows with a
  real broker.
* Mentioned extension requirements file in docs.
* [#3416] Refactored rendering of appointment data  in confirmation PDF.
* [#3389] Stopped building test images, instead use symlinks or git submodules in your
  (CI) pipeline.
* Updated appointments documentation.
* Moved service factory to more general purpose location.
* [#3421] Updated local infrastructure for form exports and clarified language to manage
  import expectations.
* Updated version of internal experimental new formio-builder.
* Prevent upgrades from < 2.3.0 to 2.4.
* Squashed *a lot* of migrations.
* Removed dead/obsolete "default BSN/KVK" configuration - no code used this anymore since
  a while.
* [#3328] Initial rework of API clients to generically support mTLS and other
  connection parameters.
* Fixed test cleanup for self-signed certs support, causing flaky tests.
* Moved around a bunch of testing utilities to more appropriate directories.
* [#3489] Refactored all API-client usage into common interface.
* Fixed tests failing with dev-settings.
* Bumped dependencies with security releases.

2.3.2 (2023-09-29)
==================

Hotfix for WebKit based browsers

* [#3511] Fixed user input "flickering" in forms with certain (backend) logic on Safari
  & other WebKit based browsers (via SDK patch).

2.3.1 (2023-09-25)
==================

Periodic bugfix release

* [#3139] Fixed form designers/admins not being able to start forms in maintenance mode.
* Fixed the version of openapi-generator.
* Bumped to latest Django patch release.
* [#3447] Fixed flash of unstyled form visible during DigiD/eHerkenning login flow.
* [#3445] Fixed not being able to enter more decimals for latitude/longitude in the map
  component configuration.
* [#3423] Fixed import crash with forms using service fetch.
* [#3420] Fixed styling of cookie overview page.
* [#3378] Fixed copying forms with logic that triggers from a particular step crashing
  the logic tab.
* [#3470] Fixed form names with slashes breaking submission generation.
* [#3437] Improved robustness of outgoing request logging solution.
* Included latest SDK bugfix release.

2.3.0 "Cruquius" (2023-08-24)
=============================

.. epigraph::

   **Cruquius** is a village in Haarlemmermeer. It gets its name from Nicolaas Kruik, one
   of the many promotors of a plan to pump the Haarlem lake (Haarlemmermeer) dry.

   -- "Cruquius, Netherlands", Wikipedia

Upgrade procedure
-----------------

Ensure that your current version of Open Forms is at least version 2.1.3 before
upgrading.

Version 2.3.0 does not contain breaking changes and therefore upgrading should be
straightforward.

Major features
--------------

**📅 Appointments**

We are introducing an all-new, optimized appointment booking flow, allowing you to make
appointments for multiple products and/or people in one go! The new user interface
focuses on better accessibility and a more fluent experience, while increasing the
flexibility for the organization managing appointments.

The JCC plugin is fully updated, while the Qmatic plugin is compatible. Please get in
touch if you use Qmatic and wish to use the multi-product flow.

The old appointment flow is now deprecated and will be removed in Open Forms 3.0.

**🧐 Prefill with DigiD Machtigen/Bewindvoering**

Open Forms supports logging in with your own credentials on behalf of someone else (
you are then the authorisee, while "someone else" is the authoriser). Up until now,
prefill could only retrieve the data of the authoriser. Starting now, you can select
from which role the data should be prefilled, so you can retrieve this for all roles
at the same time!

**🗺️ Map component**

We've improved the map component and/or geo integration:

* Configure the initial coordinates and zoom level of the map instead of the center of
  the Netherlands. This is even configurable *per component*, which can be useful if your
  organization has multiple districts, for example.
* Users now have a search box to look up their/an address, which autocompletes the
  addresses from the BAG. Clicking a suggestion places the marker on the coordinates of
  the selected address.
* Clicking a location in the map looks up the nearest address and displays this for
  extra confirmation.

**🧠 Dynamic registration backends**

Registration backends are now dynamic - you can configure one, none or multiple
registration backends on a form and use logic to decide which to use. If no or only one
backend is configured, the existing behaviour applies. However, if you have multiple
possible backends, you must create a logic rule to select the appropriate backend.

Detailed changes
----------------

The 2.3.0-alpha.0 changes are included as well, see the earlier changelog entry.

**New features**

* [#2174] Added geo-search (using the Kadaster Locatieserver by default) for the map
  component.
* [#2017] The form step slug is now moved from the form definition to the form step
  itself, allowing you to use the same slug for a step in different forms.
* [#3332] Use the JCC configuration for the latest available appointment date.
* [#3332] When selecting a product, this choice is now taken into account to populate
  the list of available additional products.
* [#3321] Added support for new appointment flow to confirmation emails.
* [#1884] Added custom error message support for invalid times.
* [#3203, #3372] Added an additional checkbox for truth declaration before submitting a
  form, in addition to the privacy policy. You can now also configure these requirements
  per-form instead of only the global configuration.
* [#1889] Added the ``current_year`` static variable.
* [#3179] You can now use logic to select an appropriate registration backend.
* [#3299] Added Qmatic support for the new appointments.

**Bugfixes**

* [#3223] Fixed some content translations not being properly translated when copying a form.
* [#3144] Fixed file download links being absent in registration emails when the file
  upload is nested inside a group.
* [#3278] Fixed a crash when the DigiD provider does not provide a sector code in the
  SAML Artifact. We now assume it's BSN (as opposed to sofinummer).
* [#3084] Fixed ``inp.heeftAlsKinderen`` missing in scope of StUF-BG request.
* [#3302] Fixed race condition causing uploaded images not be resized.
* [#3332] Ensured that naive, localized appointment times are sent to JCC.
* [#3309] Added a missing automatic appointment configuration upgrade.
* Fixed broken inline images in outgoing emails and loss of additional parameters.
* [#3322] Fixed the cancel-appointment flow for new appointments.
* [#3327] Fixed the backend markup and styling of radio fields.
* [#3319] Fixed forms possibly sending a DigiD SAML request without assurance level due
  to misconfiguration.
* Fixed passing querystring parameter to service fetch.
* [#3277] Added a workaround to use form variable values containing spaces in templates.
* [#3292] Fixed dark mode suffixes in the form builder.
* [#3286] Fixed data normalization for customer details in new appointments.
* [#3368] Fixed a crash when empty values are returned from StUF-BG.
* [#3310] Fixed alignment issue in confirmation PDF for accepted privacy policy statement.

**Project maintenance**

* Changed the fail-fast behaviour of the end-to-end tests to reduce the flakiness impact.
* We now build Docker images based on the latest available Python patch release again.
* [#3242] Added more profiling to investigate test flakiness.
* Upgraded the container base image from Debian Bullseye to Bookworm.
* [#3127] Rework developer tooling to generate code from an API specification.
* Fixed JQ documentation URL for sorting.
* Bump dependencies reported to have vulnerabilities (via @dependabot).
* Improved typing of plugins and plugin registries.
* Fixed incorrect Authentication header in the Objects API documentation.
* [#3049] Upgraded more libraries to prepare for Django 4.2

2.3.0-alpha.0 (2023-07-24)
==========================

Upgrade procedure
-----------------

Ensure that your current version of Open Forms is at least version 2.1.3 before
upgrading.

Version 2.3.0 does not contain breaking changes and therefore upgrading should be
straightforward.

Major features
--------------

**📅 Appointments**

We are introducing an all-new, optimized appointment booking flow, allowing you to make
appointments for multiple products and/or people in one go! The new user interface
focuses on better accessibility and a more fluent experience, while increasing the
flexibility for the organization managing appointments.

This feature is currently in preview and only JCC is operational - but we're aiming to
finish support for QMatic in the full release.

**🧐 Prefill with DigiD Machtigen/Bewindvoering**

Open Forms supports logging in with your own credentials on behalf of someone else (
you are then the authorisee, while "someone else" is the authoriser). Up until now,
prefill could only retrieve the data of the authoriser. Starting now, you can select
from which role the data should be prefilled, so you can retrieve this for all roles
at the same time!

**🗺️ Map component**

We are giving some the geo integration/map component some well-deserved love. The first
steps allow configuring the maps to your organization by setting a default initial
center and zoom level (global defaults), rather than initializing on the middle of the
Netherlands. You can even customize these defaults on a *per component* basis, for
example when your organization handles multiple districts.

More is coming!

Detailed changes
----------------

**New features**

* [#2471] Added a new appointments flow next to the existing one.

  .. note::

     You can opt-in to this flow by enabling the feature flag in the global
     configuration and then mark a form as being an "appointment form". Currently
     only JCC is fully implemented. Note that the entire feature has "preview"
     status and is only suitable for testing (with known issues).

  * [#3193] Added API endpoint to retrieve required customer fields meta-information.

    * Implemented retrieving this for JCC plugin.
    * Implemented configuring the fields in the admin for QMatic.

  * Added appointment meta-information to form detail enpdoint.
  * Validate the input data against the configured plugin.
  * Appointment submissions now have their own data model and entry in the admin.
  * Extended existing endpoints to support retrieving locations/dates/times for
    multiple products.
  * Defining an appointment form disables/clears the irrelevant form designer aspects.
  * [#3275] Added support for multi-product appointments in JCC.

* [#3215] Support prefilling data of the authorisee with DigiD machtigen and
  eHerkenning Bewindvoering.

* Form designer

  * [#1508] Added hidden option for legacy cosign component.
  * [#1882] Added minimum/maximum value options to the currency component.
  * [#1892] Added tooltips to (relevant) form components in the designer.
  * [#1890] Added support for upload file name templating, you can now add pre- and
    suffixes.
  * [#2175] You can now configure the default zoom level and initial map center for the
    map component, with a global default.
  * [#3045] You can now provide a suffix for number components, e.g. to hint about the
    expected unit.

* [#3238] The StUF-ZDS registration backend now has well-defined behaviour for
  non-primitive variable values, including user-defined variables.

**Bugfixes**

* Fixed testing availability of OIDC auth endpoint with HEAD requests (now uses GET).
* [#3195] Fixed hardcoded ``productaanvraag_type`` in default Objects API template to
  use configuration option.
* [#3182] Fixed importing forms from before 2.2.0 due to missing
  ``{% cosign_information %}`` tag in confirmation email templates.
* [#3211] Fixed CSP violation in Piwik Pro analytics script, causing no analytics to be
  tracked.
* [#3161] Fixed not being able to reset form-specific data removal settings to the
  empty value so that the global configuration is used again.
* [#3219] Fixed saved uploads not being deleted when the user goes back to the file and
  removes the upload again.
* Fixed CI builds (bump PyYAML, docs build).
* [#3258] Fixed labels for Haal Centraal prefill attributes.
* Fixed the broken Token Exchange extension (pre-request plugins) in the Haal Centraal
  plugin.
* [#3130] Fixed a crash when copying form-definitions with very long names.
* [#3166] Fixed Haal Centraal plugin configuration test.
*

**Project maintenance**

* Bumped dependencies to get their latest security fixes.
* Removed MacOS CI job due to broken system-level dependencies.
* Added utility to profile code with ``cProfile``.
* Sped up tests by pre-loading the OAS schema and worked on other flakiness issues.
* [#3242] Set up a CI profile for hypothesis.
* [#586] Extracted the SOAP service configuration from the StUF app into its own app.
* [#3189] Refactored authentication plugins ``provides_auth`` datatypes.
* [#3049] Upgraded a number of dependencies in preparation for Django 4.2:

  * django-autoslug
  * django-yubin
  * django-axes
  * django-colorfield
  * django-hijack
  * django-redis
  * django-treebeard
  * django-filter
  * elastic-apm
  * sentry-sdk
  * django-solo
  * django-timeline-logger
  * drf-jsonschema-serializer
  * django-admin-index
  * django-tinymce
  * djangorestframework-camel-case


.. note:: We only provided best-effort developer environment support for the MacOS
   platform. This is now costing too much resources as there are no actual MacOS users
   in the development team.
