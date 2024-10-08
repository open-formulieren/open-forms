=========
Changelog
=========

2.6.15 (2024-10-08)
===================

Final bugfix release in the `2.6.x` series.

* [#4602] Fixed missing Dutch translation for minimum required checked items error
  message in the selectboxes component.
* [#4658] Fixed certain variants of ZIP files not passing validation on Windows.
* [#4652] Fixed misaligned validation errors in the form designer UI.

2.6.14 (2024-09-02)
===================

Periodic bugfix release

* [#4597] Revert message for not-filled-in-fields in confirmation PDF back to
  just empty space.
* Fixed processing of empty file upload components in the Objects API registration plugin.

2.6.13 (2024-07-29)
===================

Bugfix release.

* [#4191] Fixed the datatype of ``vestiging`` field in ZGW registration
  rollen/betrokkenen.
* [#4334] Fixed the email registration plugin not sending a payment-received
  email when "wait for payment to register" is enabled. This behaviour is to ensure that
  financial departments can always be informed of payment administration.
* [#4502] Fixed a problem where the registration-backend routing logic is not
  calculated again after pausing and resuming a submission.
* [#4560] Fixed more PDF generation overlapping content issues. The layout no
  longer uses two columns, but just stacks the labels and answers below each other since
  a compromise was not feasible.
* [#4519] Fixed form variable dropdowns taking up too much horizontal space.
* Backend checks of form component validation configuration are mandatory. All
  components support the same set of validation mechanism in frontend and backend.

2.6.12 (2024-07-12)
===================

Bugfix release to address PDF generation issue.

* [#4191] Fixed missing required ``aoaIdentificatie`` field to ZGW registration.
* [#4450] Fixed submission PDF rows overlapping when labels wrap onto another line.
* Updated dependencies to their latest security patches.

2.6.11 (2024-06-20)
===================

Hotfix for payment integration in Objects API

* [#4425] Fixed the wrong price being sent to the Objects API when multiple payment
  attempts are made.
* [#4425] Fixed incorrectly marking failed/non-completed payment attempts as registered
  in the registration backend.
* [#4425] Added missing (audit) logging for payments started from the confirmation
  email link.

2.6.10 (2024-06-19)
===================

Hotfix fixing a regression in the PDF generation.

* [#4403] Fixed broken submission PDF layout when empty values are present.
* [#4409] Updated language used for payment amount in submission PDF.

2.6.9 (2024-06-14)
==================

Bugfix release fixing some issues (still) in 2.6.8

* [#4338] Fixed prefill for StUF-BG with SOAP 1.2 not properly extracting attributes.
* [#4390] Fixed regression introduced by #4368 that would break template variables in
  hyperlinks inside WYSIWYG content.

2.6.8 (2024-06-14)
==================

Bugfix release

* [#4255] Fixed a performance issue in the confirmation PDF generation when large
  blocks of text are rendered.
* [#4241] Fixed some backend validation being skipped when there is component key
  overlap with layout components (like fieldsets and columns).
* [#4368] Fixed URLs to the same domain being broken in the WYSIWYG editors.
* [#4377] Added support for pre-request context/extensions in BRK client
  implementation.
* [#4363] Fixed option descriptions not being translated for radio and selectboxes
  components.
* [#4362] Fixed a crash in the form designer when a textfield/textarea allows multiple
  values in forms with translations enabled.

2.6.7 (2024-05-22)
==================

Bugfix release

* [#3807] Made the co-sign request email template configurable.
* [#4302] Made co-sign data (date and co-sign attribute) available in the Objects API registration.

2.6.6 (2024-05-13)
==================

Bugfix release

* [#4146] Fixed SOAP timeout not being used for Stuf-ZDS client.
* [#4205] The CSP ``form-action`` directive now allows any ``https:`` target,
  to avoid errors on eHerkenning login redirects.
* [#4269] Fixed DMN integration for real-world decision definitions.

2.6.5 (2024-04-24)
==================

Bugfix release

* [#4165] Require a cookie consent group for analytics
* [#4115] Add new source ID and secure GUID
* [#4202] Fix Objects API registration v2 crash with hidden fields

2.6.5-beta.0 (2024-04-17)
=========================

Bugfix beta release

* [#4186] Fix for "client-side logic" in the formio-builder cleared existing values.
* [#4187] Selectboxes/radio with dynamic options are considered invalid when submitting the form.
* [#3964] Toggling visibility with frontend logic and number/currency components leads to fields being emptied.

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

Bugfix release following feedback on 2.6.2

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

2.2.10 (2024-02-27)
===================

Final release in the 2.2.x series.

* [#3863] Fixed the generated XML for StUF-BG requests when retrieving partners/children.
* [#3858] Fixed a race condition that would manifest during parallel file uploads,
  leading to permission errors.

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

2.2.9 (2024-02-06)
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

2.2.8 (2024-01-12)
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

2.1.11 (2023-12-28)
===================

Final release in the 2.1.x series.

Upgrade to Open Forms 2.2 or higher to continue receiving support/bugfixes.

* [#3656] Fixed an incorrect DigiD error message being shown with OIDC authentication
  plugins.
* [#3692] Fixed a crash when cancelling DigiD authentication while logged in as admin
  user.

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

2.2.7 (2023-12-12)
==================

Periodic bugfix release

* [#3625] Fixed crashes during StUF response parsing when certain ``nil`` values are
  present.
* [#3605] Fixed unintended number localization in StUF/SOAP messages.
* [#3613] Fixed submission resume flow not sending the user through the authentication
  flow again when they authenticated for forms that have optional authentication. This
  unfortunately resulted in hashed BSNs being sent to registration backends, which we
  can not recover/translate back to the plain-text values.

2.1.10 (2023-12-12)
===================

Periodic bugfix release

* [#3625] Fixed crashes during StUF response parsing when certain ``nil`` values are
  present.
* [#3605] Fixed unintended number localization in StUF/SOAP messages.
* [#3613] Fixed submission resume flow not sending the user through the authentication
  flow again when they authenticated for forms that have optional authentication. This
  unfortunately resulted in hashed BSNs being sent to registration backends, which we
  can not recover/translate back to the plain-text values.

**Update payment status for Object API**

If you would like information about the payment to be sent to the Object API registration backend when the user submits
a form, you can add a ``payment`` field to the ``JSON content template`` field in the settings for the Object API
registration backend. For example, if the ``JSON content template`` was:

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

2.2.6 (2023-11-09)
==================

Hotfix release

* Upgraded bundled SDK version
* [#3580] Fixed incorrect attributes being sent in ZWG registration backend when
  creating the rol/betrokkene.

2.1.9 (2023-11-09)
==================

Hotfix release

* Upgraded bundled SDK version
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

2.2.5 (2023-10-30)
==================

Periodic bugfix release

* [#3279] Added robustness to the admin that retrieves data from external APIs.
* Bumped dependencies to their latest security fixes.

2.1.8 (2023-10-30)
==================

Periodic bugfix release

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

2.2.4 (2023-09-29)
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

2.2.3 (2023-09-25)
==================

Periodic bugfix release

* [#3139] Fixed form designers/admins not being able to start forms in maintenance mode.
* Fixed the version of openapi-generator.
* Bumped to latest Django patch release.
* [#3447] Fixed flash of unstyled form visible during DigiD/eHerkenning login flow.
* [#3423] Fixed import crash with forms using service fetch.
* [#3420] Fixed styling of cookie overview page.
* [#3378] Fixed copying forms with logic that triggers from a particular step crashing
  the logic tab.
* [#3470] Fixed form names with slashes breaking submission generation.
* [#3437] Improved robustness of outgoing request logging solution.
* Included latest SDK bugfix release.

2.1.7 (2023-09-25)
==================

Periodic bugfix release

* [#3139] Fixed form designers/admins not being able to start forms in maintenance mode.
* Fixed the version of openapi-generator.
* Bumped to latest Django patch release.
* [#3447] Fixed flash of unstyled form visible during DigiD/eHerkenning login flow.
* [#3420] Fixed styling of cookie overview page.
* [#3378] Fixed copying forms with logic that triggers from a particular step crashing
  the logic tab.
* [#3470] Fixed form names with slashes breaking submission generation.
* Included latest SDK bugfix release.

2.0.11 (2023-09-25)
===================

Final bugfix release in the ``2.0.x`` series.

* [#3139] Fixed form designers/admins not being able to start forms in maintenance mode.
* Fixed the version of openapi-generator.
* Bumped to latest Django patch release.
* [#3378] Fixed copying forms with logic that triggers from a particular step crashing
  the logic tab.
* [#3470] Fixed form names with slashes breaking submission generation.
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

2.2.2 (2023-08-24)
==================

Periodic bugfix release

* [#3319] Fixed forms possibly sending a DigiD SAML request without assurance level due
  to misconfiguration.
* [#3358] Fixed display of appointment time in correct timezone.
* [#3368] Fixed a crash when empty values are returned from StUF-BG.
* Fixed JQ documentation URL for sorting.

2.1.6 (2023-08-24)
==================

Periodic bugfix release

* [#3319] Fixed forms possibly sending a DigiD SAML request without assurance level due
  to misconfiguration.
* [#3358] Fixed display of appointment time in correct timezone.
* [#3368] Fixed a crash when empty values are returned from StUF-BG.

2.0.10 (2023-08-24)
===================

Periodic bugfix release

* [#3358] Fixed display of appointment time in correct timezone.
* [#3368] Fixed a crash when empty values are returned from StUF-BG.

2.2.1 (2023-07-26)
==================

Periodic bugfix release

* Fixed testing availability of OIDC auth endpoint with HEAD requests (now uses GET).
* [#3195] Fixed hardcoded ``productaanvraag_type`` in default Objects API template to
  use configuration option.
* [#3182] Fixed importing forms from before 2.2.0 due to missing
  ``{% cosign_information %}`` tag in confirmation email templates.
* [#3216] Fixed setting the Piwik Pro SiteID parameter in the analytics scripts.
* [#3211] Fixed CSP violation in Piwik Pro analytics script, causing no analytics to be
  tracked.
* [#3161] Fixed not being able to reset form-specific data removal settings to the
  empty value so that the global configuration is used again.
* [#3219] Fixed saved uploads not being deleted when the user goes back to the file and
  removes the upload again.
* Fixed CI builds (bump PyYAML, docs build).
* [#3258] Fixed labels for Haal Centraal prefill attributes.
* [#3301] Fixed crash on DigiD authentication with brokers not returning sectoral codes.
* [#3144] Fixed missing links to uploads in the registration e-mails when the field is
  inside a container (fieldset, repeating group).
* [#3302] Fixed an issue causing uploaded images not to be resized.
* [#3084] Fixed ``inp.heeftAlsKinderen`` missing from certain StUF-BG requests.
* Bumped dependencies to get their latest security fixes
* Fixed the broken Token Exchange extension (pre-request plugins) in the Haal Centraal
  plugin.
* Removed MacOS CI job due to broken system-level dependencies.

.. note:: We only provided best-effort developer environment support for the MacOS
   platform. This is now costing too much resources as there are no actual MacOS users
   in the development team.

2.1.5 (2023-07-26)
==================

Periodic bugfix release

* [#3132] Fixed replacing form steps in the designer with another step having overlapping
  variable names.
* Fixed testing availability of OIDC auth endpoint with HEAD requests (now uses GET).
* [#3216] Fixed setting the Piwik Pro SiteID parameter in the analytics scripts.
* [#3211] Fixed CSP violation in Piwik Pro analytics script, causing no analytics to be
  tracked.
* [#3161] Fixed not being able to reset form-specific data removal settings to the
  empty value so that the global configuration is used again.
* [#3219] Fixed saved uploads not being deleted when the user goes back to the file and
  removes the upload again.
* Fixed CI builds (bump PyYAML, docs build).
* [#3258] Fixed labels for Haal Centraal prefill attributes.
* [#3301] Fixed crash on DigiD authentication with brokers not returning sectoral codes.
* [#3144] Fixed missing links to uploads in the registration e-mails when the field is
  inside a container (fieldset, repeating group).
* [#3302] Fixed an issue causing uploaded images not to be resized.
* [#3084] Fixed ``inp.heeftAlsKinderen`` missing from certain StUF-BG requests.
* Bumped dependencies to get their latest security fixes

2.0.9 (2023-07-26)
==================

Periodic bugfix release

* [#3132] Fixed replacing form steps in the designer with another step having overlapping
  variable names.
* [#3216] Fixed setting the Piwik Pro SiteID parameter in the analytics scripts.
* [#3211] Fixed CSP violation in Piwik Pro analytics script, causing no analytics to be
  tracked.
* [#3161] Fixed not being able to reset form-specific data removal settings to the
  empty value so that the global configuration is used again.
* [#3219] Fixed saved uploads not being deleted when the user goes back to the file and
  removes the upload again.
* Fixed CI builds (bump PyYAML, docs build).
* [#3258] Fixed labels for Haal Centraal prefill attributes.
* [#3301] Fixed crash on DigiD authentication with brokers not returning sectoral codes.
* [#3144] Fixed missing links to uploads in the registration e-mails when the field is
  inside a container (fieldset, repeating group).
* [#3302] Fixed an issue causing uploaded images not to be resized.
* [#3084] Fixed ``inp.heeftAlsKinderen`` missing from certain StUF-BG requests.
* Bumped dependencies to include latest security fixes.

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


2.2.0 "Èspelès" (2023-06-26)
============================

.. epigraph::

   **Èspelès**, The Hague dialect for "Ijspaleis" or "ice palace" is the nickname for
   its Town Hall.

   De bijnaam IJspaleis dankt het aan de veelvuldig gebruikte witte kleur aan exterieur en interieur.

   -- "Stadhuis van Den Haag", Wikiwand

Upgrade procedure
-----------------

Ensure that your current version of Open Forms is at least version 2.1.3 before
upgrading.

Version 2.2.0 does not contain breaking changes and therefore upgrading should be
straightforward.

Major features
--------------

**🧑 Haal Centraal BRP Personen v2 support**

In addition to v1.3, Open Forms now also supports v2 of the
`BRP Personen APIs <https://github.com/BRP-API/Haal-Centraal-BRP-bevragen>`_. You can
specify the relevant version in the admin interface for your environment.

**🔏 Reworked co-signing flow**

We've introduced a new co-signing flow, compatible with authentication gateways!

The primary person (the one filling out the form) now provides the email address of the
co-signer, whom receives the request for co-signing. After the co-signer completed their
duties, the submission is passed to the registration plugin and processed as usual.

The "old" co-sign component is still functional, but deprecated.

**🛂 Level Of Assurance (LOA) per form**

DigiD, eHerkenning and eIDAS support different levels of assurance that the logged in
user is actually the person they claim to be. Higher levels require additional
authentication requirements and/or factors.

It is now possible to configure on a per-form basis what the authentication LOA must
be, giving you stronger guarantees in your form about the authenticated person or company.

**🗃️ Reworked Objects API registration backend**

We've reworked the Objects API registration backend - our fixed "ProductAanvraag" format
has been replaced with a configurable template format, so you can decide on a per-form
basis exactly what the JSON-data structure is to be sent to the Objects API.

All form variables are available in these templates, so this gives you enormous
flexibility in which data you register for your processes.

**💄 Better theming tools**

We've added a graphical tool to edit `design token <https://nldesignsystem.nl/handboek/design-tokens/>`_
values in our admin interface. Before, you'd have to edit raw JSON-code and piece together
all bits, but now there is a handy reference of available tokens AND you can change their
values to suit your visual identity in great detail.

**🔌 Retrieve data from external registrations (preview)**

An iteration of 2.1's "Retrieve data from external registrations" feature - we now
provide a nicer user experience to configure how to retrieve data. This moves the
feature into "preview" status - you still need to opt-in to the feature but it should
be stable and we would like feedback from users!

.. note::
    Possible breaking change

    The interpolation format has changed from single bracket to double bracket
    interpolation to be consistent with interpolation in other places. We have added
    an automatic migration, but it's possible not everything is caught.

    If you have ``{some_variable}``, change this to ``{{ some_variable }}``.



Detailed changes
----------------

**New features**

* Retrieve data from external registrations (aka service fetch):

  * [#2680] Added API endpoint to expose available services for service fetch.
  * [#2661, #2693, #2834, #2835] Added user friendly UI to configure "external data retrieval".
  * [#2681] Added logic logging of service fetch to allow better debugging of form logic.
  * [#2694] Updated interpolation format to double bracket, making it possible to use
    Django template engine filters.

* [#1530] Introduced a new co-sign component

  * Implemented a new flow for co-signing so that the co-signer receives a request via
    email.
  * The submission is only registered when co-signing is completed.
  * Ensure the co-signer also receives the confirmation email.
  * The existing component is deprecated.

* Background task processing

  * [#2927] Added Celery worker monitoring tooling (for devops/infra).
  * [#3068] Added soft and hard task timeout settings for background workers.

* [#2826] The form builder now validates the format of dates in logic rules.
* [#2789] The submission pause/save modal text is now configurable.
* [#2872] The registration flow is reworked to have a pre-registration step, e.g. to
  reserve a "zaaknummer" before creating the case.
* [#2872] The email registration plugin can now include the registration reference and
  any other submission variables.
* [#2872] You can now override subject and body templates for the registration email
* [#2957] Added editor to simplify theming an instance instead of editing JSON.
* [#2444] It's now possible to hide non-applicable steps in the progress indicator
  rather than greying them out.
* [#2946] It's now possible to overwrite the confirmation email subject and content
  templates individually.
* [#2343] Added option to hide the label of a repeating group.
* [#3004] You can now disable form pausing.
* [#1879] Relevant validation plugins are now filtered per component type in the form
  designer.
* [#3031] Increased the size of Objects API registration plugin configuration form fields.
* [#2918] Added alternative Formio builder implementation, opt-in via a feature flag.
* [#1424] The form submission reference is now included in the confirmation PDF.
* [#2845] Added option to include content component in submission summary.
* [#2809] Made the link title for downloading the submission report configurable.
* [#2762] Added (opt-in) logging for outgoing requests to assist with configuration
  troubleshooting.
* [#2859] You can now configure multiple sets of ZGW APIs and configure per form where
  documents need to be uploaded.
* [#2606] Added support for Haal Centraal BRP Personen v2.
* [#2852] The Objects API registration backend data is now a template, configurable per
  form.
* [#2860] Level of assurance for DigiD and eHerkenning/eIDAS is now configurable per form.

**Bugfixes**

* [#2804] Fixed the "static variables" not being available in confirmation template
  rendering.
* [#2821] Fixed broken "Map" component configuration screen.
* [#2819] Fixed the key and translations of the password field not automatically
  updating with entered content (label and other translatable fields).
* [#2785] Fixed attribute hashing on submission suspend
* [#2822] Fixed date components being interpreted as datetimes instead of dates.
* Fixed misalignment for file upload preview in form builder.
* [#2820] Fixed translations not registering initially when adding a component to a new
  form step.
* [#2838] Fixed hidden selectboxes field triggering premature validation of required fields.
* [#2791] Fixed long words overflowing in the confirmation PDF.
* [#2842] Fixed analytics CSP-integration resulting in a misconfigured policy.
* [#2851] Fixed importing a form while the admin UI is set to English resulting in
  incorrect form translation mappings.
* [#2850] Fixed a crash in the AVG log viewer when certain log records of deleted
  submissions are displayed.
* [#2844] Fixed validation errors for submission confirmation email not being displayed
  in the form designer.
* Fixed unique component key suffix generation on a newly added component.
* [#2874] Fixed "repeating group" component group label not being translated.
* [#2888] Fixed a crash when using file fields and hidden repeating groups at the same
  time
* [#2888] Fixed a crash when using file fields and repeating groups with numbers inside
* [#2889] Fix the focus jumps of the content component in the admin by re-implement the
  component translations machinery.
* [#2911] Make validation of .heic and .heif files more lenient.
* [#2893] A minimal fix to prevent crashes of the celery task logging the evaluation of
  logic rules.
* [#2942] Fixed "undefined" being displayed in the co-signing component configuration.
* [#2945] Fixed logic rule variables inadvertedly being cleared when adding a new
  user defined variable
* [#2947] Added missing translatable error messages for number components.
* [#2877] Fixed admin crash on misconfigured ZGW services.
* [#2900] Fixed inconsistent frontend logic involving checkboxes.
* [#2716] Added missing co-sign identifier (BSN) to PDF submission report.
* [#2849] Restored ability to import forms using form logic in the pre-2.0 format.
* [#2632] Fixed crash during submission data pruning when submissions point to form
  steps that have been deleted
* [#2980] Fixed file upload component not using config overwrites when registering
  with the objects API backend.
* [#2983] Fixed broken StUF-ZDS registration for some vendors due to bad refactor
* [#2977] Fixed StUF postcode not being uppercase.
* [#2963] Fixed global configuration templates being reset to their default values.
* [#3007] Fixed worfklows where < 2.1 form exports are imported and edited in the admin.
* [#2875] Fixed another SiteImprove analytics bug where only the path was sent instead
  of the full URL.
* [#1959] Fixed invalid link to resume form after pausing and resuming multiple times.
* [#3025] Fixed resuming a form redirecting to an invalid URL.
* [#2895] Fixed WYSIWYG colors missing when filling out a form while logged in as staff user.
* [#3015] Fixed invalid URLs being generated to resume the form from WYSIWYG content.
* [#3040] Fixed file-upload validation errors being user-unfriendly.
* [#2970] Fixed design token being ignored in confirmation and suspension emails.
* [#2808] Fixed filenames in upload validation errors overflowing.
* [#2651] Fixed analytics cookies receiving incorrect domain information after enabling
  the provider via the admin.
* [#2879] Fixed the available zaaktypen not refreshing the admin when the catalogi API
  is changed.
* [#3097] Fixed invalid phone numbers example in validation error messages.
* [#3123] Added support for deploying Open Forms on a subpath (e.g. ``/formulieren``).
* [#3012] Fixed select, radio and checboxes options not being translated in the UI.
* [#3070] Fixed the confirmation email template not being copied along when copying a form.
* Fixed Matomo not using the configured Site ID correctly.
* [#3114] Fixed the "next" button not becoming active if you're not logged in as admin user.
* [#3132] Fixed replacing form steps in the designer with another step having overlapping
  variable names.

**Documentation**

* Improved Storybook documentation in the backend.
* Add instruction for Postgres 15 DB initialization (with docker-compose).
* [#2362] Documented known Ogone payment simulator limitation.
* Added more details to the release flow and backporting documentation.
* Documented the possible use of soft hyphens in the form name.
* [#2908] Documented limitations of import/export for forms with service fetch config.
* Added a note on refactor and small changes for contributors.
* [#2940] Improved SDK embedding configuration documentation.
* Documented solution for "IDP not found" DigiD error.
* [#2884] Documented how to set up service fetch.

**Project maintenance**

* Added management command to check component usage for usage analytics.
* Ignore coverage on type checking branches.
* [#2814] Added additional robustness tests for possible glom crashes.
* Removed postcss-selector-lint.
* Add 2.1.x release series to Docker Hub generation config
* Add 2.2.x release series to Docker Hub generation config
* Deprecated the password field as it has no real-world usage.
* Bumped a number of dependencies following @dependabot security alerts.
* Started preparing the upgrade to Django 4.2 LTS.
* Added tests for and refined intended behaviour of ``AllOrNoneRequiredFieldsValidator``.
* Added tests for ``ModelValidator``.
* [#3016] Fixed the MacOS CI build.
* Removed the 1.1.x series from supported versions.
* Support sufficiently modern browsers, reducing the JS bundle sizes a bit.
* [#2999] Fixed broken test isolation.
* [#2784] Introduced and refactored code to use ``FormioDate`` interface.
* Tests are now also run in reverse order in CI to catch test isolation problems.

2.1.4 (2023-06-21)
==================

Periodic bugfix release

* [#1959] Fixed invalid link to resume form after pausing and resuming multiple times.
* [#3025] Fixed resuming a form redirecting to an invalid URL.
* [#3015] Fixed invalid URLs being generated to resume the form from WYSIWYG content.
* [#2927] Added Celery worker monitoring tooling (for devops/infra).
* [#3068] Added soft and hard task timeout settings for background workers.
* [#3077] Use public (instead of private) form name for ``form_name`` variable in templates.
* [#3012] Fixed select, radio and checboxes options not being translated in the UI.
* [#3136] Fixed wrong Site ID being used for Matomo analytics.
* [#3114] Fixed the "next" button not becoming active if you're not logged in as admin user.
* [#3103] Fixed DigiD/eHerkenning-metadata missing the XML declaration.

2.0.8 (2023-06-21)
==================

Periodic bugfix release

* [#3015] Fixed invalid URLs being generated to resume the form from WYSIWYG content.
* [#2927] Added Celery worker monitoring tooling (for devops/infra).
* [#3068] Added soft and hard task timeout settings for background workers.
* [#3077] Use public (instead of private) form name for ``form_name`` variable in templates.
* [#3136] Fixed wrong Site ID being used for Matomo analytics.
* [#3117] Fixed a crash in migrations preventing upgrading from older versions.
* [#3114] Fixed the "next" button not becoming active if you're not logged in as admin user.
* [#3128] Fixed hidden (file) components triggering validation too early.

.. note::

    The fix for premature validation triggering (#3128) only applies to new
    components/forms.

    To fix this for existing file components, it's recommended to remove and re-add the
    component in the form.

2.0.7 (2023-05-01)
==================

Periodic bugfix release

* [#1959] Fixed invalid link to resume form after pausing and resuming multiple times.
* [#3007] Fixed worfklows where < 2.1 form exports are imported and edited in the admin.

2.1.3 (2023-04-19)
==================

Hotfix - 2.1.2 unfortunately broke saving forms from previous minor version exports

* [#2877] Backported admin crash on misconfigured ZGW services.
* [#3007] Fixed worfklows where < 2.1 form exports are imported and edited in the admin.
* [#2875] Fixed SiteImprove analytics integration (for real now)
* [#2895] Fixed WYSIWYG colors missing when filling out a form while logged in as staff user.

2.1.2 (2023-04-18)
==================

Periodic bugfix release

* [#2947] Added missing translatable error messages for number components
* [#2908] Documented limitations of import/export for forms with service fetch config
* [#2900] Fixed inconsistent frontend logic involving checkboxes
* [#2632] Fixed crash during submission data pruning when submissions point to form
  steps that have been deleted
* [#2849] Restored ability to import forms using form logic in the pre-2.0 format
* [#2983] Fixed broken StUF-ZDS registration for some vendors due to bad refactor
* [#2963] Fixed global configuration templates being reset to their default values
* [#2977] Fixed StUF postcode not being uppercase
* Updated the bundled SDK version to 1.3.2
* [#2980] Fixed file upload component not using config overwrites when registering
  with the objects API backend.

2.0.6 (2023-04-17)
==================

Periodic bugfix release

Note that there is a manual intervention below if you make use of analytics providers
integration.

* [#2791] Fixed long words overflowing in the confirmation PDF.
* [#2838] Fixed hidden selectboxes triggering validation of required fields too early
* [#2850] Fixed a crash in the AVG log viewer when certain log records of deleted
  submissions are displayed.
* [#2842] Fixed the Content Security Policy breaking when enabling analytics provider
  configurations
* [#2888] Fixed a crash when using file fields and hidden repeating groups at the same
  time
* [#2888] Fixed a crash when using file fields and repeating groups with numbers inside
* [#2945] Fixed logic rule variables inadvertedly being cleared when adding a new
  user defined variable
* Fixed mutatiesoort when doing StUF ``UpdateZaak`` calls
* [#2716] Added missing co-sign identifier (BSN) to PDF submission report
* [#2900] Fixed inconsistent frontend logic involving checkboxes
* [#2632] Fixed crash during submission data pruning when submissions point to form
  steps that have been deleted
* [#2977] Fixed StUF postcode not being uppercase
* [#2849] Restored ability to import forms using form logic in the pre-2.0 format
* Updated the bundled SDK version to 1.2.8
* CI no longer installs the codecov package from PyPI (obsolete)


.. warning:: Manual intervention required if analytics tools are enabled

   When enabling analytics tools, CSP directives were automatically added to the admin
   under  **Configuratie** > **CSP settings**. The directive
   ``connect-src <domain of the analytic tool>`` was causing forms to no longer load.

   In order to fix this issue:

   1. Go to  **Configuratie** > **CSP settings**
   2. Delete any directive that is not ``default-src``, for example ``connect-src``, ``script-src``...
   3. If not present, add a directive ``default-src <domain of the analytic tool>``

1.1.11 (2023-04-17)
===================

This release marks the end-of-life (EOL) of the 1.1.x series per our versioning policy.

**Bugfixes**

* [#2791] Fixed long words overflowing in the confirmation PDF.
* [#2850] Fixed a crash in the AVG log viewer when certain log records of deleted
  submissions are displayed.
* Fixed mutatiesoort when doing StUF ``UpdateZaak`` calls
* [#2977] Fixed StUF postcode not being uppercase
* Updated the bundled SDK version to 1.1.4

**Project maintenance**

* CI no longer installs the codecov package from PyPI (obsolete)
* Ignored deleted branch in changelog during docs link checking

2.1.1 (2023-03-31)
==================

Periodic maintenance release

* [#2945] Prevent the addition of user defined variables from breaking the logic rules.
* [#2893] A minimal fix to prevent crashes of the celery task logging the evaluation of logic rules.
* Upgrade of the SDK version
* [#2911] Make validation of .heic and .heif files more lenient.
* [#2889] Fix the focus jumps of the content component in the admin by re-implement the component translations machinery.
* [#2888] Change the validation of BSN components from 'on change' to 'on blur'.
* [#2888] Fix uploading documents inside a repeating group when a number component is also present in the repeating group.
* [#2888] Fix uploading documents when there is a hidden repeating group.
* Change the type of mutation from "T" to "W" when making Zaak update calls in the StUF registration backend.
* A note was added to the documentation on how to use soft hyphens when configuring form or form step names.


2.1.0 "Gers" (2023-03-14)
=========================

.. epigraph::

   **Gers** *[Gers]• Gaaf/mooi/leuk/geweldig/tof/heel goed*

   -- Rotterdams Woordenboek

Upgrade procedure
-----------------

Ensure that your current version of Open Forms is at least version 2.0.2 before
upgrading.

Version 2.1.0 does not contain breaking changes and therefore upgrading should be
straightforward.

Major features
--------------

A quick summary of the new features in version 2.1 compared to 2.0.

**🌐 Multilingual support**

You can now enter content translations for supported languages (NL/EN) and enable
language selection on a per-form basis. End-users can then pick their preferred language
while filling out a form, defaulting to the browser preferences.

The submission language is registered as metadata in registration backends, and assets
like the confirmation PDF are rendered in the preferred language.

Contact us to add support for additional languages, if desired.

**♿️ Accessibility improvements**

We've scrutinized the markup to find accessibility issues and made big steps in fixing
them. Using Open Forms with a screen reader or other assistive technology should now be
a more pleasant experience. We continue making improvements in this department!

Additionally, it's now possible to specify custom error messages for form components
instead of relying on the default, generic messages.

Finally, the form designer now comes with presets for a number of common form fields,
which provide the appropriate autocomplete configuration.

**🛂 Organization member authentication (OIDC)**

Forms can now be set up for organization member authentication (via OpenID Connect) so
that your employees can start submissions for them.

This functionality is useful for internal forms that should not be filled out by
non-employees, or for employees filling out forms on behalf of a customer. In the latter
case, all the necessary meta-information is registered alongside the form submission
itself.

**💄 Further integration with NL Design System**

We are increasingly adapting the principles and community components under the NL Design
System umbrella, which exposes more and more controls to organizations for themeing Open
Forms to their brand/identity.

**💫 Dynamic options for choice-fields**

You can now use variables as the source of choice options for dropdowns, radio and
checboxes components. Combined with logic, this means you can make these components
dependent on earlier inputs.

**⚗️ Retrieve data from external registrations [Experimental]**

Query data from an external registration/JSON-service based on user input, process the
returned data and subsequently use it in your forms, for example as dynamic dropdown
options!

We're very excited about this feature, but the UX and implementation are not
fully polished yet which is why it is not yet enabled by default.

**🦠 Added support for virus scanning**

We now support (opt-in) virus scanning with `ClamAV <https://www.clamav.net/>`_. Files
uploaded by end-users are passed through the virus scan before they are saved in
Open Forms.

Detailed changes
----------------

Please review the changelog entries for the release candidate and alpha versions of
2.1.0. The changes listed below are compared to the release candidate ``2.1.0-rc.0``.

**Bugfixes**

* [#2804] Fixed the "static variables" not being available in confirmation template
  rendering.
* [#2821] Fixed broken "Map" component configuration screen.
* [#2822] Fixed date components being interpreted as datetimes instead of dates.
* [#2819] Fixed the key and translations of the password field not automatically
  updating with entered content (label and other translatable fields).
* [#2820] Fixed translations not registering initially when adding a component to a new
  form step.
* [#2791] Fixed long words overflowing in the confirmation PDF.
* [#2850] Fixed a crash in the AVG log viewer when certain log records of deleted
  submissions are displayed.
* [#2842] Fixed analytics CSP-integration resulting in a misconfigured policy.
* [#2851] Fixed importing a form while the admin UI is set to English resulting in
  incorrect form translation mappings.
* [#2838] Fixed hidden selectboxes field triggering premature validation of required fields.
* [#2874] Fixed "repeating group" component group label not being translated.

2.0.5 (2023-03-07)
==================

Hotfix release

* [#2804] Fixed static variables not being included in template context for submission
  confirmation template.
* [#2400] Clean up cached execution state

2.1.0-rc.0 (2023-03-03)
=======================

We are proud to announce a release candidate of Open Forms 2.1!

This release candidate has focused on stability issues compared to the previous alpha
version and includes some new experimental features.

Detailed changes
----------------

**New features**

* Multilingual support

  * [#2493] Display warnings for missing translations in the form designer when form
    translations are enabled.
  * [#2685] Staff users can now configure their admin UI language preferences.

* [#2623] Improved implementation of dynamic options (select, radio, checkboxes).
* [#2663] Added ClamAV cirus scanning support. This is disabled by default - you need to
  deploy a ClamAV service instance and then enable it in the Open Forms configuration.
* [#2653] Allow more configuration in the ZGW registration plugin:

  * Specify a default bronorganisatie RSIN + allow overriding it per file-component.
  * Specify a default documentation vertrouwelijkheidaanduiding + allow overriding it
    per file-component.
  * File upload components can now specify the document title and auteur fields.

* Data retrieval from external registrations

  * [#2454] Implemented retrieving and processing data from external JSON services.
  * [#2753] Added opt-in feature flag.

 [#2786] Improved phone number validation error messages.

**Bugfixes**

* [#2601] Disabled autocomplete for username/password in (services) admin.
* [#2635] Fixed component key not being updated anymore with label changes.
* [#2643] Fixed description generation for empty ``var`` operations and the ``map``
  operation.
* [#2641] Relaxed email URL stripping for subdomains of allow-listed domains.
* [#2549] Fixed cookie banner overlapping footer links
* [#2673] Fixed mobile styling (spacing + location of language selection component).
* [#2676] Fixed more mobile styling spacing issues (header/footer, logo).
* [#2636] Fixed a number of bugs that appeared in the previous version

  * Fixed saving user defined variables with a falsy initial value.
  * Fixed broken display of logic rule "trigger from step" selected choice.

* Fixed the API forcing the default language in the admin when a form does not have
  translations enabled.
* [#2646] Fixed "privacy policy acceptance" not being recorded/validated in the backend.
* [#2699] Fixed uploads in repeating groups not being registered in the backend.
* [#2682] Fixed some date/datetime component issues

  * Fixed editor options not refreshing when selecting a validation method.
  * Fixed validation min/max value tab settings not having any effect.

* [#2709] Fixed (bandaid) inconsistent dynamic product price logic
* [#2671] Fixed QR code not being readable in dark mode.
* [#2742] Fixed the key of file upload components not updating with the label.
* [#2721] Updated django-simple-certmanager version
* [#2734] Validate that component keys inside repeating groups cannot duplicate existing
  form keys.
* [#2096] Prevented users from being able to bypass steps blocked by logic.
* [#2781] Fixed the data-clearing/data extraction of (hidden) nested components.
* [#2770] Fixed formio unique component key generation to take into account keys from
  other steps.
* [#2805] Fixed form builder crash when enabling translations and adding a new form step.
* [#2798] Fixed select/radio/checkboxes option values not being derived from labels
  anymore.
* [#2769] Fixed date/datetime components relative validation settings not being
  registered correctly.

**Documentation**

* Improved SharePoint registration backend documentation.
* [#2619] Added Storybook documentation for the backend JS/CSS components.
* [#2481] Updated the screenshots of the translations UI in the manual.
* [#2696] Updated documentation about dynamic form options and unsupported JSON-logic
  operators.
* [#2735] Documented functionalities that don't work (yet) in repeating groups.
* Added patch release changelog entries from stable branches.
* Documented Django changelist component in Storybook.
* Reorganized the component groups in Storybook.

**Project maintenance**

* Bumped dependencies to their latest (security) releases
* [#2471] Add preparations for new appointments flow.
* [#388, #965] Refactored the StUF client implementations.
* Updated Github Actions workflows to use composite actions for duplicated steps.
* [#2657] Replaced Selenium end-to-end tests with Playwright.
* [#2665] Update coverage reporting configuration to exclude test files themselves.
* Fixed ``generate_minimal_setup`` factory trait by adding label to generated components.
* [#2700] Replaced the last Github dependencies with PyPI versions of them.
* Enabled opt-in to use X-Forwarded-Host headers [infrastructure].
* [#2711] Moved ``openforms.utils.api`` utilities to the ``openforms.api`` package.
* [#2748] Pinned the project to Python 3.10.9 due to a CPython regression.
* [#2712] Replaced django-choices usage with core Django equivalents.
* Fixed a test failing between 00:00-01:00 AM.


2.0.4 (2023-02-28)
==================

Periodic maintenance release

* [#2607] Fixed crash when selecting trigger-from-step in logic editor
* Fixed crash when importing forms
* [#2699] Fixed file uploads not resolving when inside fieldsets/repeating groups
* Stopped link checking JCC links in CI since we're actively being blocked
* [#2671] Fixed QR code background in dark mode
* [#2709] Fixed (bandaid) inconsistent dynamic product price logic
* [#2724] Ensure backport of negative-numbers (#1351) is correctly included
* [#2734] Added bandaid fix for non-unique keys inside repeating groups
* Updated to SDK 1.2.6
* [#2717] Fixed crash on StUF-ZDS when updating the payment status
* [#2781] Fixed clearing the value of hidden components with a nested key (``nested.key``).
* [#2759] Fixed handling of file uploads with a nested key (``nested.key``).


1.1.10 (2023-02-28)
===================

Bugfix release with some fixes from newer versions applied.

* [#2520] Fixed bug in mimetype validation for ``application/ms-word`` (and similar) files
* Bump required SDK version
* [#2717] Fixed crash on StUF-ZDS when updating the payment status
* [#2671] Fixed QR code background in dark mode
* [#2709] Fixed (bandaid) inconsistent dynamic product price logic


2.1.0-alpha.2 (2023-02-01)
==========================

Next 2.1.0 preview version.

This alpha release of Open Forms 2.1 is likely to be the last one before the beta
version(s) and associated feature freeze.

Detailed changes
----------------

**New features**

* Multilingual support

  * [#2478] Implemented UI/UX for form designers to manage component-level translations.
  * [#2390] PDF reports and confirmation emails are now rendered in the submission
    language.
  * [#2286] Ensured that the API endpoints for the SDK return the translations
    according to the active language.
  * [#2546] Added language metadata to MS Graph, Objects API, ZGW API, StUF-ZDS and
    email registration backends.
  * [#1242] The form designer component edit form and preview are now properly localized.

* Accessibility improvements

  * [#2268] Added support for the autocomplete property in the form designer. This
    comes with a set of pre-configured form fields having the correct autocomplete
    attribute set out of the box.
  * [#2490] Login logo objects in the API now contain meta-information about their
    appearance for appropriate focus-styling in the SDK.
  * [#2534] Added support for custom errors per-component in the form designer,
    including translation options.
  * [#2273] Improved accessibility of error messages for required fields.

* Registration plugins

  * [#2494] Added ability to add identifying person details in StUF-ZDS registration
    even if the person did not authenticate via DigiD (or similar).
  * [#2511] Added more options for the Microsoft Graph registration plugin, such as
    base folder path, drive ID and year/month/day interpolation.

* [#1902] Added support for sourcing choice widget values from variables.
* [#2504] Improved performance in form designer initial load when you have many
  forms/form definitions.
* [#2450] Added "description" field to logic rules in the form designer. The description
  can be specified manually or is automatically generated from the logic expression.
* [#2143] Added option to exclude confirmation page content from PDF.
* [#2539] Added support for ``.msg`` and ``.dwg`` file uploads.
* [security#20] Use fully qualified URLs in analytics config for maximum CSP strictness.
* [#2591] Added rate limits to API endpoints for pausing and submitting forms.
* [#2557] Implemented comparing date and times with the ``now +- someDelta`` variable.

**Bugfixes**

* [#2520] Fixed MIME type validation error for ``.doc`` files.
* [#2577] Fixed MIME type validation regression for OpenOffice and dwg files.
* [#2377] Fixed link-hover design token not being applied consistently.
* [#2519] Only perform upgrade checks when not upgrading between patch versions.
* [#2120] Fixed layout components inadvertedly getting the ``validate.required=true``
  configuration.
* [#2396] Fixed auto-login setting not resetting when the authentication option is
  removed from the form.
* Add missing ``br`` tag to allowed WYSIWYG tag list.
* [#2550] Removed ``role=img`` from logo in header.
* [#2525] Fixed clearing the date component min/max validation configuration.
* [#2538] Normalize radio components to always be string type.
* [#2576] Fix crash on components with prefill attribute names > 50 chars.
* [#2012] Fixed missing ``script-src`` CSP directive for SiteImprove analytics.
* [#2541] Fixed a crash in the logic editor when changing the key of selectboxes
  components.
* [#2587] Fixed inadvertedly HTML escaping while templating out email subjects.
* [#2599] Fixed typo in registration constants.
* [#2607] Fixed crash in logic editor when specifying a "trigger-from" step.
* [#2581] Fixed bug in logic where dates and datetimes were being mixed.

**Documentation**

* [#2198] Added examples and documentation for highly-available setups with regard to
  the background task message queue.
* Updated installation documentation to mention the correct Python version.
* Documented the flow to register a form on behalf of a customer.
* Delete obsolete/old boilerplate documentation.
* Updated developer docs and clarified SDK developer documentation.

**Project maintenance**

* Removed some obsolete/unnecessary assets on error pages.
* [#2377] Refactored links to make use of the NL DS ``utrecht-link`` component - you can
  now use all the design tokens from that component in Open Forms too.
* [#2454] Upgraded black and flake8 versions for Python 3.10 support.
* [#2450] Moved JSON-logic expression processing into maykin-json-logic-py library.
* Upgraded a number of dependencies.
* [#2471] Refactored appointments module to bring the plugin structure in line with the
  rest of the project.
* [#1439] The Docker Hub readme/description is now automatically updated via Github
  Actions.
* [#2555] Removed dead code.
* [#1904] Refactored existing code to make use of the sandboxed template backends.
* [#1898] Refactored template validators to use the sandboxed template backends.
* Tweaked CI for speed so we spend less time waiting for CI builds to complete.
* Delete explicitly setting the template loaders.
* [#2583] Fixed a case of broken test isolation.
* Upgraded drf-spectacular to the latest version.
* Added omg.org and jccsoftware.nl to docs link-check ignore list.
* Added CI job to install dev deps on MacOS.
* [#2478] Added frontend code test infrastructure.


2.0.3 (2023-01-24)
==================

Bugfix release addressing some more upgrade issues

* [#2520] Fixed bug in mimetype validation for ``application/ms-word`` (and similar) files
* [#2519] Skip 2.0.x upgrade checks if we're already on 2.0.x
* [#2576] Fix upgrade crash on components with prefill attribute names > 50 chars
* [security#20] Fixed CSP configuration for Matomo, Piwik and Piwik PRO analytics
* [#2012] Fixed CSP mechanisms in SiteImprove analytics provider snippet
* [#2396] Fixed "auto login authentication" option not properly resetting
* [#2541] Fixed a crash in the logic editor when changing the key of selectboxes components

.. warning:: Manual intervention required for Matomo, Piwik and Piwik PRO users.

   Before 2.0.3, the server URLs for these analytics providers were configured without
   protocol (typically ``https://``), leading to an insufficiently strict CSP
   configuration.

   We can not automatically migrate this, but the configuration can be fixed easily in
   the admin in two places:

   1. Navigate to Admin > Configuratie > Analytics tools-configuratie
   2. Add ``https://`` in front of your analytics provider server URL (or ``http://``,
      depending on your environment)
   3. Save the changes

   Next, apply the same update to the CSP configuration:

   1. Navigate to Admin > Configuratie > Csp settings
   2. Find all occurrences of your analytics tool server URL (e.g. ``matomo.example.com``)
   3. Update every record by prepending ``https://`` (or ``http://``, depending on your
      environment) and save the changes

2.0.2 (2022-12-23)
==================

Periodic bugfix release, addressing some blocking defects and upgrade issues.

* [#2331] Fixed incorrect key validation problem which would block upgrades to 2.0+
* [#2385] Fixed incomplete logic handling which would block upgrades to 2.0+
* [#2398] Fixed logic trigger processing which could crash upgrades to 2.0+
* [#2413] Fixed fields being made visible by selectboxes in frontend logic not being
  visible in summary/pdf/emails
* [#2422] Fixed invalid postcode format being sent to StUF-ZDS
* [#2289] Fixed StUF-ZDS: now a ``Vestiging`` is created if vestigingsnummer is present,
  falling back to ``NietNatuurlijkPersoon`` otherwise.
* [#2494] Fixed person details not being sent to StUF-ZDS if the submitter was not
  authenticated but instead filled out details manually.
* [#2432] Fixed importing pre-2.0 forms with legacy form step references in actions
* Fix docs build due to legacy renegotiation being disabled in openssl 3

1.1.9 (2023-12-23)
==================

Periodic bugfix release, addressing some blocking defects and upgrade issues.

* [#2331] Fixed incorrect key validation problem which would block upgrades to 2.0+
* [#2385] Fixed incomplete logic handling which would block upgrades to 2.0+
* [#2413] Fixed fields being made visible by selectboxes in frontend logic not being
  visible in summary/pdf/emails
* [#2422] Fixed invalid postcode format being sent to StUF-ZDS
* [#2494] Fixed person details not being sent to StUF-ZDS if the submitter was not
  authenticated but instead filled out details manually.
* Fix docs build due to legacy renegotiation being disabled in openssl 3

2.1.0-alpha.1 (2022-12-20)
==========================

Second alpha version of the 2.1.0 release.

**New features**

* [#2332] Added ``ServiceFetchConfiguration`` data model
* [#2348] Added audit logging for empty prefill plugin values
* [#2313] Added ``translations`` keys to API endpoints to store/read field translations
* [#2402] Updated JSON-structure of "ProductAanvraag" registration
* [#2314] Added UI in form designer to manage form/form step translations
* [#2287] Confirmed support for multi-language forms in import/export
* [#1862] Include "rol" metadata when an employee registers a case on behalf of a customer
* [#2389] Add submission language code to submission exports
* [#2390] Render documents in submission language: PDF report and confirmation email
* [#2463] Improved repeating groups error messages
* [#2447] Expose meta-information if an authentication plugin is for 'machtigen'
* [#2458] Added option to extract OIDC user information from ID-token instead of
  info endpoint
* [#2430] Added HEIC and TXT to filetypes for upload
* [#2428] Added organization name configuration option, displayed in various
  labels/titles.
* [#2315] Implementing UI for entering and storing formio.js component translations

**Bugfixes**

* [#2367] Fixed upgrade/migration crash when dealing with selectboxes frontend logic
* [#2251] Fixed broken logic when comparing to dates
* [#2385] Fixed a crash when processing incomplete frontend logic
* [#2219] Updated fix for CSS-unit issue with design tokens in email header logo
* [#2400] Clean up cached execution state
* [#2340] Added bandaid fix to clear data that isn't visible if the parent component is
  hidden
* [#2397] Fixed some duplicate labels in admin
* [#2413] Fixed fields made visible by selectboxes type components not showing up in
  summary/pdf/email
* [#1302] Fixed family members component crash when no BSN is known
* [#2422] remove spaces from postcodes in StUF messages
* [#2250] Fixed broken analytics scripts not loading/executing
* [#2436] Fixed broken default value of copied fields inside fieldsets
* [#2445] Ensure that removing a fieldset in the form designer also removes the variables
* [#2398] Fixed upgrade/migration crash when formio logic references non-existing
  component keys
* [#2432] Fixed backwards-compatibility layer for pre-2.0 form exports with actions
  targetting form steps
* [#2484] Fixed unexpected fallbacks to NL for form literals instead of using the
  global configuration
* [#2488] Disable inline edit for repeating groups again
* [#2449] Fixed server-side logic interpretation inside repeating groups
* Fixed import crash due to performance optimization
* [#1790] Fixed broken "form definition used in forms" modal in production builds
* [#2373] Remove (unintended) multiple option for map component

**Documentation**

* Updated examples and example form exports to 2.0
* Provide best-practices for securing OF installations
* [#2394] Removed digid/eherkenning envvars config from docs
* [#2477] Added new page for multi-language configuration to the manual
* Removed ambiguity about staff/non-staff fields in certain API endpoints

**Project maintenance**

* Upgraded Pillow to the latest version
* [#1068] Finalized refactor for formio integration in the backend
* removed unused UI template tags/options
* [#2312] Upgraded base docker images to Debian bullseye
* [#2487] Add import sorting plugin for prettier
* Catch invalid appointment configs in management command
* Bumped frontend/build dependency versions


2.0.1 (2022-11-23)
==================

First maintenance release of the 2.0 series.

This patch fixes a couple of bugs encountered when upgrading from 1.1 to 2.0.

**Bugfixes**

* [#2301] Fixed identifying attributes still being hashed after a submission is resumed
* [#2135] Fixed submission step data being cascade deleted in certain edge cases
* [#2219] A fix was also attempted for bad CSS unit usage in confirmation emails, but
  this caused other problems. As a workaround you should use the correctly sized images
  for the time being.
* [#2244] Fixed 'content' component and components not marked as showInSummary showing
  up in server rendered summary
* Fixed pattern for formio key validation
* [#2304] Refactored form logic action "mark step as not applicable" to use ID
  references rather than API paths, which affected some logic actions.
* [#2262] Fixed upgrade from < 2.0 crash when corrupt prefill configuration was present
  in existing forms
* [#1899] Apply prefill data normalization before saving into variables
* [#2367] Fixed automatic conversion of advanced frontend logic when using selectboxes
  component type

2.1.0-alpha.0 (2022-11-21)
==========================

First alpha version of the 2.1.0 release.

Open Forms now has the ambition to release an alpha version about every 4 weeks (at
the end of a sprint) and putting out a new minor or major version every quarter.

**New features**

* [#1861, #1862] Added organization member authentication for forms. Using OIDC, employees of
  the organization can now log in to (internal) forms and submit them. It is also
  possible for employees (e.g. service desk staff) to start forms on behalf of customers.
* [#2042] Optimized component mutations (by logic) by using a caching datastructure
* [#2209] Simplified number component validation error messages
* Ensured that upgrading to 2.1 enforces upgrading to 2.0 first
* [#2225] Emit openforms-theme as default theme unless an explicit theme is configured
* [#2197] Implemented plugin hooks to modify requests that are about to be made to
  third party services
* [#2197] Added container image tag/version including all official extensions
  (including token-exchange authorization)
* [#1929] Added early file type/extension validation for file uploads
* Added ``reverse_plus()`` utility function
* [#1849] DigiD/eHerkenning/eIDAS metadata can now be configured and generated from the admin
* First steps for translatable content/forms:

  * [#2228] Enabled run-time language preference detection
  * [#2229] Added endpoint to expose available (and currently activated) language(s)
  * [#2230] Expose translatable properties for forms (in the admin)
  * [#2231] API endpoints return content in the currently activated/requested language
  * [#2232] Expose whether form translations are enabled (and enforce the default
    language if they're not)
  * [#2278, #2279] Store the language for a form submission when it's created
  * [#2255] SDK: use the correct locale for static translations

* [#2289] Create NNP/Vestiging depending on the available properties (registration backends)
* [#2329] The CSP post-processor now performs HTML sanitation too, stripping tags and
  attributes that are not on the allowlist.
* Optimized form list endpoint
* Upgraded to Python 3.10

**Bugfixes**

* [#2062] Fixed "Print this page" CSP violation
* [#1180] Fixed Google Analytics not measuring form steps correctly
* [#2208] Fixed JSON-logic expressions with primitives (number, string...)
* [#1924] Various fixes to the dark mode theme for the form designer
* [#2206] Fixed a race condition related to prefill variables
* [#2213] Fixed inconsistent default values for copied components in the form designer
* [#2246] Fixed invalid error styling in form designer
* [#1901] Fixed image inline styles in content components by CSP post-processing them
* [#1957] Fixes admin ``retry_processing_submissions()`` action to reset
  submission registration attempts counter
* [#2148] Changed VertrouwelijkheidsAanduidingen translatable choice labels to Dutch
* [#2245] Changed privacy policy link in summary page to open in new window
* [#2277] Fixed Ogone feedback URL
* [#2301] Fixed identifying attributes still being hashed after a submission is resumed
* [#2135] Fixed submission step data being cascade deleted in certain edge cases
* [#2244] Fixed 'content' component and components not marked as ``showInSummary``
  showing up in server rendered summary
* Fixed pattern for formio key validation
* [#2337] Fixed crash on data prefill for certain multi-step forms
* [#2304] Refactored form logic action "mark step as not applicable" to use ID references
  rather than API paths.
* [#1899] Apply prefill data normalization before saving into variables
* [#2352] Removed permissions to delete user from standard groups as those cascade
  delete admin log entries.
* [#2344] Fixed out-of-place repeating groups required-field asterisk
* [#2145] Removed copy-paste snippets from form change page as they are not guaranteed
  to be correct to your use-case.

**Documentation**

* [#2163] Document file upload storage flow
* Installation docs: configure db *before* migrate and runserver
* Installation docs: added missing OS-level dependencies
* [#2205] Documented unsupported JSON-logic operators

**Project maintenance**

* [#2050] Removed ``SubmissionFileAttachment.form_key`` field and using variables instead
* [#2117] Fixed spelling 'organisation' -> 'organization'
* Fixed example dotenv file
* Emit deprecation warning for openforms.formio.utils.get_component
* Update Django to latest patch/security releases
* [#2221] Removed code for warning about duplicate keys
* Converted squashed migration into regular migrations
* Updated github workflows to action versions following some deprecations
* Fixed private media and add media mount in examples/docker-compose file
* Upgraded to latest lxml version
* Dropped django-capture-on-commit-callbacks as Django provides it now
* Pin postgres version to 14 in docker-compose
* [#2166] Modified Dockerfile with Volumes hint to prevent writing to container layer
* [#2165] Upgrade django-simple-certmanager
* [#2280] Removed ``SubmissionValueVariable.language``
* Refactored mail cleaning utilities into separate library
* Parametrize workflows/dockerfile for extensions build

1.1.8 (2022-11-07)
==================

Open Forms 1.1.8 fixes some bugs for which no workaround exists

* [#1724] Fixed content fields showing as "required" field
* [#2117] Fixed exporting submissions with conditionally filled form steps
* [#1899] Fixed prefill-data tampering check rejecting data due to difference in
  formatting logic between prefill plugin and form data
* [#1351] Ensure that number and currency components can accept negative values
* [#2135] Fixed submission steps being deleted when deleting form steps and/or restoring
  old form versions. This did not affect data sent to registration backends.
* [#1957] Fixed retrying submission registration in the admin when the maximum number
  of attempts was already reached.
* [#2301] Fixed identifying attributes still being hashed for paused-and-resumed
  submissions. This caused the hashes to be sent to registration backends rather than
  the actual BSN/KVK/Pseudo attribute.
* [#2219] Fixed CSS units usage for logo design tokens in (confirmation) emails

2.0.0 "Règâh" (2022-10-26)
==========================

*The symbol of The Hague is the stork, a majestic bird, which is somewhat
disrespectfully called a Règâh, or heron, by the residents of The Hague.*

BEFORE upgrading to 2.0.0, please read the release notes carefully.

Upgrade procedure
-----------------

Open Forms 2.0.0 contains a number of breaking changes. While we aim to make the upgrade
process as smooth as possible, you will have to perform some manual actions to ensure
this process works correctly.

1. You must first upgrade to (at least) version 1.1.6

   .. warning::
      This ensures that all the relevant database changes are applied before
      the changes for 2.0 are applied. Failing to do so may result in data loss.

2. Ensure that there are no duplicate component keys in your forms.

   After upgrading to 1.1.6, run the ``check_duplicate_component_keys`` management
   command, which will report the forms that have non-unique component keys:

   .. code-block:: bash

       # in the container via ``docker exec`` or ``kubectl exec``:
       python src/manage.py check_duplicate_component_keys

   If there are duplicate component keys, you must edit the forms via the admin
   interface to rename them.

3. Next, you must ensure that all component keys are *valid* keys - keys may only
   contains letters, numbers, underscores, hyphens and periods. Additionally, keys may not
   end with a period or hyphen.

   .. code-block:: bash

       # in the container via ``docker exec`` or ``kubectl exec``:
       python src/manage.py check_invalid_field_keys

   Any invalid keys will be reported, and you must edit the forms via the admin
   interface to change them.

4. After resolving any problems reported from the commands/scripts above, you can
   proceed to upgrade to version 2.0.0

Changes
-------

**Breaking changes**

We always try to minimize the impact of breaking changes, especially with automated
upgrade processes. However, we cannot predict all edge cases, so we advise you to
double check with the list of breaking changes in mind.

* Introduced form variables in the engine core. Existing forms are automatically
  migrated and should continue to work.
* Component keys must be unique within a single form. This used to be a warning, it is
  now an error.
* The logic action type ``value`` has been replaced with setting the value of a
  variable. There is an automatic migration to update existing forms.
* Removed the ``Submission.bsn``, ``Submission.kvk`` and ``Submission.pseudo`` fields.
  These have been replaced with the ``authentication.AuthInfo`` model.
* The major API version is now ``/api/v2`` and the ``/api/v1`` endpoints have been
  replaced. For non-deprecated endpoints, you can simply replace ``v1`` with ``v2`` in
  your own configuration.
* The logic rules (form logic, price logic) endpoints have been removed in favour of
  the new bulk endpoints
* The logic action type 'value' has been replaced with action type 'variable'. There is
  an automatic migration to update existing forms.
* The Design tokens to theme Open Forms have been renamed. There is an automatic
  migration to update your configuration.
* Before 1.2.0, the SDK would display a hardcoded message to start the form depending on
  the authentication options. This is removed and you need to use the form explanation
  WYSIWYG field to add the text for end-users.
* The ``DELETE /api/v1/authentication/session`` endpoint was removed, instead use the
  submission specific endpoint.
* Advanced logic in certain components (like fieldsets) has been removed - conditional
  hide/display other than JSON-logic/simple logic is no longer supported.
* Enabled Cross-Site-Request-Forgery protections for *anonymous* users (read: non-staff
  users filling out forms). Ensure that your Open Forms Client sends the CSRF Token
  value received from the backend. Additionally, for embedded forms you must ensure
  that the ``Referer`` request header is sent in cross-origin requests. You will likely
  have to tweak the ``Referrer-Policy`` response header.

**New features/improvements**

*Core*

* [#1325] Introduced the concept of "form variables", enabling a greater flexibility
  for form designers

  * Every form field is automatically a form variable
  * Defined a number of always-available static variables (such as the current
    timestamp, form name and ID, environment, authentication details...)
  * Form designers can define their own "user-defined variables" to use in logic and
    calculations
  * Added API endpoints to read/set form variables in bulk
  * Added API endpoint to list the static variables
  * The static variables interface is extensible

* [#1546] Reworked form logic rules

  * Rules now have explicit ordering, which you can modify in the UI
  * You can now specify that a rule should only be evaluated from a particular form
    step onwards (instead of 'always')
  * Form rules are now explicitely listed in the admin for debugging purposes
  * Improved display of JSON-logic expressions in the form designer
  * When adding a logic rule, you can now pick between simple or advanced - more types
    will be added in the future, such as DMN.
  * You can now use all form variables in logic rules

* [#1708] Reworked the logic evaluation for a submission

  * Implemented isolated/sandboxed template environment
  * Form components now support template expressions using the form variables
  * The evaluation flow is now more deterministic: first all rules are evaluated that
    updated values of variables, then all other logic actions are evaluated using
    those variable values

* [#1661] Submission authentication is now tracked differently

  * Removed the authentication identifier fields on the ``Submission`` model
  * Added a new, generic model to track authentication information:
    ``authentication.AuthInfo``
  * Exposed the submission authentication details as static form variables - you now
    no longer need to add hidden form fields to access this information.

* [#1967] Reworked form publishing tools

  * Deactivated forms are deactivated for everyone
  * Forms in maintenance mode are not available, unless you're a staff member
  * The API endpoints now return HTTP 422 or HTTP 503 errors when a form is deactivated
    or in maintenance mode
  * [#2014] Documented the recommended workflows

* [#1682] Logic rules evaluation is now logged with the available context. This should
  help in debugging your form logic.
* [#1616] Define extra CSP directives in the admin
* [#1680] Laid the groundwork for DMN engine support. Note that this is not exposed
  anywhere yet, but this will come in the future.
* [#1687] There is now an explicit validate endpoint for submisisons and possible error
  responses are documented in the API spec.
* [#1739] (API) endpoints now emit headers to prevent browser caching
* [#1719] Submission reports can now be downloaded for a limited time instead of only once
* [#1835] Added bulk endpoints for form and price logic rules
* [#1944] API responses now include more headers to expose staff-only functionality to
  the SDK, and permissions are now checked to block/allow navigating between form
  steps without the previous steps being completed.
* [#1922] First passes at profiling and optimizing the API endpoints performance
* Enabled Cross-Site-Request-Forgery protections for *anonymous* users
* [#2042] Various performance improvements

*Form designer*

* [#1642] Forms can now be assigned to categories in a folder structure
* [#1710] Added "repeating group" functionality/component
* [#1878] Added more validation options for date components

  * Specify a fixed min or max date; or
  * Specify a minimum date in the future; or
  * Specify a maximum date in the past; or
  * Specify a min/max date relative to a form variable

* [#1921] You can now specify a global default for allowed file types
* [#1621] The save/save-and-continue buttons are now always visible on the page in
  large forms
* [#1651] Added 'Show Form' button on form admin page
* [#1643] There is now a default maximum amount of characters (1000) for text areas
* [#1325] Added management command to check number of forms with duplicate component keys
* [#1611] Improved the UX when saving a form which still has validation errors somewhere.
* [#1771] When a form step is deleted and the form definition is not reusable, the form
  definition is now deleted as well
* [#1702] Added validation for re-usable form definitions - you can no longer mark a
  form definition as not-reusable if it's used in multiple forms
* [#1708] We now keep track of the number of formio components used in a form step for
  statistical/performance analysis
* [#1806] Ensure that logic variable references are updated
* [#1933] Replaced hardcoded SDK start (login) message with text in form explanation
  template.
* [#2078] field labels are now compulsory (a11y)
* [#2124] Added message to file-upload component informing the user of the maximum
  allowed file upload size.
* [#2113] added option to control column size on mobile viewports
* [#1351] Allow negative currency and number components

*Registrations*

* [#1007] you can now specify the document type for every upload component (applies to
  Objects API and ZGW registration)
* [#1723] StUF-ZDS: Most of the configuration options are now optional
* [#1745] StUF: file content is now sent with the ``contenttype`` attribute
* [#1769] StUF-ZDS: you can now specify the ``vertrouwelijkheidaanduiding``
* [#1183] Intermediate registration results are now properly tracked and re-used,
  preventing the same objects being created over and over again if registration is being
  retried. This especially affects StUF-ZDS and ZGW API's registration backends.
* [#1877] Registration email subject is now configurable
* [#1867] StUF-ZDS & ZGW: Added more registration fields

*Prefill*

* [#1693] Added normalization of the postcode format according to the specified
  comonent mask
* The prefill machinery is updated to work with variables. A bunch of (private API) code
  in the ``openforms.prefill`` module was deleted.
* Removed the ``Submission.prefill_data`` field. This data is now stored in
  form/submission variables.

*Other*

* [#1620] Text colors in content component can now be configured with your own presets
* [#1659] Added configuration options for theme class name and external stylesheet to load
* Renamed design tokens to align with NL Design System style design tokens
* [#1716] Added support for Piwik Pro analytics provider
* [#1803] Form versions and exports now record the Open Forms version they were created
  with, showing warnings when restoring a form from another Open Forms version.
* [#1672] Improved error feedback on OIDC login failures
* [#1320] Reworked the configuration checks for plugins
* You can now use separate DigiD/eHerkenning certificates
* [#1294] Reworked analytics integration - enabling/disabling an analytics provider now
  automatically updates the cookies and CSP configuration
* [#1787] You can now configure the "form pause" email template to use
* [#1971] Added config option to disable search engine indexing
* [#1895] Removed deprecated functionality
* Improved search fields in Form/Form Definition admin pages
* [#2055] Added management command to check for invalid keys
* [#2058] Added endpoint to collect submission summary data
* [#2141] Set up stable SDK asset URLs
* [#2209] Improved validation errors for min/max values in number components

**Bugfixes**

* [#1657] Fixed content component configuration options
* Fixed support for non-white background colors in PDFs with organization logos
* [CVE-2022-31041] Perform proper upload file type validation
* [CVE-2022-31040] Fixed open redirect in cookie-consent 'close' button
* [#1670] Update error message for number validation
* [#1681] Use a unique reference number every time for StUF-ZDS requests
* [#1724] Content fields must not automatically be marked as required
* [#1475] Fixed crash when setting an empty value in logic action editor
* [#1715] Fixed logo sizing for PDFs (again)
* [#1731] Fixed crash with non-latin1 characters in StUF-calls (such as StUF-ZDS)
* [#1737] Fixed typo in email translations
* [#1729] Applied workaround for ``defaultValue`` Formio bug
* [#1730] Fixed CORS policy to allow CSP nonce header
* [#1617] Fixed crash on StUF onvolledige datum
* [GHSA-g936-w68m-87j8] Do additional permission checks for forms requiring login
* [#1783] Upgraded formiojs to fix searching in dropdowns
* Bumped Django and django-sendfile2 versions with fixes for CVE-2022-36359
* [#1839] Fixed tooltip text not being displayed entirely
* [#1880] Fixed some validation errors not being displayed properly
* [#1842] Ensured prefill errors via StUF-BG are visible in logs
* [#1832] Fixed address lookup problems because of rate-limiting
* [#1871] Fixed respecting simple client-side visibility logic
* [#1755] Fixed removing field data for fields that are made visible/hidden by logic
* [#1957] Fixed submission retry for submissions that failed registration, but exceeded
  the automatic retry limit
* [#1984] Normalize the show/hide logic for components and only expose simple variants.
  The complex logic was not intended to be exposed.
* [#2066] Re-add key validation in form builder
* Fixed some translation mistakes
* Only display application version for authenticated staff users, some pages still
  leaked this information
* Fixed styling of the password reset pages
* [#2154] Fixed coloured links email rendering crash
* [#2117] Fixed submission export for submissions with filled out subset of
  available fields
* [#1899] Fixed validation problem on certain types of prefilled fields during
  anti-tampering check due to insufficient data normalization
* [#2062] Fixed "print this page" CSP violation

**Project maintenance**

* Upgraded icon fonts version
* Upgraded CSS toolchain
* Frontend code is now formatted using ``prettier``
* [#1646] Tweaked django-axes configuration
* Updated examples in the documentation
* Made Docker build smaller/more efficient
* Added the open-forms design-tokens package
* Bumped a number of (dev) dependencies that had security releases
* [#1615] documented the CORS policy requirement for font files
* Added and improved the developer installation documentation
* Added pretty formatting of ``flake8`` errors in CI
* Configured webpack for 'absolute' imports
* Replaced deprected ``defusedxml.lxml`` usage
* [#1781] Implemented script to dump the instance configuration for import into another
  environment
* Added APM instrumentation for better insights in endpoint performance
* Upgrade to zgw-consumers and django-simple-certmanager
* Improved documentation on embedding the SDK
* [#921] Added decision tree docs
* Removed noise from test output in CI
* [#1979] documented the upgrade process and added checks to verify consistency/state
  BEFORE migrating the database when upgrading versions
* [#2004] Add post-processing hook to add CSRF token parameter
* [#2221] Remove code for duplicated component key warnings

1.1.7 (2022-10-04)
==================

1.1.6 was broken due to a bad merge conflict resolution.

* [#2095] Fixed accidentally removing the OF layer on top of Formio
* [#1871] Ensure that fields hidden in frontend don't end up in registration emails

1.1.6 (2022-09-29)
==================

Bugfix release + preparation for 2.0.0 upgrade

* [#1856] Fixed crash on logic rule saving in the admin
* [#1842] Fixed crash on various types of empty StUF-BG response
* [#1832] Prevent and handle location service rate limit errors
* [#1960] Ensure design tokens override default style
* [#1957] Fixed not being able to manually retry errored submission registrations having
  exceeded the retry limit
* [#1867] Added more StUF-ZDS/ZGW registration fields.
* Added missing translation for max files
* [#2011] Worked around thread-safety issue when configuring Ogone merchants in the admin
* [#2066] Re-added key validation in form builder
* [#2055] Added management command to check for invalid keys
* [#1979] Added model to track currently deployed version

1.0.14 (2022-09-29)
===================

Final bugfix release in the ``1.0.x`` series.

* [#1856] Fixed crash on logic rule saving in the admin
* [#1842] Fixed crash on various types of empty StUF-BG response
* [#1832] Prevent and handle location service rate limit errors
* [#1960] Ensure design tokens override default style
* [#1957] Fixed not being able to manually retry errored submission registrations having
  exceeded the retry limit
* [#1867] Added more StUF-ZDS/ZGW registration fields.
* Added missing translation for max files
* [#2011] Worked around thread-safety issue when configuring Ogone merchants in the admin
* [#2066] Re-added key validation in form builder
* [#2055] Added management command to check for invalid keys
* [#1979] Added model to track currently deployed version

.. note:: This is the FINAL 1.0.x release - support for this version has now ended. We
   recommend upgrading to the latest major version.

1.1.5 (2022-08-09)
==================

Security fix release

This release fixes a potential reflected file download vulnerability.

* Bumped Django and django-sendfile2 versions with fixes for CVE-2022-36359
* [#1833] Fixed submission being blocked on empty prefill data

1.0.13 (2022-08-09)
===================

Security fix release

This release fixes a potential reflected file download vulnerability.

* Bumped Django and django-sendfile2 versions with fixes for CVE-2022-36359
* Fixed the filename of submission attachment file downloads
* [#1833] Fixed submission being blocked on empty prefill data

1.1.4 (2022-07-25)
==================

Bugfix release

Note that this release includes a fix for Github security advisory
`GHSA-g936-w68m-87j8 <https://github.com/open-formulieren/open-forms/security/advisories/GHSA-g936-w68m-87j8>`_.

* Upgraded to latest Django security release
* [#1730] Update allowed headers for nonce CSP header
* [#1325] Added management command to check number of forms with duplicate component
  keys (required for upgrade to 1.2 when it's available)
* [#1723] StUF-ZDS registration: a number of configuration options are now optional
* [#1769] StUF-ZDS registration: you can now configure the confidentiality level of a
  document attached to the zaak
* [#1617] Fixed crash on StUF onvolledige datum
* [GHSA-g936-w68m-87j8] Perform additional permission checks if the form requires
  login
* Backported Submission.is_authenticated from #1418

1.0.12 (2022-07-25)
===================

Bugfix release

Note that this release includes a fix for Github security advisory
`GHSA-g936-w68m-87j8 <https://github.com/open-formulieren/open-forms/security/advisories/GHSA-g936-w68m-87j8>`_.

* Upgraded to latest Django security release
* [#1730] Update allowed headers for nonce CSP header
* [#1325] Added management command to check number of forms with duplicate component
  keys (required for upgrade to 1.2 when it's available)
* [#1723] StUF-ZDS registration: a number of configuration options are now optional
* [#1769] StUF-ZDS registration: you can now configure the confidentiality level of a
  document attached to the zaak
* [#1617] Fixed crash on StUF onvolledige datum
* [GHSA-g936-w68m-87j8] Perform additional permission checks if the form requires
  login
* Backported Submission.is_authenticated from #1418

1.1.3 (2022-07-01)
==================

Periodic bugfix release

* [#1681] Use a unique reference number every time for StUF-ZDS requests
* [#1687] Added explicit submission step validate endpoint
* Fixed unintended camelization of response data
* Bumped API version to 1.1.1
* [#1693] Fixed postcode validation errors by applying input mask normalization to prefill values
* [#1731] Fixed crash with non-latin1 characters in StUF-calls (such as StUF-ZDS)

1.0.11 (2022-06-29)
===================

Periodic bugfix release

* [#1681] Use a unique reference number every time for StUF-ZDS requests
* [#1687] Added explicit submission step validate endpoint
* Fixed unintended camelization of response data
* Bumped API version to 1.0.2
* [#1693] Fixed postcode validation errors by applying input mask normalization to
  prefill values
* [#1731] Fixed crash with non-latin1 characters in StUF-calls (such as StUF-ZDS)

1.1.2 (2022-06-16)
==================

Hotfix following 1.1.1

The patch validating uploaded file content types did not anticipate the explicit
wildcard configuration option in Formio to allow all file types. This caused files
uploaded by end-users to not be attached to the submission.

We've fixed the wildcard behaviour, but you should check your instances for incomplete
data. This involves a couple of steps with some pointers below.

1. The temporary uploads are automatically removed by the cronjobs at 3:30 UTC. The
   default setting is to do this after 2 days (48 hours). We have provided an example
   management command that you can use to check if you need to partially
   restore backups. Make sure to tweak the ``WINDOW_START`` and ``WINDOW_END`` variables
   to your specific situation - the start would be when you started deploying version
   1.0.9, and the end would be ``most recent 3:30 minus 48 hours``.

2. If you need to do partial restores, you should recover the records from the
   ``submissions_temporaryfileupload`` database table where the ``created_on`` timestamp
   lies in your interval. Additionally, you need to recover the file uploads of those
   relevant records. The paths are given by the column ``content``. You find those files
   in the ``private_media`` directory.

3. Finally, you can run the management command ``recover_missing_attachments``, which
   will report any issues and print out the references and IDs of the affected
   submissions.

1.0.10 (2022-06-16)
===================

Hotfix following 1.0.9 - this is the same patch as 1.1.2.

1.1.1 (2022-06-13)
==================

Security release (CVE-2022-31040, CVE-2022-31041)

This bugfix release fixes two security issues in Open Forms. We recommend upgrading
as soon as possible.

* [CVE-2022-31040] Fixed open redirect in cookie-consent 'close' button
* [CVE-2022-31041] Perform upload content validation against allowed file types
* [#1670] Update error message for number validation

1.0.9 (2022-06-13)
==================

Security release (CVE-2022-31040, CVE-2022-31041)

This bugfix release fixes two security issues in Open Forms. We recommend upgrading
as soon as possible.

* [CVE-2022-31040] Fixed open redirect in cookie-consent 'close' button
* [CVE-2022-31041] Perform upload content validation against allowed file types
* [#1670] Update error message for number validation
* [#1560] Fix prefill not working inside of nested/layout components

1.1.0 (2022-05-24)
==================

Feature release 1.1.0

For the full list of changes, please review the changelog entries below for 1.1.0-rc.0
and 1.1.0-rc.1.

Since 1.1.0-rc.1, the following changes were made:

* Fixed maintaining the logo aspect ratio in the confirmation PDF for a submission
* Exposed options to display content/WYSIWYG text in confirmation emails
* WYSIWYG component content is displayed full-width in the confirmation email and PDF

1.1.0-rc.1 (2022-05-20)
=======================

Second release candidate for the 1.1.0 feature release.

* [#1624] Fixed list of prefill attributes refresh on prefill plugin change
* Fixed styling issue with card components in non-admin pages
* [#1628] Make fieldset labels stand out in emails
* [#1628] Made styling of registration email consistent with confirmation email
* Added raw_id_fields to submissions admin for a performance boost
* [#1627] Fixed CSRF error when authenticating in the admin after starting a form
* Fixed cookie ``SameSite=None`` being used in non-HTTPS context for dev environments
* [#1628] Added missing form designer translations for display/summary options
* [#1628] Added vertical spacing to confirmation PDF pages other than the first page

.. note:: #1627 caused session authentication to no longer be available in the API
   schema for the submission suspend/complete endpoints. This was not intended to be
   public API, so this option is gone now.

   Both of these endpoints require a valid submission ID to exist in the session to
   use them, which was the intended behaviour.

1.1.0-rc.0 (2022-05-17)
=======================

First release candidate of the 1.1.x release series!

Version 1.1.0 contains a number of improvements, both in the backend and SDK. All
changes are backwards compatible, but some features have been deprecated and will be
removed in version 2.0, see the last section of this changelog entry.

**Summary**

* The API spec has been bumped to version 1.1.0
* A new minor version of the SDK is available, which requires a minimum backend version
  of 1.1.0
* Upgrading should be straigh-forward - no manual interventions are needed.

**New features**

* [#1418] Expose ``Submission.isAuthenticated`` in the API
* [#1404] Added configuration options for required fields

  - Configure whether fields should be marked as required by default or not
  - Configure if an asterisk should be used for required fields or not

* [#565] Added support for DigiD/eHerkenning via OpenID Connect protocol
* [#1420] Links created by the form-builder now always open in a new window (by default)
* [#1358] Added support for Mutual TLS (mTLS) in service configuration - you can now
  upload client/server certificates and relate them to JSON/SOAP services.
* [#1495] Reworked admin interface to configure mTLS for SOAP services
* [#1436] Expose ``Form.submissionAllowed`` as public field in the API
* [#1441] Added submission-specific user logout endpoint to the API. This now clears the
  session for the particular form only, leaving other form session untouched. For
  authenticated staff users, this no longer logs you out from the admin interface. The
  existing endpoint is deprecated.
* [#1449] Added option to specify maximum number of files for file uploads
* [#1452] Added option to specify a validation regular-expression on telefone field
* [#1452] Added phone-number validators to API for extensive validation
* [#1313] Added option to auto redirect to selected auth backend
* [#1476] Added readonly option to BSN, date and postcode components
* [#1472] Improved logic validation error feedback in the form builder
* [#1482, #1510] Added bulk export and import of forms functionality to the admin interface
* [#1483] Added support for dark browser theme
* [#1471] Added support for DigiD Machtigen and eHerkenning Bewindvoering with OIDC
* [#1453] Added Formio specific file-upload endpoint, as it expects a particular
  response format for success/failure respones. The existing endpoint is deprecated.
* [#1540] Removed "API" and "layout" tabs for the content component.
* [#1544] Improved overview of different components in the logic rule editor.
* [#1541] Allow some NL Design System compatible custom CSS classes for the content
  component.
* [#1451] Completely overhauled "submission rendering". Submission rendering is used
  to generate the confirmation emails, PDFs, registration emails, exports...

  - You can now specify whether a component should be displayed in different modes
    (PDF, summary, confirmation email)
  - Implemented sane defaults for configuration options
  - PDF / Confirmation emails / registration emails now have more structure,
    including form step titles
  - Container elements (fieldsets, columns, steps) are only rendered if they have
    visible content
  - Logic is now respected to determine which elements are visible or hidden
  - Added a CLI render mode for debug/testing purposes
  - Fixed page numbers being half-visible in the confirmation PDF

* [#1458] Submission registration attempts are now limited to a configurable upper
  bound. After this is reached, there will be no automatic retries anymore, but manual
  retries via the admin interface are still possible.
* [#1584] Use the original filename when downloading submission attachments
* [#1308] The admin interface now displays warnings and proper error messages if your
  session is about to expire or has expired. When the session is about to expire, you
  can extend it so you can keep working for longer times in the UI.

**Bugfixes**

All the bugfixes up to the ``1.0.8`` release are included.

* [#1422] Prevent update of custom keys on label changes for radio button components
  in the form builder
* [#1061] Fixed duplicate 'multiple' checkbox in email component options
* [#1480] Reset steps with data if they turn out to be not applicable
* [#1560] Fix prefill fields in columns not working (thanks @rbakels)

**Documentation**

* [#1547] Document advanced rules for selectboxes
* [#1564] Document how logic rules are evaluated

**Project maintenance**

* [#1414] Removed ``GlobalConfiguration.enable_react_form`` feature flag
* Set CSP_REPORT_ONLY to true in docker-compose setup
* Set up deterministic networking across compose files
* Upgrade to django-admin-index 2.0.0
* Delete dead code on custom fields
* Upgraded to Webpack 5 & use ``nvm`` config on CI
* Bumped Node JS version from 14 to 16 (and npm from v6 to v8)
* Added command to disable demo plugins and applied to OAS generation script
* [maykinmedia/django-digid-eherkenning#4] Updated because of external provider changes
* Added CI check to lint requirements/base.in
* Ensure uwsgi runs in master process mode for better crash recovery
* Improved development views to view how confirmation emails/PDFs will be rendered
* Refactor submission models
* Refactor form serializers file
* Moved some generic OIDC functionality to mozilla-django-oidc-db
* [#1366] default to allow CORS with docker-compose
* Remove SDK from docker-compose
* Add SMTP container to docker-compose stack for outgoing emails
* [#1444] resolve media files locally too with WeasyPrint
* Update momentjs version (dependabot alert)
* [#1574] Dropped Django 2.x SameSiteNoneCookieMiddlware

**Deprecations**

* [#1441] The ``/api/v1/authentication/session`` endpoint is now deprecated. Use the
  submission-specific endpoint instead.
* [#1453] The  ``/api/v1/submissions/files/upload`` endpoint is now deprecated. Use the
  formio-specific endpoint instead.
* ``Submission.nextStep`` is deprecated as it's unused, all the information to determine
  this is available from other attributes.

1.0.8 (2022-05-16)
==================

Bugfix maintenance release

* [#1568] Fixed logic engine crash when form fields are removed while someone is
  filling out the form
* [#1539] Fixed crash when deleting a temporary file upload
* [#1344] Added missing translation for validation error key
* [#1593] Update nginx location rules for fileuploads
* [#1587] Fixed analytics scripts being blocked by the CSP
* Updated to SDK version 1.0.3 with frontend bugfixes
* Fixed API schema documentation for temporary upload GET

1.0.7 (2022-05-04)
==================

Fixed some more reported issues

* [#1492] Fixed crashes when using file upload components with either a maximum filesize
  specified as empty string/value or a value containing spaces.
* [#1550] Fixed form designer partial crash when adding a currency/number component
* Bump uwsgi version
* Ensure uwsgi runs in master process mode
* [#1453] Fixed user feedback for upload handler validation errors
* [#1498] Fixed duplicate payment completion updates being sent by registration backend(s)

1.0.6 (2022-04-25)
==================

Periodic bugfix release

* Bumped to SDK version 1.0.2 with frontend bugfixes
* Updated DigiD/eHerkenning/eIDAS integration library for breaking changes in some
  brokers per May 1st
* Bumped to latest Django security releases
* [#1493] Fixed form copy admin (bulk/object) actions not copying logic
* [#1489] Fixed layout of confirmation emails
* [#1527] Fixed clearing/resetting the data of fields hidden by server-side logic

1.0.5 (2022-03-31)
==================

Fixed some critical bugs

* [#1466] Fixed crash in submission processing for radio and select fields with numeric values
* [#1464] Fixed broken styles/layout on some admin pages, such as the import form page

1.0.4 (2022-03-17)
==================

Fixed a broken build and security vulnerabilities

* [#1445] ``libexpat`` had some security vulnerabilities patched in Debian which lead to broken
  XML parsing in the StUF-BG prefill plugin. This affected version 1.0.1 through 1.0.3, possibly
  also 1.0.0.

There are no Open Forms code changes, but this release and version bump includes the
newer versions of the fixed OS-level dependencies and updates to Python 3.8.13.

1.0.3 (2022-03-16)
==================

Fixed some more bugs discovered during acceptance testing

* [#1076] Fixed missing regex pattern validation for postcode component
* [#1433] Fixed inclusion/exclusion of components in confirmation emails
* [#1428] Fixed edge case in data processing for email registration backend
* Updated Pillow dependency with CVE-2022-22817 fix
* Bump required SDK release to 1.0.1

1.0.2 (2022-03-11)
==================

Fixed some issues with the confirmation PDF generation

* [#1423] The registration reference is not available yet at PDF generation time,
  removed it from the template
* [#1423] Fixed an issue with static file resolution while rendering PDFs, causing the
  styling to be absent

1.0.1 (2022-03-11)
==================

Fixed some unintended CSS style overrides in the admin.

1.0.0 (2022-03-10)
==================

Final fixes/improvements for the 1.0.0 release

This release pins the formal API v1.0 definition and includes the 1.0.0 version of the
SDK. v1.0.0 is subject to our
`versioning policy <https://open-forms.readthedocs.io/en/latest/developers/versioning.html>`_.

Bugfixes
--------

* [#1376] Fixed straat/woonplaats attributes in Haal Centraal prefill plugin
* [#1385] Avoid changing case in form data
* [#1322] Demo authentication plugins can now only be used by staff users
* [#1395, #1367] Moved identifying attributes hashing to on_completion cleanup stage,
  registrations backends now no longer receive hashed values
* Fixed bug in email registration backend when using new formio formatters
* [#1293, #1179] "signature" components are now proper images in PDF/confirmation email
* Fixed missing newlines in HTML-mail-to-plain-text conversion
* [#1333] Removed 'multiple'/'default value' component options where they don't make sense
* [#1398] File upload size limit is now restricted to integer values due to broken
  localized number parsing in Formio
* [#1393] Prefill data is now validated against tampering if marked as "readonly"
* [#1399] Fixed KVK (prefill) integration by fetching the "basisprofiel" information
* [#1410] Fixed admin session not being recognized by SDK/API for demo auth plugins
* [#840] Fixed hijack functionality in combination with 2FA

  - Hijack and enforced 2FA can now be used together (again)
  - Hijacking and releasing users is now logged in the audit log

* [#1408] Hardened TimelineLogProxy against disappeared content object

New features/improvements
-------------------------

* [#1336] Defined and implemented backend extension mechanism
* [#1378] Hidden components are now easily identifiable in the form builder
* [#940] added option to display 'back to main website' link
* [#1103] Plugin options can now be managed from a friendly user interface in the
  global configuration page
* [#1391] Added option to hide the fieldset header
* [#988] implemented permanently deleting forms after soft-delete
* [#949] Redesigned/styled the confirmation/summary PDF - this now applies the
  configured organization theming

Project maintenance
-------------------

* [#478] Published django-digid-eherkenning to PyPI and replaced the Github dependency.
* [#1381] added targeted elasticapm instrumentation to get better insights in
  performance bottlenecks
* Cleaned up admin overrides CSS in preparation for dark-theme support
* [#1403] Removed the legacy formio formatting feature flag and behaviour

1.0.0-rc.4 (2022-02-25)
=======================

Release candidate 4.

A couple of fixes in the previous release candidates broke new things, and thanks to
the extensive testing some more issues were discovered.

Bugfixes
--------

* [#1337] Made the component key for form fields required
* [#1348] Fixed restoring a form with multiple steps/logics attached
* [#1349] Fixed missing admin-index menu in import form and password change template
* [#1368] Updated translations
* [#1371] Fixed Digid login by upgrading django-digid-eherkenning package

New features
------------

* [#1264] Set up and documented the Open Forms versioning policy
* [#1348] Improved interface for form version history/restore
* [#1363] User uploads as registration email attachments is now configurable
* [#1367] Implemented hashing identifying attributes when they are not actively used

Project maintenance
-------------------

* Ignore some management commands for coverage
* Add (local development) install instruction
* Open redirect is fixed in cookie-consent, our monkeypatch is no longer needed
* Further automation to bundling the correct SDK release in the Open Forms image
  This simplifies deployment quite a bit.
* [#1301] Extensive testing of a new approach to display the submitted data, still opt-in.
* Add more specific Formio component type hints

1.0.0-rc.3 (2022-02-16)
=======================

Release candidate 2 had some more bugfixes.

* [#1254] Fixed columns component to not depend on bootstrap
* Fix missing RELEASE build arg in dockerfile
* Bump elastic-apm preventing container start
* Fix admin login styles after Django 3.2 upgrade
* Do not display version number on admin login page
* Fix dropdown menu styling if the domain switcher is enabled

1.0.0-rc.2 (2022-02-16)
=======================

Second release candidate with various bugfixes and some project tooling improvements

Bugfixes
--------

* [#1207] Fixed excessive remote service calls in prefill machinery
* [#1255] Fixed warnings being displayed incorrectly while form editing
* [#944] Display submission authentication information in logevent logging
* [#1275] Added additional warnings in the form designer for components requiring
  authentication
* [#1278] Fixed Haal Centraal prefill according to spec
* [#1269] Added SESSION_EXPIRE_AT_BROWSER_CLOSE configuration option
* [#807] Implemented a strict Content Security Policy

    - allow script/style assets from own source
    - allow script/style assets from SDK base url
    - allow a limited number of inline script/style via nonce

* Allow for configurable DigiD XML signing
* [#1288] Fixed invalid map component markup
* Update the NUM_PROXIES configuration option default value to protect against
  X-Forwarded-For header spoofing
* [#1285] Remove the multiple option from signature component
* Handle KvK non-unique API roots
* [#1127] Added ``clearOnHide`` configuration option for hidden fields
* [#1222] Fixed visual state when deleting logic rules
* [#1273] Fixed various logs to be readonly (even for superusers)
* [#1280] Fixed reusable definition handling when copying form
* [#1099] Fixed rendering submission data when duplicate labels exist (PDF, confirmation email)
* [#1193] Fixed file upload component/handling

    - configured and documented webserver upload size limit
    - ensured file uploads are not attached to emails but are instead downloadable from
      the backend. A staff account is required for this.
    - ensured individually configured component file size limits are enforced
    - ensured file uploads are deleted from the storage when submission data is pruned/
      stripped from sensitive data

* [#1272] Hardened XML submission export to handle multiple values
* [#1299] Updated to celery 5
* [#1216] Fixed retrieving deleted forms in the API
* Fixed docker-compose with correct non-privileged nginx SDK port numbers
* [#1251] Fixed container file system polution when using self-signed certificates
* Fixed leaking of Form processing configuration
* [#1199] Handle possible OIDC duplicate user email problems
* [#1018] WCAG added title attribute to header logo
* [#1330] Fixed dealing with component/field configuration changes when they are used
  in logic
* [#1296] Refactor warning component
* Bumped to Django 3.2 (LTS) and update third party packages

New features
------------

* [#1291] Privacy policy link in footer is now configurable

Documentation
-------------

* Clarified cookies and analytics documentation
* Document stable release branches
* Document bundled SDK image tag in release process

Project maintenance
-------------------

* Cleaned up a TODO in logging.logevent
* Fixed sourcing the build/version information to display in the admin
* Ensure that the SDK build bundled in the backend image is correctly versioned
* Upgraded dependencies with security releases

    - Django
    - Pillow

* Upgraded frontend dependencies with security releases (dev tooling)
* Replaced gulp-based frontend dev stack with pure webpack
* Bumped to django-yubin 1.7, drops pyzmail36 transitive dep
* Deleted a bunch of dead (test) code
* Improved DigiD/eHerkenning settings


1.0.0-rc.1 (2022-01-28)
=======================

* Updated several translations
* Updated documentation with advanced JSON-logic examples
* Updated documentation for the form basics
* Updated documentation with versioning and release policies
* [#1243] Fixed an admin bug that made form definitions crash
* [#1206] Fixed StUF-BG configuration check to allow empty responses
* [#1208] Fixed exports to use dynamic file upload URLs
* [#1247] Updated admin menu structure to fit on screens (1080 pixels height) again
* [#1237] Updated admin version info to show proper version
* [#1227] Removed option to allow multiple options in selectboxes
* [#1225] Updated admin formbuilder: Moved some fields to a new catagory
* [#1123] Updated admin formbuilder: Fieldset now has a logic tab
* [#1212] Updated prefilling to be more graceful
* [#986] Fixed form definitons to handle unique URLs better
* [#1217] Fixed import with duplicate form slug
* [#1168] Fixed import with "form specific email" option enabled
* [#1214] Fixed eIDAS ID storage field
* [#1213] Added prefill tab to date field
* [#1019] Added placeholder for text field
* [#1083] Avoid checking logic on old data


1.0.0-rc.0 (2022-01-17)
=======================

First release candidate of Open Forms.

Only critical bugs and security issues are considered release blockers. Other
improvements and bug fixes will go into a minor or patch release.

Features
--------

* User-friendly admin interface for staff users to design forms to be filled out by
  end users
* RESTful JSON API to manage/administer forms AND end-user sessions
* Javascript SDK to render forms

    - Built-in into the backend with pages to host forms
    - Embeddable in third party websites

* Authentication module for forms, with plugins:

    - DigiD
    - eHerkenning
    - eIDAS
    - mock/simulation equivalents to try out flows

* Optional Registrations module for forms - form data is sent to a plugin of choice:

    - ZGW APIs - REST/JSON binding with Dutch national standard for "Zaakgericht werken"
      (supports Open Zaak out of the box)
    - StUF-ZKN - StUF/SOAP binding with Dutch national standard for "Zaakgericht werken"
    - Camunda process engine, with detailed variable management options
    - Email - send the data and attachments to a backoffice via email.
    - Microsoft Sharepoint file store
    - Objects API - REST/JSON binding with the Dutch national standard

* Payments module

    - Connect products and pricing information
    - Ogone payment provider with support for multiple accounts

* Appointments module, with plugins for:

    - JCC Afspraken
    - QMatic Appointments

* Prefilling of data through plugins:

    - StUF-BG - StUF/SOAP Dutch national standard for retrieving person details
    - KvK - fetch company information from the Chamber of Commerce APIs
    - HaalCentraal - REST/JSON binding to Dutch national standard for retrieving person details

* GDPR/AVG support built-in

    - mark data fields as sensitive data
    - automatically scheduled and configurable removal of (privacy-sensitive) data
    - automatic logging of data access events

* NLX support
* Extensive dynamic and real-time logic options, based on the data the end-user is
  entering.
* User-administration suitable for your environment

    - Local user database
    - Integration with OpenID Connect (ADFS, Azure AD, KeyCloak...)
    - (Optional) Two-Factor authentication via OTP
    - RBAC with default roles
    - Multi-domain/tenant support

* Internationalization and localization support

    - Dutch
    - English

Meta features
-------------

Open Forms is a project aiming to set an example for the industry by also focusing
on aspects that are not directly visible in the product itself, but rather invest
in the future quality by following best practices.

* Open Source
* Strong focus on security
* Strong focus on codebase quality
* Automated (regression) testing to ensure codebase quality
* Publicly available documentation, both functional and technical
* Automated and public publishing of build artifacts
* TPM audited
* Scalable processing of data
* Containerized deployment, suitable for cloud and on-premise hosting and tuning
