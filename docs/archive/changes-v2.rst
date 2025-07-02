=============
Open Forms v2
=============

Changes for major version 2 of Open Forms.

.. warning::

   The versions listed here no longer receive bugfixes, they are end-of-life. For
   maintained versions, see :ref:`changelog`.

2.4.10 (2024-06-19)
===================

Final bugfix release in the ``2.4.x`` series.

* [:backend:`4403`] Fixed broken submission PDF layout when empty values are present.

2.4.9 (2024-06-14)
==================

Bugfix release fixing some issues (still) in 2.4.8

Note that 2.4.8 was never published to Docker Hub.

* [:backend:`4338`] Fixed prefill for StUF-BG with SOAP 1.2 not properly extracting attributes.
* [:backend:`4390`] Fixed regression introduced by #4368 that would break template variables in
  hyperlinks inside WYSIWYG content.

2.4.8 (2024-06-14)
==================

Bugfix release

* [:backend:`4255`] Fixed a performance issue in the confirmation PDF generation when large
  blocks of text are rendered.
* [:backend:`4368`] Fixed URLs to the same domain being broken in the WYSIWYG editors.
* [:backend:`4362`] Fixed a crash in the form designer when a textfield/textarea allows multiple
  values in forms with translations enabled.

2.4.7 (2024-05-13)
==================

Bugfix release

* [:backend:`4079`] Fixed metadata retrieval for DigiD failing when certificates signed by the G1 root are used.
* [:backend:`4103`] Fixed incorrect appointment details being included in the submission PDF.
* [:backend:`4145`] Fixed the payment status not being registered correctly for StUF-ZDS.
* [:backend:`3964`] Toggling visibility with frontend logic and number/currency components leads to fields being emptied.
* [:backend:`4205`] The CSP ``form-action`` directive now allows any ``https:`` target,
  to avoid errors on eHerkenning login redirects.

2.4.6 (2024-03-14)
==================

Bugfix release

* [:backend:`3863`] Fixed the generated XML for StUF-BG requests when retrieving partners/children.
* [:backend:`3858`] Fixed a race condition that would manifest during parallel file uploads,
  leading to permission errors.
* [:backend:`3864`] Fixed handling of StUF-BG responses where one partner is returned.
* [:backend:`1052`] Upgraded DigiD/eHerkenning library.
* [:backend:`3975`, :backend:`3052`] Fixed legacy service fetch configuration being picked over the intended
  format.
* [:backend:`3881`] Fixed updating a re-usable form definition in one form causing issues in other
  forms that also use this same form definition.

2.4.5 (2024-02-06)
==================

Bugfix release

This release addresses a security weakness. We believe there was no way to actually
exploit it.

* [:cve:`CVE-2024-24771`] Fixed (non-exploitable) multi-factor authentication weakness.
* [:sdk:`642`] Fixed DigiD error message via SDK patch release.
* Upgraded dependencies to their latest available security releases.

2.4.4 (2024-01-30)
==================

Hotfix release to address an upgrade problem.

* Bump packages to their latest security releases
* [:backend:`3616`] Fixed broken PDF template for appointment data.
* Fixed a broken migration preventing upgrading to 2.4.x.

2.4.3 (2024-01-12)
==================

Periodic bugfix release

* [:backend:`3656`] Fixed incorrect DigiD error messages being shown when using OIDC-based plugins.
* [:backend:`3692`] Fixed crash when using OIDC DigiD login while logged into the admin interface.
* [:backend:`3744`] Fixed conditionally marking a postcode component as required/optional.

  .. note:: We cannot automatically fix existing logic rules. For affected forms, you
     can remove and re-add the logic rule action to modify the 'required' state.

* [:backend:`3704`] Fixed the family members component not retrieving the partners when using
  StUF-BG as data source.
* [:backend:`2710`] Added missing initials (voorletters) prefill option for StUF-BG plugin.
* Fixed failing docs build by disabling/changing some link checks.

2.4.2 (2023-12-08)
==================

Periodic bugfix release

* [:backend:`3625`] Fixed crashes during StUF response parsing when certain ``nil`` values are
  present.
* Updated CSP ``frame-ancestors`` directive to be consistent with the ``X-Frame-Options``
  configuration.
* [:backend:`3605`] Fixed unintended number localization in StUF/SOAP messages.
* [:backend:`3613`] Fixed submission resume flow not sending the user through the authentication
  flow again when they authenticated for forms that have optional authentication. This
  unfortunately resulted in hashed BSNs being sent to registration backends, which we
  can not recover/translate back to the plain-text values.
* [:backend:`3647`] Fixed a backend (logic check) crash when non-parsable time, date or datetime
  values are passed. The values are now ignored as if nothing was submitted.

2.4.1 (2023-11-14)
==================

Hotfix release

* [:backend:`3604`] Fixed a regression in the Objects API and ZGW API's registration backends. The
  required ``Content-Crs`` request header was no longer sent in outgoing requests after
  the API client refactoring.

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

    * [:backend:`586`] Added support for Suwinet as a prefill plugin.
    * [:backend:`3188`] Added better error feedback when adding form steps to a form with
      duplicate keys.
    * [:backend:`3351`] The family members component can now be used to retrieve partner
      information instead of only the children (you can select children, partners or
      both).
    * [:backend:`2953`] Added support for durations between dates in JSON-logic.
    * [:backend:`2952`] Form steps can now initially be non-applicable and dynamically be made
      applicable.

* [:backend:`3499`] Accepting/declining cookies in the notice now no longer refreshes the page.
* [:backend:`3477`] Added CSP ``form-action`` directives, generated via the DigiD/eHerkenning
  and Ogone configuration.
* [:backend:`3524`] The behaviour when retrieving family members who don't have a BSN is now
  consistent and well-defined.
* [:backend:`3566`] Replaced custom buttons with utrecht-button components.

**Bugfixes**

* [:backend:`3527`] Duplicated form steps in a form are now blocked at the database level.
* [:backend:`3448`] Fixed emails not being sent with a subject line > 70 characters.
* [:backend:`3448`] Fixed a performance issue when upgrading the underlying email sending library
  if you have many (queued) emails.
* [:backend:`2629`] Fixed array variable inputs in the form designer.
* [:backend:`3491`] Fixed slowdown in the form designer when created a new or loading an existing
  form when many reusable form definitions exist.
* [:backend:`3557`] Fixed a bug that would not display the available document types when
  configuring the file upload component.
* [:backend:`3553`] Fixed a crash when validating a ZWG registration backend when no default
  ZGW API group is set.
* [:backend:`3537`] Fixed validator plugin list endpoint to properly converting camelCase params
  into snake_case.
* [:backend:`3467`] Fixed crashes when importing/copying forms with ``null`` in the prefill
  configuration.
* [:backend:`3580`] Fixed incorrect attributes being sent in ZWG registration backend when
  creating the rol/betrokkene.

**Project maintenance**

* Upgraded various dependencies with the most recent (security) releases.
* [:backend:`2958`] Started the rework for form field-level translations, the backend can now
  handle present and future formats.
* [:backend:`3489`] All API client usage is updated to a new library, which should lead to a
  better developer experience and make it easier to get better performance when making
  (multiple) API calls.
* Bumped pip-tools for latest pip compatibility.
* [:backend:`3531`] Added a custom migration operation class for formio component transformations.
* [:backend:`3531`] The time component now stores ``minTime``/``maxTime`` in the ``validate``
  namespace.
* Contributed a number of library extensions back to the library itself.
* Squashed the variables app migrations.
* [:backend:`2958`] Upgraded (experimental) new form builder to 0.8.0, which uses the new
  translations format.
* Fixed test suite which didn't take DST into account.
* [:backend:`3449`] Documented the (new) co-sign flow.

2.4.0-alpha.0 (2023-10-02)
==========================

Upgrade procedure
-----------------

.. warning::

    Ensure you upgrade to Open Forms 2.3.0 before upgrading to the 2.4 release series.


Detailed changes
----------------

**New features**

* [:backend:`3185`] Added Haal Centraal: HR prefill plugin to official extensions build.
* [:backend:`3051`] You can now schedule activation/deactivation of forms.
* [:backend:`1884`] Added more fine-grained custom errors for time field components.
* More fields irrelevant to appointment forms are now hidden in the form designer.
* [:backend:`3456`] Implemented multi-product and multi-customer appointments for Qmatic.
* [:backend:`3413`] Improved UX by including direct hyperlinks to the form in co-sign emails (
  admins can disable this behaviour).
* [:backend:`3328`] Qmatic appointments plugin now support mTLS.
* [:backend:`3481`] JSON-data sent to the Objects API can now optionally be HTML-escaped for when
  downstream systems fail to do so.
* [:backend:`2688`] Service-fetch response data is now cached & timeouts are configurable on the
  configuration.
* [:backend:`3443`] You can now provide custom validation error messages for date fields
* [:backend:`3402`] Added tracing information to outgoing emails so we can report on failures.
* [:backend:`3402`] Added email digest to report (potential) observed problems, like email
  delivery failures.

**Bugfixes**

* [:backend:`3139`] Fixed form designers/admins not being able to start forms in maintenance mode.
* Fixed the version of openapi-generator.
* Bumped to latest Django patch release.
* [:backend:`3447`] Fixed flash of unstyled form visible during DigiD/eHerkenning login flow.
* [:backend:`3445`] Fixed not being able to enter more decimals for latitude/longitude in the map
  component configuration.
* [:backend:`3423`] Fixed import crash with forms using service fetch.
* [:backend:`3420`] Fixed styling of cookie overview page.
* [:backend:`3378`] Fixed copying forms with logic that triggers from a particular step crashing
  the logic tab.
* [:backend:`3470`] Fixed form names with slashes breaking submission generation.
* [:backend:`3437`] Improved robustness of outgoing request logging solution.
* Included latest SDK bugfix release.
* [:backend:`3393`] Fixed duplicated form field label in eHerkenning configuration.
* [:backend:`3375`] Fixed translation warnings being shown for optional empty fields.
* [:backend:`3187`] Fixed UI displaying re-usable form definitions that are already in the form.
* [:backend:`3422`] Fixed logic tab crashes when variables/fields are deleted and added a generic
  error boundary with troubleshooting information.
* [:backend:`3308`] Fixed new installations having all-English default messages for translatable
  default content.
* [:backend:`3492`] Fixed help text referring to old context variable.
* [:backend:`3437`] Made request logging solution more robust to prevent weird crashes.
* [:backend:`3279`] Added robustness to admin pages making requests to external hosts.

**Project maintenance**

* [:backend:`3190`] Added end-to-end tests for DigiD and eHerkenning authentication flows with a
  real broker.
* Mentioned extension requirements file in docs.
* [:backend:`3416`] Refactored rendering of appointment data  in confirmation PDF.
* [:backend:`3389`] Stopped building test images, instead use symlinks or git submodules in your
  (CI) pipeline.
* Updated appointments documentation.
* Moved service factory to more general purpose location.
* [:backend:`3421`] Updated local infrastructure for form exports and clarified language to manage
  import expectations.
* Updated version of internal experimental new formio-builder.
* Prevent upgrades from < 2.3.0 to 2.4.
* Squashed *a lot* of migrations.
* Removed dead/obsolete "default BSN/KVK" configuration - no code used this anymore since
  a while.
* [:backend:`3328`] Initial rework of API clients to generically support mTLS and other
  connection parameters.
* Fixed test cleanup for self-signed certs support, causing flaky tests.
* Moved around a bunch of testing utilities to more appropriate directories.
* [:backend:`3489`] Refactored all API-client usage into common interface.
* Fixed tests failing with dev-settings.
* Bumped dependencies with security releases.

2.3.9 (2024-05-08)
==================

Final bugfix release in the ``2.3.x`` series.

* Upgraded Pillow to latest bugfix release.
* [:backend:`4145`] Fixed StUF-ZDS not sending up-to-date payment status on registration after payment.

2.3.8 (2024-03-14)
==================

Bugfix release

* [:backend:`3863`] Fixed the generated XML for StUF-BG requests when retrieving partners/children.
* [:backend:`3858`] Fixed a race condition that would manifest during parallel file uploads,
  leading to permission errors.
* [:backend:`3975`, :backend:`3052`] Fixed legacy service fetch configuration being picked over the intended
  format.
* [:backend:`3881`] Fixed updating a re-usable form definition in one form causing issues in other
  forms that also use this same form definition.

2.3.7 (2024-02-06)
==================

Bugfix release

This release addresses a security weakness. We believe there was no way to actually
exploit it.

* [:cve:`CVE-2024-24771`] Fixed (non-exploitable) multi-factor authentication weakness.
* [:sdk:`642`] Fixed DigiD error message via SDK patch release.
* Upgraded dependencies to their latest available security releases.

2.3.6 (2024-01-12)
==================

Periodic bugfix release

* [:backend:`3656`] Fixed incorrect DigiD error messages being shown when using OIDC-based plugins.
* [:backend:`3692`] Fixed crash when using OIDC DigiD login while logged into the admin interface.
* [:backend:`3744`] Fixed conditionally marking a postcode component as required/optional.

  .. note:: We cannot automatically fix existing logic rules. For affected forms, you
     can remove and re-add the logic rule action to modify the 'required' state.

* [:backend:`3704`] Fixed the family members component not retrieving the partners when using
  StUF-BG as data source.
* [:backend:`2710`] Added missing initials (voorletters) prefill option for StUF-BG plugin.
* Fixed failing docs build by disabling/changing some link checks.

2.3.5 (2023-12-12)
==================

Periodic bugfix release

* [:backend:`3625`] Fixed crashes during StUF response parsing when certain ``nil`` values are
  present.
* [:backend:`3605`] Fixed unintended number localization in StUF/SOAP messages.
* [:backend:`3613`] Fixed submission resume flow not sending the user through the authentication
  flow again when they authenticated for forms that have optional authentication. This
  unfortunately resulted in hashed BSNs being sent to registration backends, which we
  can not recover/translate back to the plain-text values.

2.3.4 (2023-11-09)
==================

Hotfix release

* Upgraded bundled SDK version
* [:backend:`3585`] Fixed a race condition when trying to send emails that haven't been saved to
  the DB yet.
* [:backend:`3580`] Fixed incorrect attributes being sent in ZWG registration backend when
  creating the rol/betrokkene.

2.3.3 (2023-10-30)
==================

Periodic bugfix release

* [:backend:`3279`] Added robustness to the admin that retrieves data from external APIs.
* [:backend:`3527`] Added duplicated form steps detection script and added it to the upgrade check
  configuration.
* [:backend:`3448`] Applied mail-queue library patches ahead of their patch release.
* [:backend:`3557`] Fixed a bug that would not display the available document types when
  configuring the file upload component.
* Bumped dependencies to their latest security fixes.

2.3.2 (2023-09-29)
==================

Hotfix for WebKit based browsers

* [:backend:`3511`] Fixed user input "flickering" in forms with certain (backend) logic on Safari
  & other WebKit based browsers (via SDK patch).

2.3.1 (2023-09-25)
==================

Periodic bugfix release

* [:backend:`3139`] Fixed form designers/admins not being able to start forms in maintenance mode.
* Fixed the version of openapi-generator.
* Bumped to latest Django patch release.
* [:backend:`3447`] Fixed flash of unstyled form visible during DigiD/eHerkenning login flow.
* [:backend:`3445`] Fixed not being able to enter more decimals for latitude/longitude in the map
  component configuration.
* [:backend:`3423`] Fixed import crash with forms using service fetch.
* [:backend:`3420`] Fixed styling of cookie overview page.
* [:backend:`3378`] Fixed copying forms with logic that triggers from a particular step crashing
  the logic tab.
* [:backend:`3470`] Fixed form names with slashes breaking submission generation.
* [:backend:`3437`] Improved robustness of outgoing request logging solution.
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

* [:backend:`2174`] Added geo-search (using the Kadaster Locatieserver by default) for the map
  component.
* [:backend:`2017`] The form step slug is now moved from the form definition to the form step
  itself, allowing you to use the same slug for a step in different forms.
* [:backend:`3332`] Use the JCC configuration for the latest available appointment date.
* [:backend:`3332`] When selecting a product, this choice is now taken into account to populate
  the list of available additional products.
* [:backend:`3321`] Added support for new appointment flow to confirmation emails.
* [:backend:`1884`] Added custom error message support for invalid times.
* [:backend:`3203`, :backend:`3372`] Added an additional checkbox for truth declaration before submitting a
  form, in addition to the privacy policy. You can now also configure these requirements
  per-form instead of only the global configuration.
* [:backend:`1889`] Added the ``current_year`` static variable.
* [:backend:`3179`] You can now use logic to select an appropriate registration backend.
* [:backend:`3299`] Added Qmatic support for the new appointments.

**Bugfixes**

* [:backend:`3223`] Fixed some content translations not being properly translated when copying a form.
* [:backend:`3144`] Fixed file download links being absent in registration emails when the file
  upload is nested inside a group.
* [:backend:`3278`] Fixed a crash when the DigiD provider does not provide a sector code in the
  SAML Artifact. We now assume it's BSN (as opposed to sofinummer).
* [:backend:`3084`] Fixed ``inp.heeftAlsKinderen`` missing in scope of StUF-BG request.
* [:backend:`3302`] Fixed race condition causing uploaded images not be resized.
* [:backend:`3332`] Ensured that naive, localized appointment times are sent to JCC.
* [:backend:`3309`] Added a missing automatic appointment configuration upgrade.
* Fixed broken inline images in outgoing emails and loss of additional parameters.
* [:backend:`3322`] Fixed the cancel-appointment flow for new appointments.
* [:backend:`3327`] Fixed the backend markup and styling of radio fields.
* [:backend:`3319`] Fixed forms possibly sending a DigiD SAML request without assurance level due
  to misconfiguration.
* Fixed passing querystring parameter to service fetch.
* [:backend:`3277`] Added a workaround to use form variable values containing spaces in templates.
* [:backend:`3292`] Fixed dark mode suffixes in the form builder.
* [:backend:`3286`] Fixed data normalization for customer details in new appointments.
* [:backend:`3368`] Fixed a crash when empty values are returned from StUF-BG.
* [:backend:`3310`] Fixed alignment issue in confirmation PDF for accepted privacy policy statement.

**Project maintenance**

* Changed the fail-fast behaviour of the end-to-end tests to reduce the flakiness impact.
* We now build Docker images based on the latest available Python patch release again.
* [:backend:`3242`] Added more profiling to investigate test flakiness.
* Upgraded the container base image from Debian Bullseye to Bookworm.
* [:backend:`3127`] Rework developer tooling to generate code from an API specification.
* Fixed JQ documentation URL for sorting.
* Bump dependencies reported to have vulnerabilities (via @dependabot).
* Improved typing of plugins and plugin registries.
* Fixed incorrect Authentication header in the Objects API documentation.
* [:backend:`3049`] Upgraded more libraries to prepare for Django 4.2

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

* [:backend:`2471`] Added a new appointments flow next to the existing one.

  .. note::

     You can opt-in to this flow by enabling the feature flag in the global
     configuration and then mark a form as being an "appointment form". Currently
     only JCC is fully implemented. Note that the entire feature has "preview"
     status and is only suitable for testing (with known issues).

  * [:backend:`3193`] Added API endpoint to retrieve required customer fields meta-information.

    * Implemented retrieving this for JCC plugin.
    * Implemented configuring the fields in the admin for QMatic.

  * Added appointment meta-information to form detail enpdoint.
  * Validate the input data against the configured plugin.
  * Appointment submissions now have their own data model and entry in the admin.
  * Extended existing endpoints to support retrieving locations/dates/times for
    multiple products.
  * Defining an appointment form disables/clears the irrelevant form designer aspects.
  * [:backend:`3275`] Added support for multi-product appointments in JCC.

* [:backend:`3215`] Support prefilling data of the authorisee with DigiD machtigen and
  eHerkenning Bewindvoering.

* Form designer

  * [:backend:`1508`] Added hidden option for legacy cosign component.
  * [:backend:`1882`] Added minimum/maximum value options to the currency component.
  * [:backend:`1892`] Added tooltips to (relevant) form components in the designer.
  * [:backend:`1890`] Added support for upload file name templating, you can now add pre- and
    suffixes.
  * [:backend:`2175`] You can now configure the default zoom level and initial map center for the
    map component, with a global default.
  * [:backend:`3045`] You can now provide a suffix for number components, e.g. to hint about the
    expected unit.

* [:backend:`3238`] The StUF-ZDS registration backend now has well-defined behaviour for
  non-primitive variable values, including user-defined variables.

**Bugfixes**

* Fixed testing availability of OIDC auth endpoint with HEAD requests (now uses GET).
* [:backend:`3195`] Fixed hardcoded ``productaanvraag_type`` in default Objects API template to
  use configuration option.
* [:backend:`3182`] Fixed importing forms from before 2.2.0 due to missing
  ``{% cosign_information %}`` tag in confirmation email templates.
* [:backend:`3211`] Fixed CSP violation in Piwik Pro analytics script, causing no analytics to be
  tracked.
* [:backend:`3161`] Fixed not being able to reset form-specific data removal settings to the
  empty value so that the global configuration is used again.
* [:backend:`3219`] Fixed saved uploads not being deleted when the user goes back to the file and
  removes the upload again.
* Fixed CI builds (bump PyYAML, docs build).
* [:backend:`3258`] Fixed labels for Haal Centraal prefill attributes.
* Fixed the broken Token Exchange extension (pre-request plugins) in the Haal Centraal
  plugin.
* [:backend:`3130`] Fixed a crash when copying form-definitions with very long names.
* [:backend:`3166`] Fixed Haal Centraal plugin configuration test.
*

**Project maintenance**

* Bumped dependencies to get their latest security fixes.
* Removed MacOS CI job due to broken system-level dependencies.
* Added utility to profile code with ``cProfile``.
* Sped up tests by pre-loading the OAS schema and worked on other flakiness issues.
* [:backend:`3242`] Set up a CI profile for hypothesis.
* [:backend:`586`] Extracted the SOAP service configuration from the StUF app into its own app.
* [:backend:`3189`] Refactored authentication plugins ``provides_auth`` datatypes.
* [:backend:`3049`] Upgraded a number of dependencies in preparation for Django 4.2:

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

2.2.10 (2024-02-27)
===================

Final release in the 2.2.x series.

* [:backend:`3863`] Fixed the generated XML for StUF-BG requests when retrieving partners/children.
* [:backend:`3858`] Fixed a race condition that would manifest during parallel file uploads,
  leading to permission errors.

2.2.9 (2024-02-06)
==================

Bugfix release

This release addresses a security weakness. We believe there was no way to actually
exploit it.

* [:cve:`CVE-2024-24771`] Fixed (non-exploitable) multi-factor authentication weakness.
* [:sdk:`642`] Fixed DigiD error message via SDK patch release.
* Upgraded dependencies to their latest available security releases.

2.2.8 (2024-01-12)
==================

Periodic bugfix release

* [:backend:`3656`] Fixed incorrect DigiD error messages being shown when using OIDC-based plugins.
* [:backend:`3692`] Fixed crash when using OIDC DigiD login while logged into the admin interface.
* [:backend:`3744`] Fixed conditionally marking a postcode component as required/optional.

  .. note:: We cannot automatically fix existing logic rules. For affected forms, you
     can remove and re-add the logic rule action to modify the 'required' state.

* [:backend:`3704`] Fixed the family members component not retrieving the partners when using
  StUF-BG as data source.
* [:backend:`2710`] Added missing initials (voorletters) prefill option for StUF-BG plugin.
* Fixed failing docs build by disabling/changing some link checks.

2.2.7 (2023-12-12)
==================

Periodic bugfix release

* [:backend:`3625`] Fixed crashes during StUF response parsing when certain ``nil`` values are
  present.
* [:backend:`3605`] Fixed unintended number localization in StUF/SOAP messages.
* [:backend:`3613`] Fixed submission resume flow not sending the user through the authentication
  flow again when they authenticated for forms that have optional authentication. This
  unfortunately resulted in hashed BSNs being sent to registration backends, which we
  can not recover/translate back to the plain-text values.

2.2.6 (2023-11-09)
==================

Hotfix release

* Upgraded bundled SDK version
* [:backend:`3580`] Fixed incorrect attributes being sent in ZWG registration backend when
  creating the rol/betrokkene.

2.2.5 (2023-10-30)
==================

Periodic bugfix release

* [:backend:`3279`] Added robustness to the admin that retrieves data from external APIs.
* Bumped dependencies to their latest security fixes.

2.2.4 (2023-09-29)
==================

Hotfix for WebKit based browsers

* [:backend:`3511`] Fixed user input "flickering" in forms with certain (backend) logic on Safari
  & other WebKit based browsers (via SDK patch).

2.2.3 (2023-09-25)
==================

Periodic bugfix release

* [:backend:`3139`] Fixed form designers/admins not being able to start forms in maintenance mode.
* Fixed the version of openapi-generator.
* Bumped to latest Django patch release.
* [:backend:`3447`] Fixed flash of unstyled form visible during DigiD/eHerkenning login flow.
* [:backend:`3423`] Fixed import crash with forms using service fetch.
* [:backend:`3420`] Fixed styling of cookie overview page.
* [:backend:`3378`] Fixed copying forms with logic that triggers from a particular step crashing
  the logic tab.
* [:backend:`3470`] Fixed form names with slashes breaking submission generation.
* [:backend:`3437`] Improved robustness of outgoing request logging solution.
* Included latest SDK bugfix release.

2.2.2 (2023-08-24)
==================

Periodic bugfix release

* [:backend:`3319`] Fixed forms possibly sending a DigiD SAML request without assurance level due
  to misconfiguration.
* [:backend:`3358`] Fixed display of appointment time in correct timezone.
* [:backend:`3368`] Fixed a crash when empty values are returned from StUF-BG.
* Fixed JQ documentation URL for sorting.

2.2.1 (2023-07-26)
==================

Periodic bugfix release

* Fixed testing availability of OIDC auth endpoint with HEAD requests (now uses GET).
* [:backend:`3195`] Fixed hardcoded ``productaanvraag_type`` in default Objects API template to
  use configuration option.
* [:backend:`3182`] Fixed importing forms from before 2.2.0 due to missing
  ``{% cosign_information %}`` tag in confirmation email templates.
* [:backend:`3216`] Fixed setting the Piwik Pro SiteID parameter in the analytics scripts.
* [:backend:`3211`] Fixed CSP violation in Piwik Pro analytics script, causing no analytics to be
  tracked.
* [:backend:`3161`] Fixed not being able to reset form-specific data removal settings to the
  empty value so that the global configuration is used again.
* [:backend:`3219`] Fixed saved uploads not being deleted when the user goes back to the file and
  removes the upload again.
* Fixed CI builds (bump PyYAML, docs build).
* [:backend:`3258`] Fixed labels for Haal Centraal prefill attributes.
* [:backend:`3301`] Fixed crash on DigiD authentication with brokers not returning sectoral codes.
* [:backend:`3144`] Fixed missing links to uploads in the registration e-mails when the field is
  inside a container (fieldset, repeating group).
* [:backend:`3302`] Fixed an issue causing uploaded images not to be resized.
* [:backend:`3084`] Fixed ``inp.heeftAlsKinderen`` missing from certain StUF-BG requests.
* Bumped dependencies to get their latest security fixes
* Fixed the broken Token Exchange extension (pre-request plugins) in the Haal Centraal
  plugin.
* Removed MacOS CI job due to broken system-level dependencies.

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

We've added a graphical tool to edit `design token <https://nldesignsystem.nl/handboek/huisstijl/design-tokens/>`_
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

  * [:backend:`2680`] Added API endpoint to expose available services for service fetch.
  * [:backend:`2661`, :backend:`2693`, :backend:`2834`, :backend:`2835`] Added user friendly UI to configure "external data retrieval".
  * [:backend:`2681`] Added logic logging of service fetch to allow better debugging of form logic.
  * [:backend:`2694`] Updated interpolation format to double bracket, making it possible to use
    Django template engine filters.

* [:backend:`1530`] Introduced a new co-sign component

  * Implemented a new flow for co-signing so that the co-signer receives a request via
    email.
  * The submission is only registered when co-signing is completed.
  * Ensure the co-signer also receives the confirmation email.
  * The existing component is deprecated.

* Background task processing

  * [:backend:`2927`] Added Celery worker monitoring tooling (for devops/infra).
  * [:backend:`3068`] Added soft and hard task timeout settings for background workers.

* [:backend:`2826`] The form builder now validates the format of dates in logic rules.
* [:backend:`2789`] The submission pause/save modal text is now configurable.
* [:backend:`2872`] The registration flow is reworked to have a pre-registration step, e.g. to
  reserve a "zaaknummer" before creating the case.
* [:backend:`2872`] The email registration plugin can now include the registration reference and
  any other submission variables.
* [:backend:`2872`] You can now override subject and body templates for the registration email
* [:backend:`2957`] Added editor to simplify theming an instance instead of editing JSON.
* [:backend:`2444`] It's now possible to hide non-applicable steps in the progress indicator
  rather than greying them out.
* [:backend:`2946`] It's now possible to overwrite the confirmation email subject and content
  templates individually.
* [:backend:`2343`] Added option to hide the label of a repeating group.
* [:backend:`3004`] You can now disable form pausing.
* [:backend:`1879`] Relevant validation plugins are now filtered per component type in the form
  designer.
* [:backend:`3031`] Increased the size of Objects API registration plugin configuration form fields.
* [:backend:`2918`] Added alternative Formio builder implementation, opt-in via a feature flag.
* [:backend:`1424`] The form submission reference is now included in the confirmation PDF.
* [:backend:`2845`] Added option to include content component in submission summary.
* [:backend:`2809`] Made the link title for downloading the submission report configurable.
* [:backend:`2762`] Added (opt-in) logging for outgoing requests to assist with configuration
  troubleshooting.
* [:backend:`2859`] You can now configure multiple sets of ZGW APIs and configure per form where
  documents need to be uploaded.
* [:backend:`2606`] Added support for Haal Centraal BRP Personen v2.
* [:backend:`2852`] The Objects API registration backend data is now a template, configurable per
  form.
* [:backend:`2860`] Level of assurance for DigiD and eHerkenning/eIDAS is now configurable per form.

**Bugfixes**

* [:backend:`2804`] Fixed the "static variables" not being available in confirmation template
  rendering.
* [:backend:`2821`] Fixed broken "Map" component configuration screen.
* [:backend:`2819`] Fixed the key and translations of the password field not automatically
  updating with entered content (label and other translatable fields).
* [:backend:`2785`] Fixed attribute hashing on submission suspend
* [:backend:`2822`] Fixed date components being interpreted as datetimes instead of dates.
* Fixed misalignment for file upload preview in form builder.
* [:backend:`2820`] Fixed translations not registering initially when adding a component to a new
  form step.
* [:backend:`2838`] Fixed hidden selectboxes field triggering premature validation of required fields.
* [:backend:`2791`] Fixed long words overflowing in the confirmation PDF.
* [:backend:`2842`] Fixed analytics CSP-integration resulting in a misconfigured policy.
* [:backend:`2851`] Fixed importing a form while the admin UI is set to English resulting in
  incorrect form translation mappings.
* [:backend:`2850`] Fixed a crash in the AVG log viewer when certain log records of deleted
  submissions are displayed.
* [:backend:`2844`] Fixed validation errors for submission confirmation email not being displayed
  in the form designer.
* Fixed unique component key suffix generation on a newly added component.
* [:backend:`2874`] Fixed "repeating group" component group label not being translated.
* [:backend:`2888`] Fixed a crash when using file fields and hidden repeating groups at the same
  time
* [:backend:`2888`] Fixed a crash when using file fields and repeating groups with numbers inside
* [:backend:`2889`] Fix the focus jumps of the content component in the admin by re-implement the
  component translations machinery.
* [:backend:`2911`] Make validation of .heic and .heif files more lenient.
* [:backend:`2893`] A minimal fix to prevent crashes of the celery task logging the evaluation of
  logic rules.
* [:backend:`2942`] Fixed "undefined" being displayed in the co-signing component configuration.
* [:backend:`2945`] Fixed logic rule variables inadvertedly being cleared when adding a new
  user defined variable
* [:backend:`2947`] Added missing translatable error messages for number components.
* [:backend:`2877`] Fixed admin crash on misconfigured ZGW services.
* [:backend:`2900`] Fixed inconsistent frontend logic involving checkboxes.
* [:backend:`2716`] Added missing co-sign identifier (BSN) to PDF submission report.
* [:backend:`2849`] Restored ability to import forms using form logic in the pre-2.0 format.
* [:backend:`2632`] Fixed crash during submission data pruning when submissions point to form
  steps that have been deleted
* [:backend:`2980`] Fixed file upload component not using config overwrites when registering
  with the objects API backend.
* [:backend:`2983`] Fixed broken StUF-ZDS registration for some vendors due to bad refactor
* [:backend:`2977`] Fixed StUF postcode not being uppercase.
* [:backend:`2963`] Fixed global configuration templates being reset to their default values.
* [:backend:`3007`] Fixed worfklows where < 2.1 form exports are imported and edited in the admin.
* [:backend:`2875`] Fixed another SiteImprove analytics bug where only the path was sent instead
  of the full URL.
* [:backend:`1959`] Fixed invalid link to resume form after pausing and resuming multiple times.
* [:backend:`3025`] Fixed resuming a form redirecting to an invalid URL.
* [:backend:`2895`] Fixed WYSIWYG colors missing when filling out a form while logged in as staff user.
* [:backend:`3015`] Fixed invalid URLs being generated to resume the form from WYSIWYG content.
* [:backend:`3040`] Fixed file-upload validation errors being user-unfriendly.
* [:backend:`2970`] Fixed design token being ignored in confirmation and suspension emails.
* [:backend:`2808`] Fixed filenames in upload validation errors overflowing.
* [:backend:`2651`] Fixed analytics cookies receiving incorrect domain information after enabling
  the provider via the admin.
* [:backend:`2879`] Fixed the available zaaktypen not refreshing the admin when the catalogi API
  is changed.
* [:backend:`3097`] Fixed invalid phone numbers example in validation error messages.
* [:backend:`3123`] Added support for deploying Open Forms on a subpath (e.g. ``/formulieren``).
* [:backend:`3012`] Fixed select, radio and checboxes options not being translated in the UI.
* [:backend:`3070`] Fixed the confirmation email template not being copied along when copying a form.
* Fixed Matomo not using the configured Site ID correctly.
* [:backend:`3114`] Fixed the "next" button not becoming active if you're not logged in as admin user.
* [:backend:`3132`] Fixed replacing form steps in the designer with another step having overlapping
  variable names.

**Documentation**

* Improved Storybook documentation in the backend.
* Add instruction for Postgres 15 DB initialization (with docker-compose).
* [:backend:`2362`] Documented known Ogone payment simulator limitation.
* Added more details to the release flow and backporting documentation.
* Documented the possible use of soft hyphens in the form name.
* [:backend:`2908`] Documented limitations of import/export for forms with service fetch config.
* Added a note on refactor and small changes for contributors.
* [:backend:`2940`] Improved SDK embedding configuration documentation.
* Documented solution for "IDP not found" DigiD error.
* [:backend:`2884`] Documented how to set up service fetch.

**Project maintenance**

* Added management command to check component usage for usage analytics.
* Ignore coverage on type checking branches.
* [:backend:`2814`] Added additional robustness tests for possible glom crashes.
* Removed postcss-selector-lint.
* Add 2.1.x release series to Docker Hub generation config
* Add 2.2.x release series to Docker Hub generation config
* Deprecated the password field as it has no real-world usage.
* Bumped a number of dependencies following @dependabot security alerts.
* Started preparing the upgrade to Django 4.2 LTS.
* Added tests for and refined intended behaviour of ``AllOrNoneRequiredFieldsValidator``.
* Added tests for ``ModelValidator``.
* [:backend:`3016`] Fixed the MacOS CI build.
* Removed the 1.1.x series from supported versions.
* Support sufficiently modern browsers, reducing the JS bundle sizes a bit.
* [:backend:`2999`] Fixed broken test isolation.
* [:backend:`2784`] Introduced and refactored code to use ``FormioDate`` interface.
* Tests are now also run in reverse order in CI to catch test isolation problems.

2.1.11 (2023-12-28)
===================

Final release in the 2.1.x series.

Upgrade to Open Forms 2.2 or higher to continue receiving support/bugfixes.

* [:backend:`3656`] Fixed an incorrect DigiD error message being shown with OIDC authentication
  plugins.
* [:backend:`3692`] Fixed a crash when cancelling DigiD authentication while logged in as admin
  user.

2.1.10 (2023-12-12)
===================

Periodic bugfix release

* [:backend:`3625`] Fixed crashes during StUF response parsing when certain ``nil`` values are
  present.
* [:backend:`3605`] Fixed unintended number localization in StUF/SOAP messages.
* [:backend:`3613`] Fixed submission resume flow not sending the user through the authentication
  flow again when they authenticated for forms that have optional authentication. This
  unfortunately resulted in hashed BSNs being sent to registration backends, which we
  can not recover/translate back to the plain-text values.

2.1.9 (2023-11-09)
==================

Hotfix release

* Upgraded bundled SDK version
* [:backend:`3580`] Fixed incorrect attributes being sent in ZWG registration backend when
  creating the rol/betrokkene.

2.1.8 (2023-10-30)
==================

Periodic bugfix release

* Bumped dependencies to their latest security fixes.

2.1.7 (2023-09-25)
==================

Periodic bugfix release

* [:backend:`3139`] Fixed form designers/admins not being able to start forms in maintenance mode.
* Fixed the version of openapi-generator.
* Bumped to latest Django patch release.
* [:backend:`3447`] Fixed flash of unstyled form visible during DigiD/eHerkenning login flow.
* [:backend:`3420`] Fixed styling of cookie overview page.
* [:backend:`3378`] Fixed copying forms with logic that triggers from a particular step crashing
  the logic tab.
* [:backend:`3470`] Fixed form names with slashes breaking submission generation.
* Included latest SDK bugfix release.

2.1.6 (2023-08-24)
==================

Periodic bugfix release

* [:backend:`3319`] Fixed forms possibly sending a DigiD SAML request without assurance level due
  to misconfiguration.
* [:backend:`3358`] Fixed display of appointment time in correct timezone.
* [:backend:`3368`] Fixed a crash when empty values are returned from StUF-BG.

2.1.5 (2023-07-26)
==================

Periodic bugfix release

* [:backend:`3132`] Fixed replacing form steps in the designer with another step having overlapping
  variable names.
* Fixed testing availability of OIDC auth endpoint with HEAD requests (now uses GET).
* [:backend:`3216`] Fixed setting the Piwik Pro SiteID parameter in the analytics scripts.
* [:backend:`3211`] Fixed CSP violation in Piwik Pro analytics script, causing no analytics to be
  tracked.
* [:backend:`3161`] Fixed not being able to reset form-specific data removal settings to the
  empty value so that the global configuration is used again.
* [:backend:`3219`] Fixed saved uploads not being deleted when the user goes back to the file and
  removes the upload again.
* Fixed CI builds (bump PyYAML, docs build).
* [:backend:`3258`] Fixed labels for Haal Centraal prefill attributes.
* [:backend:`3301`] Fixed crash on DigiD authentication with brokers not returning sectoral codes.
* [:backend:`3144`] Fixed missing links to uploads in the registration e-mails when the field is
  inside a container (fieldset, repeating group).
* [:backend:`3302`] Fixed an issue causing uploaded images not to be resized.
* [:backend:`3084`] Fixed ``inp.heeftAlsKinderen`` missing from certain StUF-BG requests.
* Bumped dependencies to get their latest security fixes

2.1.4 (2023-06-21)
==================

Periodic bugfix release

* [:backend:`1959`] Fixed invalid link to resume form after pausing and resuming multiple times.
* [:backend:`3025`] Fixed resuming a form redirecting to an invalid URL.
* [:backend:`3015`] Fixed invalid URLs being generated to resume the form from WYSIWYG content.
* [:backend:`2927`] Added Celery worker monitoring tooling (for devops/infra).
* [:backend:`3068`] Added soft and hard task timeout settings for background workers.
* [:backend:`3077`] Use public (instead of private) form name for ``form_name`` variable in templates.
* [:backend:`3012`] Fixed select, radio and checboxes options not being translated in the UI.
* [:backend:`3136`] Fixed wrong Site ID being used for Matomo analytics.
* [:backend:`3114`] Fixed the "next" button not becoming active if you're not logged in as admin user.
* [:backend:`3103`] Fixed DigiD/eHerkenning-metadata missing the XML declaration.

2.1.3 (2023-04-19)
==================

Hotfix - 2.1.2 unfortunately broke saving forms from previous minor version exports

* [:backend:`2877`] Backported admin crash on misconfigured ZGW services.
* [:backend:`3007`] Fixed worfklows where < 2.1 form exports are imported and edited in the admin.
* [:backend:`2875`] Fixed SiteImprove analytics integration (for real now)
* [:backend:`2895`] Fixed WYSIWYG colors missing when filling out a form while logged in as staff user.

2.1.2 (2023-04-18)
==================

Periodic bugfix release

* [:backend:`2947`] Added missing translatable error messages for number components
* [:backend:`2908`] Documented limitations of import/export for forms with service fetch config
* [:backend:`2900`] Fixed inconsistent frontend logic involving checkboxes
* [:backend:`2632`] Fixed crash during submission data pruning when submissions point to form
  steps that have been deleted
* [:backend:`2849`] Restored ability to import forms using form logic in the pre-2.0 format
* [:backend:`2983`] Fixed broken StUF-ZDS registration for some vendors due to bad refactor
* [:backend:`2963`] Fixed global configuration templates being reset to their default values
* [:backend:`2977`] Fixed StUF postcode not being uppercase
* Updated the bundled SDK version to 1.3.2
* [:backend:`2980`] Fixed file upload component not using config overwrites when registering
  with the objects API backend.

2.1.1 (2023-03-31)
==================

Periodic maintenance release

* [:backend:`2945`] Prevent the addition of user defined variables from breaking the logic rules.
* [:backend:`2893`] A minimal fix to prevent crashes of the celery task logging the evaluation of logic rules.
* Upgrade of the SDK version
* [:backend:`2911`] Make validation of .heic and .heif files more lenient.
* [:backend:`2889`] Fix the focus jumps of the content component in the admin by re-implement the component translations machinery.
* [:backend:`2888`] Change the validation of BSN components from 'on change' to 'on blur'.
* [:backend:`2888`] Fix uploading documents inside a repeating group when a number component is also present in the repeating group.
* [:backend:`2888`] Fix uploading documents when there is a hidden repeating group.
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

* [:backend:`2804`] Fixed the "static variables" not being available in confirmation template
  rendering.
* [:backend:`2821`] Fixed broken "Map" component configuration screen.
* [:backend:`2822`] Fixed date components being interpreted as datetimes instead of dates.
* [:backend:`2819`] Fixed the key and translations of the password field not automatically
  updating with entered content (label and other translatable fields).
* [:backend:`2820`] Fixed translations not registering initially when adding a component to a new
  form step.
* [:backend:`2791`] Fixed long words overflowing in the confirmation PDF.
* [:backend:`2850`] Fixed a crash in the AVG log viewer when certain log records of deleted
  submissions are displayed.
* [:backend:`2842`] Fixed analytics CSP-integration resulting in a misconfigured policy.
* [:backend:`2851`] Fixed importing a form while the admin UI is set to English resulting in
  incorrect form translation mappings.
* [:backend:`2838`] Fixed hidden selectboxes field triggering premature validation of required fields.
* [:backend:`2874`] Fixed "repeating group" component group label not being translated.

2.1.0-rc.0 (2023-03-03)
=======================

We are proud to announce a release candidate of Open Forms 2.1!

This release candidate has focused on stability issues compared to the previous alpha
version and includes some new experimental features.

Detailed changes
----------------

**New features**

* Multilingual support

  * [:backend:`2493`] Display warnings for missing translations in the form designer when form
    translations are enabled.
  * [:backend:`2685`] Staff users can now configure their admin UI language preferences.

* [:backend:`2623`] Improved implementation of dynamic options (select, radio, checkboxes).
* [:backend:`2663`] Added ClamAV cirus scanning support. This is disabled by default - you need to
  deploy a ClamAV service instance and then enable it in the Open Forms configuration.
* [:backend:`2653`] Allow more configuration in the ZGW registration plugin:

  * Specify a default bronorganisatie RSIN + allow overriding it per file-component.
  * Specify a default documentation vertrouwelijkheidaanduiding + allow overriding it
    per file-component.
  * File upload components can now specify the document title and auteur fields.

* Data retrieval from external registrations

  * [:backend:`2454`] Implemented retrieving and processing data from external JSON services.
  * [:backend:`2753`] Added opt-in feature flag.

 [:backend:`2786`] Improved phone number validation error messages.

**Bugfixes**

* [:backend:`2601`] Disabled autocomplete for username/password in (services) admin.
* [:backend:`2635`] Fixed component key not being updated anymore with label changes.
* [:backend:`2643`] Fixed description generation for empty ``var`` operations and the ``map``
  operation.
* [:backend:`2641`] Relaxed email URL stripping for subdomains of allow-listed domains.
* [:backend:`2549`] Fixed cookie banner overlapping footer links
* [:backend:`2673`] Fixed mobile styling (spacing + location of language selection component).
* [:backend:`2676`] Fixed more mobile styling spacing issues (header/footer, logo).
* [:backend:`2636`] Fixed a number of bugs that appeared in the previous version

  * Fixed saving user defined variables with a falsy initial value.
  * Fixed broken display of logic rule "trigger from step" selected choice.

* Fixed the API forcing the default language in the admin when a form does not have
  translations enabled.
* [:backend:`2646`] Fixed "privacy policy acceptance" not being recorded/validated in the backend.
* [:backend:`2699`] Fixed uploads in repeating groups not being registered in the backend.
* [:backend:`2682`] Fixed some date/datetime component issues

  * Fixed editor options not refreshing when selecting a validation method.
  * Fixed validation min/max value tab settings not having any effect.

* [:backend:`2709`] Fixed (bandaid) inconsistent dynamic product price logic
* [:backend:`2671`] Fixed QR code not being readable in dark mode.
* [:backend:`2742`] Fixed the key of file upload components not updating with the label.
* [:backend:`2721`] Updated django-simple-certmanager version
* [:backend:`2734`] Validate that component keys inside repeating groups cannot duplicate existing
  form keys.
* [:backend:`2096`] Prevented users from being able to bypass steps blocked by logic.
* [:backend:`2781`] Fixed the data-clearing/data extraction of (hidden) nested components.
* [:backend:`2770`] Fixed formio unique component key generation to take into account keys from
  other steps.
* [:backend:`2805`] Fixed form builder crash when enabling translations and adding a new form step.
* [:backend:`2798`] Fixed select/radio/checkboxes option values not being derived from labels
  anymore.
* [:backend:`2769`] Fixed date/datetime components relative validation settings not being
  registered correctly.

**Documentation**

* Improved SharePoint registration backend documentation.
* [:backend:`2619`] Added Storybook documentation for the backend JS/CSS components.
* [:backend:`2481`] Updated the screenshots of the translations UI in the manual.
* [:backend:`2696`] Updated documentation about dynamic form options and unsupported JSON-logic
  operators.
* [:backend:`2735`] Documented functionalities that don't work (yet) in repeating groups.
* Added patch release changelog entries from stable branches.
* Documented Django changelist component in Storybook.
* Reorganized the component groups in Storybook.

**Project maintenance**

* Bumped dependencies to their latest (security) releases
* [:backend:`2471`] Add preparations for new appointments flow.
* [:backend:`388`, :backend:`965`] Refactored the StUF client implementations.
* Updated Github Actions workflows to use composite actions for duplicated steps.
* [:backend:`2657`] Replaced Selenium end-to-end tests with Playwright.
* [:backend:`2665`] Update coverage reporting configuration to exclude test files themselves.
* Fixed ``generate_minimal_setup`` factory trait by adding label to generated components.
* [:backend:`2700`] Replaced the last Github dependencies with PyPI versions of them.
* Enabled opt-in to use X-Forwarded-Host headers [infrastructure].
* [:backend:`2711`] Moved ``openforms.utils.api`` utilities to the ``openforms.api`` package.
* [:backend:`2748`] Pinned the project to Python 3.10.9 due to a CPython regression.
* [:backend:`2712`] Replaced django-choices usage with core Django equivalents.
* Fixed a test failing between 00:00-01:00 AM.

2.1.0-alpha.2 (2023-02-01)
==========================

Next 2.1.0 preview version.

This alpha release of Open Forms 2.1 is likely to be the last one before the beta
version(s) and associated feature freeze.

Detailed changes
----------------

**New features**

* Multilingual support

  * [:backend:`2478`] Implemented UI/UX for form designers to manage component-level translations.
  * [:backend:`2390`] PDF reports and confirmation emails are now rendered in the submission
    language.
  * [:backend:`2286`] Ensured that the API endpoints for the SDK return the translations
    according to the active language.
  * [:backend:`2546`] Added language metadata to MS Graph, Objects API, ZGW API, StUF-ZDS and
    email registration backends.
  * [:backend:`1242`] The form designer component edit form and preview are now properly localized.

* Accessibility improvements

  * [:backend:`2268`] Added support for the autocomplete property in the form designer. This
    comes with a set of pre-configured form fields having the correct autocomplete
    attribute set out of the box.
  * [:backend:`2490`] Login logo objects in the API now contain meta-information about their
    appearance for appropriate focus-styling in the SDK.
  * [:backend:`2534`] Added support for custom errors per-component in the form designer,
    including translation options.
  * [:backend:`2273`] Improved accessibility of error messages for required fields.

* Registration plugins

  * [:backend:`2494`] Added ability to add identifying person details in StUF-ZDS registration
    even if the person did not authenticate via DigiD (or similar).
  * [:backend:`2511`] Added more options for the Microsoft Graph registration plugin, such as
    base folder path, drive ID and year/month/day interpolation.

* [:backend:`1902`] Added support for sourcing choice widget values from variables.
* [:backend:`2504`] Improved performance in form designer initial load when you have many
  forms/form definitions.
* [:backend:`2450`] Added "description" field to logic rules in the form designer. The description
  can be specified manually or is automatically generated from the logic expression.
* [:backend:`2143`] Added option to exclude confirmation page content from PDF.
* [:backend:`2539`] Added support for ``.msg`` and ``.dwg`` file uploads.
* [security#20] Use fully qualified URLs in analytics config for maximum CSP strictness.
* [:backend:`2591`] Added rate limits to API endpoints for pausing and submitting forms.
* [:backend:`2557`] Implemented comparing date and times with the ``now +- someDelta`` variable.

**Bugfixes**

* [:backend:`2520`] Fixed MIME type validation error for ``.doc`` files.
* [:backend:`2577`] Fixed MIME type validation regression for OpenOffice and dwg files.
* [:backend:`2377`] Fixed link-hover design token not being applied consistently.
* [:backend:`2519`] Only perform upgrade checks when not upgrading between patch versions.
* [:backend:`2120`] Fixed layout components inadvertedly getting the ``validate.required=true``
  configuration.
* [:backend:`2396`] Fixed auto-login setting not resetting when the authentication option is
  removed from the form.
* Add missing ``br`` tag to allowed WYSIWYG tag list.
* [:backend:`2550`] Removed ``role=img`` from logo in header.
* [:backend:`2525`] Fixed clearing the date component min/max validation configuration.
* [:backend:`2538`] Normalize radio components to always be string type.
* [:backend:`2576`] Fix crash on components with prefill attribute names > 50 chars.
* [:backend:`2012`] Fixed missing ``script-src`` CSP directive for SiteImprove analytics.
* [:backend:`2541`] Fixed a crash in the logic editor when changing the key of selectboxes
  components.
* [:backend:`2587`] Fixed inadvertedly HTML escaping while templating out email subjects.
* [:backend:`2599`] Fixed typo in registration constants.
* [:backend:`2607`] Fixed crash in logic editor when specifying a "trigger-from" step.
* [:backend:`2581`] Fixed bug in logic where dates and datetimes were being mixed.

**Documentation**

* [:backend:`2198`] Added examples and documentation for highly-available setups with regard to
  the background task message queue.
* Updated installation documentation to mention the correct Python version.
* Documented the flow to register a form on behalf of a customer.
* Delete obsolete/old boilerplate documentation.
* Updated developer docs and clarified SDK developer documentation.

**Project maintenance**

* Removed some obsolete/unnecessary assets on error pages.
* [:backend:`2377`] Refactored links to make use of the NL DS ``utrecht-link`` component - you can
  now use all the design tokens from that component in Open Forms too.
* [:backend:`2454`] Upgraded black and flake8 versions for Python 3.10 support.
* [:backend:`2450`] Moved JSON-logic expression processing into maykin-json-logic-py library.
* Upgraded a number of dependencies.
* [:backend:`2471`] Refactored appointments module to bring the plugin structure in line with the
  rest of the project.
* [:backend:`1439`] The Docker Hub readme/description is now automatically updated via Github
  Actions.
* [:backend:`2555`] Removed dead code.
* [:backend:`1904`] Refactored existing code to make use of the sandboxed template backends.
* [:backend:`1898`] Refactored template validators to use the sandboxed template backends.
* Tweaked CI for speed so we spend less time waiting for CI builds to complete.
* Delete explicitly setting the template loaders.
* [:backend:`2583`] Fixed a case of broken test isolation.
* Upgraded drf-spectacular to the latest version.
* Added omg.org and jccsoftware.nl to docs link-check ignore list.
* Added CI job to install dev deps on MacOS.
* [:backend:`2478`] Added frontend code test infrastructure.

2.1.0-alpha.1 (2022-12-20)
==========================

Second alpha version of the 2.1.0 release.

**New features**

* [:backend:`2332`] Added ``ServiceFetchConfiguration`` data model
* [:backend:`2348`] Added audit logging for empty prefill plugin values
* [:backend:`2313`] Added ``translations`` keys to API endpoints to store/read field translations
* [:backend:`2402`] Updated JSON-structure of "ProductAanvraag" registration
* [:backend:`2314`] Added UI in form designer to manage form/form step translations
* [:backend:`2287`] Confirmed support for multi-language forms in import/export
* [:backend:`1862`] Include "rol" metadata when an employee registers a case on behalf of a customer
* [:backend:`2389`] Add submission language code to submission exports
* [:backend:`2390`] Render documents in submission language: PDF report and confirmation email
* [:backend:`2463`] Improved repeating groups error messages
* [:backend:`2447`] Expose meta-information if an authentication plugin is for 'machtigen'
* [:backend:`2458`] Added option to extract OIDC user information from ID-token instead of
  info endpoint
* [:backend:`2430`] Added HEIC and TXT to filetypes for upload
* [:backend:`2428`] Added organization name configuration option, displayed in various
  labels/titles.
* [:backend:`2315`] Implementing UI for entering and storing formio.js component translations

**Bugfixes**

* [:backend:`2367`] Fixed upgrade/migration crash when dealing with selectboxes frontend logic
* [:backend:`2251`] Fixed broken logic when comparing to dates
* [:backend:`2385`] Fixed a crash when processing incomplete frontend logic
* [:backend:`2219`] Updated fix for CSS-unit issue with design tokens in email header logo
* [:backend:`2400`] Clean up cached execution state
* [:backend:`2340`] Added bandaid fix to clear data that isn't visible if the parent component is
  hidden
* [:backend:`2397`] Fixed some duplicate labels in admin
* [:backend:`2413`] Fixed fields made visible by selectboxes type components not showing up in
  summary/pdf/email
* [:backend:`1302`] Fixed family members component crash when no BSN is known
* [:backend:`2422`] remove spaces from postcodes in StUF messages
* [:backend:`2250`] Fixed broken analytics scripts not loading/executing
* [:backend:`2436`] Fixed broken default value of copied fields inside fieldsets
* [:backend:`2445`] Ensure that removing a fieldset in the form designer also removes the variables
* [:backend:`2398`] Fixed upgrade/migration crash when formio logic references non-existing
  component keys
* [:backend:`2432`] Fixed backwards-compatibility layer for pre-2.0 form exports with actions
  targetting form steps
* [:backend:`2484`] Fixed unexpected fallbacks to NL for form literals instead of using the
  global configuration
* [:backend:`2488`] Disable inline edit for repeating groups again
* [:backend:`2449`] Fixed server-side logic interpretation inside repeating groups
* Fixed import crash due to performance optimization
* [:backend:`1790`] Fixed broken "form definition used in forms" modal in production builds
* [:backend:`2373`] Remove (unintended) multiple option for map component

**Documentation**

* Updated examples and example form exports to 2.0
* Provide best-practices for securing OF installations
* [:backend:`2394`] Removed digid/eherkenning envvars config from docs
* [:backend:`2477`] Added new page for multi-language configuration to the manual
* Removed ambiguity about staff/non-staff fields in certain API endpoints

**Project maintenance**

* Upgraded Pillow to the latest version
* [:backend:`1068`] Finalized refactor for formio integration in the backend
* removed unused UI template tags/options
* [:backend:`2312`] Upgraded base docker images to Debian bullseye
* [:backend:`2487`] Add import sorting plugin for prettier
* Catch invalid appointment configs in management command
* Bumped frontend/build dependency versions

2.1.0-alpha.0 (2022-11-21)
==========================

First alpha version of the 2.1.0 release.

Open Forms now has the ambition to release an alpha version about every 4 weeks (at
the end of a sprint) and putting out a new minor or major version every quarter.

**New features**

* [:backend:`1861`, :backend:`1862`] Added organization member authentication for forms. Using OIDC, employees of
  the organization can now log in to (internal) forms and submit them. It is also
  possible for employees (e.g. service desk staff) to start forms on behalf of customers.
* [:backend:`2042`] Optimized component mutations (by logic) by using a caching datastructure
* [:backend:`2209`] Simplified number component validation error messages
* Ensured that upgrading to 2.1 enforces upgrading to 2.0 first
* [:backend:`2225`] Emit openforms-theme as default theme unless an explicit theme is configured
* [:backend:`2197`] Implemented plugin hooks to modify requests that are about to be made to
  third party services
* [:backend:`2197`] Added container image tag/version including all official extensions
  (including token-exchange authorization)
* [:backend:`1929`] Added early file type/extension validation for file uploads
* Added ``reverse_plus()`` utility function
* [:backend:`1849`] DigiD/eHerkenning/eIDAS metadata can now be configured and generated from the admin
* First steps for translatable content/forms:

  * [:backend:`2228`] Enabled run-time language preference detection
  * [:backend:`2229`] Added endpoint to expose available (and currently activated) language(s)
  * [:backend:`2230`] Expose translatable properties for forms (in the admin)
  * [:backend:`2231`] API endpoints return content in the currently activated/requested language
  * [:backend:`2232`] Expose whether form translations are enabled (and enforce the default
    language if they're not)
  * [:backend:`2278`, :backend:`2279`] Store the language for a form submission when it's created
  * [:backend:`2255`] SDK: use the correct locale for static translations

* [:backend:`2289`] Create NNP/Vestiging depending on the available properties (registration backends)
* [:backend:`2329`] The CSP post-processor now performs HTML sanitation too, stripping tags and
  attributes that are not on the allowlist.
* Optimized form list endpoint
* Upgraded to Python 3.10

**Bugfixes**

* [:backend:`2062`] Fixed "Print this page" CSP violation
* [:backend:`1180`] Fixed Google Analytics not measuring form steps correctly
* [:backend:`2208`] Fixed JSON-logic expressions with primitives (number, string...)
* [:backend:`1924`] Various fixes to the dark mode theme for the form designer
* [:backend:`2206`] Fixed a race condition related to prefill variables
* [:backend:`2213`] Fixed inconsistent default values for copied components in the form designer
* [:backend:`2246`] Fixed invalid error styling in form designer
* [:backend:`1901`] Fixed image inline styles in content components by CSP post-processing them
* [:backend:`1957`] Fixes admin ``retry_processing_submissions()`` action to reset
  submission registration attempts counter
* [:backend:`2148`] Changed VertrouwelijkheidsAanduidingen translatable choice labels to Dutch
* [:backend:`2245`] Changed privacy policy link in summary page to open in new window
* [:backend:`2277`] Fixed Ogone feedback URL
* [:backend:`2301`] Fixed identifying attributes still being hashed after a submission is resumed
* [:backend:`2135`] Fixed submission step data being cascade deleted in certain edge cases
* [:backend:`2244`] Fixed 'content' component and components not marked as ``showInSummary``
  showing up in server rendered summary
* Fixed pattern for formio key validation
* [:backend:`2337`] Fixed crash on data prefill for certain multi-step forms
* [:backend:`2304`] Refactored form logic action "mark step as not applicable" to use ID references
  rather than API paths.
* [:backend:`1899`] Apply prefill data normalization before saving into variables
* [:backend:`2352`] Removed permissions to delete user from standard groups as those cascade
  delete admin log entries.
* [:backend:`2344`] Fixed out-of-place repeating groups required-field asterisk
* [:backend:`2145`] Removed copy-paste snippets from form change page as they are not guaranteed
  to be correct to your use-case.

**Documentation**

* [:backend:`2163`] Document file upload storage flow
* Installation docs: configure db *before* migrate and runserver
* Installation docs: added missing OS-level dependencies
* [:backend:`2205`] Documented unsupported JSON-logic operators

**Project maintenance**

* [:backend:`2050`] Removed ``SubmissionFileAttachment.form_key`` field and using variables instead
* [:backend:`2117`] Fixed spelling 'organisation' -> 'organization'
* Fixed example dotenv file
* Emit deprecation warning for openforms.formio.utils.get_component
* Update Django to latest patch/security releases
* [:backend:`2221`] Removed code for warning about duplicate keys
* Converted squashed migration into regular migrations
* Updated github workflows to action versions following some deprecations
* Fixed private media and add media mount in examples/docker-compose file
* Upgraded to latest lxml version
* Dropped django-capture-on-commit-callbacks as Django provides it now
* Pin postgres version to 14 in docker-compose
* [:backend:`2166`] Modified Dockerfile with Volumes hint to prevent writing to container layer
* [:backend:`2165`] Upgrade django-simple-certmanager
* [:backend:`2280`] Removed ``SubmissionValueVariable.language``
* Refactored mail cleaning utilities into separate library
* Parametrize workflows/dockerfile for extensions build

2.0.11 (2023-09-25)
===================

Final bugfix release in the ``2.0.x`` series.

* [:backend:`3139`] Fixed form designers/admins not being able to start forms in maintenance mode.
* Fixed the version of openapi-generator.
* Bumped to latest Django patch release.
* [:backend:`3378`] Fixed copying forms with logic that triggers from a particular step crashing
  the logic tab.
* [:backend:`3470`] Fixed form names with slashes breaking submission generation.
* Included latest SDK bugfix release.

2.0.10 (2023-08-24)
===================

Periodic bugfix release

* [:backend:`3358`] Fixed display of appointment time in correct timezone.
* [:backend:`3368`] Fixed a crash when empty values are returned from StUF-BG.

2.0.9 (2023-07-26)
==================

Periodic bugfix release

* [:backend:`3132`] Fixed replacing form steps in the designer with another step having overlapping
  variable names.
* [:backend:`3216`] Fixed setting the Piwik Pro SiteID parameter in the analytics scripts.
* [:backend:`3211`] Fixed CSP violation in Piwik Pro analytics script, causing no analytics to be
  tracked.
* [:backend:`3161`] Fixed not being able to reset form-specific data removal settings to the
  empty value so that the global configuration is used again.
* [:backend:`3219`] Fixed saved uploads not being deleted when the user goes back to the file and
  removes the upload again.
* Fixed CI builds (bump PyYAML, docs build).
* [:backend:`3258`] Fixed labels for Haal Centraal prefill attributes.
* [:backend:`3301`] Fixed crash on DigiD authentication with brokers not returning sectoral codes.
* [:backend:`3144`] Fixed missing links to uploads in the registration e-mails when the field is
  inside a container (fieldset, repeating group).
* [:backend:`3302`] Fixed an issue causing uploaded images not to be resized.
* [:backend:`3084`] Fixed ``inp.heeftAlsKinderen`` missing from certain StUF-BG requests.
* Bumped dependencies to include latest security fixes.

2.0.8 (2023-06-21)
==================

Periodic bugfix release

* [:backend:`3015`] Fixed invalid URLs being generated to resume the form from WYSIWYG content.
* [:backend:`2927`] Added Celery worker monitoring tooling (for devops/infra).
* [:backend:`3068`] Added soft and hard task timeout settings for background workers.
* [:backend:`3077`] Use public (instead of private) form name for ``form_name`` variable in templates.
* [:backend:`3136`] Fixed wrong Site ID being used for Matomo analytics.
* [:backend:`3117`] Fixed a crash in migrations preventing upgrading from older versions.
* [:backend:`3114`] Fixed the "next" button not becoming active if you're not logged in as admin user.
* [:backend:`3128`] Fixed hidden (file) components triggering validation too early.

.. note::

    The fix for premature validation triggering (:backend:`3128`) only applies to new
    components/forms.

    To fix this for existing file components, it's recommended to remove and re-add the
    component in the form.

2.0.7 (2023-05-01)
==================

Periodic bugfix release

* [:backend:`1959`] Fixed invalid link to resume form after pausing and resuming multiple times.
* [:backend:`3007`] Fixed worfklows where < 2.1 form exports are imported and edited in the admin.

2.0.6 (2023-04-17)
==================

Periodic bugfix release

Note that there is a manual intervention below if you make use of analytics providers
integration.

* [:backend:`2791`] Fixed long words overflowing in the confirmation PDF.
* [:backend:`2838`] Fixed hidden selectboxes triggering validation of required fields too early
* [:backend:`2850`] Fixed a crash in the AVG log viewer when certain log records of deleted
  submissions are displayed.
* [:backend:`2842`] Fixed the Content Security Policy breaking when enabling analytics provider
  configurations
* [:backend:`2888`] Fixed a crash when using file fields and hidden repeating groups at the same
  time
* [:backend:`2888`] Fixed a crash when using file fields and repeating groups with numbers inside
* [:backend:`2945`] Fixed logic rule variables inadvertedly being cleared when adding a new
  user defined variable
* Fixed mutatiesoort when doing StUF ``UpdateZaak`` calls
* [:backend:`2716`] Added missing co-sign identifier (BSN) to PDF submission report
* [:backend:`2900`] Fixed inconsistent frontend logic involving checkboxes
* [:backend:`2632`] Fixed crash during submission data pruning when submissions point to form
  steps that have been deleted
* [:backend:`2977`] Fixed StUF postcode not being uppercase
* [:backend:`2849`] Restored ability to import forms using form logic in the pre-2.0 format
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

2.0.5 (2023-03-07)
==================

Hotfix release

* [:backend:`2804`] Fixed static variables not being included in template context for submission
  confirmation template.
* [:backend:`2400`] Clean up cached execution state

2.0.4 (2023-02-28)
==================

Periodic maintenance release

* [:backend:`2607`] Fixed crash when selecting trigger-from-step in logic editor
* Fixed crash when importing forms
* [:backend:`2699`] Fixed file uploads not resolving when inside fieldsets/repeating groups
* Stopped link checking JCC links in CI since we're actively being blocked
* [:backend:`2671`] Fixed QR code background in dark mode
* [:backend:`2709`] Fixed (bandaid) inconsistent dynamic product price logic
* [:backend:`2724`] Ensure backport of negative-numbers (:backend:`1351`) is correctly included
* [:backend:`2734`] Added bandaid fix for non-unique keys inside repeating groups
* Updated to SDK 1.2.6
* [:backend:`2717`] Fixed crash on StUF-ZDS when updating the payment status
* [:backend:`2781`] Fixed clearing the value of hidden components with a nested key (``nested.key``).
* [:backend:`2759`] Fixed handling of file uploads with a nested key (``nested.key``).

2.0.3 (2023-01-24)
==================

Bugfix release addressing some more upgrade issues

* [:backend:`2520`] Fixed bug in mimetype validation for ``application/ms-word`` (and similar) files
* [:backend:`2519`] Skip 2.0.x upgrade checks if we're already on 2.0.x
* [:backend:`2576`] Fix upgrade crash on components with prefill attribute names > 50 chars
* [security#20] Fixed CSP configuration for Matomo, Piwik and Piwik PRO analytics
* [:backend:`2012`] Fixed CSP mechanisms in SiteImprove analytics provider snippet
* [:backend:`2396`] Fixed "auto login authentication" option not properly resetting
* [:backend:`2541`] Fixed a crash in the logic editor when changing the key of selectboxes components

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

* [:backend:`2331`] Fixed incorrect key validation problem which would block upgrades to 2.0+
* [:backend:`2385`] Fixed incomplete logic handling which would block upgrades to 2.0+
* [:backend:`2398`] Fixed logic trigger processing which could crash upgrades to 2.0+
* [:backend:`2413`] Fixed fields being made visible by selectboxes in frontend logic not being
  visible in summary/pdf/emails
* [:backend:`2422`] Fixed invalid postcode format being sent to StUF-ZDS
* [:backend:`2289`] Fixed StUF-ZDS: now a ``Vestiging`` is created if vestigingsnummer is present,
  falling back to ``NietNatuurlijkPersoon`` otherwise.
* [:backend:`2494`] Fixed person details not being sent to StUF-ZDS if the submitter was not
  authenticated but instead filled out details manually.
* [:backend:`2432`] Fixed importing pre-2.0 forms with legacy form step references in actions
* Fix docs build due to legacy renegotiation being disabled in openssl 3

2.0.1 (2022-11-23)
==================

First maintenance release of the 2.0 series.

This patch fixes a couple of bugs encountered when upgrading from 1.1 to 2.0.

**Bugfixes**

* [:backend:`2301`] Fixed identifying attributes still being hashed after a submission is resumed
* [:backend:`2135`] Fixed submission step data being cascade deleted in certain edge cases
* [:backend:`2219`] A fix was also attempted for bad CSS unit usage in confirmation emails, but
  this caused other problems. As a workaround you should use the correctly sized images
  for the time being.
* [:backend:`2244`] Fixed 'content' component and components not marked as showInSummary showing
  up in server rendered summary
* Fixed pattern for formio key validation
* [:backend:`2304`] Refactored form logic action "mark step as not applicable" to use ID
  references rather than API paths, which affected some logic actions.
* [:backend:`2262`] Fixed upgrade from < 2.0 crash when corrupt prefill configuration was present
  in existing forms
* [:backend:`1899`] Apply prefill data normalization before saving into variables
* [:backend:`2367`] Fixed automatic conversion of advanced frontend logic when using selectboxes
  component type

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

* [:backend:`1325`] Introduced the concept of "form variables", enabling a greater flexibility
  for form designers

  * Every form field is automatically a form variable
  * Defined a number of always-available static variables (such as the current
    timestamp, form name and ID, environment, authentication details...)
  * Form designers can define their own "user-defined variables" to use in logic and
    calculations
  * Added API endpoints to read/set form variables in bulk
  * Added API endpoint to list the static variables
  * The static variables interface is extensible

* [:backend:`1546`] Reworked form logic rules

  * Rules now have explicit ordering, which you can modify in the UI
  * You can now specify that a rule should only be evaluated from a particular form
    step onwards (instead of 'always')
  * Form rules are now explicitely listed in the admin for debugging purposes
  * Improved display of JSON-logic expressions in the form designer
  * When adding a logic rule, you can now pick between simple or advanced - more types
    will be added in the future, such as DMN.
  * You can now use all form variables in logic rules

* [:backend:`1708`] Reworked the logic evaluation for a submission

  * Implemented isolated/sandboxed template environment
  * Form components now support template expressions using the form variables
  * The evaluation flow is now more deterministic: first all rules are evaluated that
    updated values of variables, then all other logic actions are evaluated using
    those variable values

* [:backend:`1661`] Submission authentication is now tracked differently

  * Removed the authentication identifier fields on the ``Submission`` model
  * Added a new, generic model to track authentication information:
    ``authentication.AuthInfo``
  * Exposed the submission authentication details as static form variables - you now
    no longer need to add hidden form fields to access this information.

* [:backend:`1967`] Reworked form publishing tools

  * Deactivated forms are deactivated for everyone
  * Forms in maintenance mode are not available, unless you're a staff member
  * The API endpoints now return HTTP 422 or HTTP 503 errors when a form is deactivated
    or in maintenance mode
  * [:backend:`2014`] Documented the recommended workflows

* [:backend:`1682`] Logic rules evaluation is now logged with the available context. This should
  help in debugging your form logic.
* [:backend:`1616`] Define extra CSP directives in the admin
* [:backend:`1680`] Laid the groundwork for DMN engine support. Note that this is not exposed
  anywhere yet, but this will come in the future.
* [:backend:`1687`] There is now an explicit validate endpoint for submisisons and possible error
  responses are documented in the API spec.
* [:backend:`1739`] (API) endpoints now emit headers to prevent browser caching
* [:backend:`1719`] Submission reports can now be downloaded for a limited time instead of only once
* [:backend:`1835`] Added bulk endpoints for form and price logic rules
* [:backend:`1944`] API responses now include more headers to expose staff-only functionality to
  the SDK, and permissions are now checked to block/allow navigating between form
  steps without the previous steps being completed.
* [:backend:`1922`] First passes at profiling and optimizing the API endpoints performance
* Enabled Cross-Site-Request-Forgery protections for *anonymous* users
* [:backend:`2042`] Various performance improvements

*Form designer*

* [:backend:`1642`] Forms can now be assigned to categories in a folder structure
* [:backend:`1710`] Added "repeating group" functionality/component
* [:backend:`1878`] Added more validation options for date components

  * Specify a fixed min or max date; or
  * Specify a minimum date in the future; or
  * Specify a maximum date in the past; or
  * Specify a min/max date relative to a form variable

* [:backend:`1921`] You can now specify a global default for allowed file types
* [:backend:`1621`] The save/save-and-continue buttons are now always visible on the page in
  large forms
* [:backend:`1651`] Added 'Show Form' button on form admin page
* [:backend:`1643`] There is now a default maximum amount of characters (1000) for text areas
* [:backend:`1325`] Added management command to check number of forms with duplicate component keys
* [:backend:`1611`] Improved the UX when saving a form which still has validation errors somewhere.
* [:backend:`1771`] When a form step is deleted and the form definition is not reusable, the form
  definition is now deleted as well
* [:backend:`1702`] Added validation for re-usable form definitions - you can no longer mark a
  form definition as not-reusable if it's used in multiple forms
* [:backend:`1708`] We now keep track of the number of formio components used in a form step for
  statistical/performance analysis
* [:backend:`1806`] Ensure that logic variable references are updated
* [:backend:`1933`] Replaced hardcoded SDK start (login) message with text in form explanation
  template.
* [:backend:`2078`] field labels are now compulsory (a11y)
* [:backend:`2124`] Added message to file-upload component informing the user of the maximum
  allowed file upload size.
* [:backend:`2113`] added option to control column size on mobile viewports
* [:backend:`1351`] Allow negative currency and number components

*Registrations*

* [:backend:`1007`] you can now specify the document type for every upload component (applies to
  Objects API and ZGW registration)
* [:backend:`1723`] StUF-ZDS: Most of the configuration options are now optional
* [:backend:`1745`] StUF: file content is now sent with the ``contenttype`` attribute
* [:backend:`1769`] StUF-ZDS: you can now specify the ``vertrouwelijkheidaanduiding``
* [:backend:`1183`] Intermediate registration results are now properly tracked and re-used,
  preventing the same objects being created over and over again if registration is being
  retried. This especially affects StUF-ZDS and ZGW API's registration backends.
* [:backend:`1877`] Registration email subject is now configurable
* [:backend:`1867`] StUF-ZDS & ZGW: Added more registration fields

*Prefill*

* [:backend:`1693`] Added normalization of the postcode format according to the specified
  comonent mask
* The prefill machinery is updated to work with variables. A bunch of (private API) code
  in the ``openforms.prefill`` module was deleted.
* Removed the ``Submission.prefill_data`` field. This data is now stored in
  form/submission variables.

*Other*

* [:backend:`1620`] Text colors in content component can now be configured with your own presets
* [:backend:`1659`] Added configuration options for theme class name and external stylesheet to load
* Renamed design tokens to align with NL Design System style design tokens
* [:backend:`1716`] Added support for Piwik Pro analytics provider
* [:backend:`1803`] Form versions and exports now record the Open Forms version they were created
  with, showing warnings when restoring a form from another Open Forms version.
* [:backend:`1672`] Improved error feedback on OIDC login failures
* [:backend:`1320`] Reworked the configuration checks for plugins
* You can now use separate DigiD/eHerkenning certificates
* [:backend:`1294`] Reworked analytics integration - enabling/disabling an analytics provider now
  automatically updates the cookies and CSP configuration
* [:backend:`1787`] You can now configure the "form pause" email template to use
* [:backend:`1971`] Added config option to disable search engine indexing
* [:backend:`1895`] Removed deprecated functionality
* Improved search fields in Form/Form Definition admin pages
* [:backend:`2055`] Added management command to check for invalid keys
* [:backend:`2058`] Added endpoint to collect submission summary data
* [:backend:`2141`] Set up stable SDK asset URLs
* [:backend:`2209`] Improved validation errors for min/max values in number components

**Bugfixes**

* [:backend:`1657`] Fixed content component configuration options
* Fixed support for non-white background colors in PDFs with organization logos
* [:cve:`CVE-2022-31041`] Perform proper upload file type validation
* [:cve:`CVE-2022-31040`] Fixed open redirect in cookie-consent 'close' button
* [:backend:`1670`] Update error message for number validation
* [:backend:`1681`] Use a unique reference number every time for StUF-ZDS requests
* [:backend:`1724`] Content fields must not automatically be marked as required
* [:backend:`1475`] Fixed crash when setting an empty value in logic action editor
* [:backend:`1715`] Fixed logo sizing for PDFs (again)
* [:backend:`1731`] Fixed crash with non-latin1 characters in StUF-calls (such as StUF-ZDS)
* [:backend:`1737`] Fixed typo in email translations
* [:backend:`1729`] Applied workaround for ``defaultValue`` Formio bug
* [:backend:`1730`] Fixed CORS policy to allow CSP nonce header
* [:backend:`1617`] Fixed crash on StUF onvolledige datum
* [:ghsa:`GHSA-g936-w68m-87j8`] Do additional permission checks for forms requiring login
* [:backend:`1783`] Upgraded formiojs to fix searching in dropdowns
* Bumped Django and django-sendfile2 versions with fixes for :cve:`CVE-2022-36359`
* [:backend:`1839`] Fixed tooltip text not being displayed entirely
* [:backend:`1880`] Fixed some validation errors not being displayed properly
* [:backend:`1842`] Ensured prefill errors via StUF-BG are visible in logs
* [:backend:`1832`] Fixed address lookup problems because of rate-limiting
* [:backend:`1871`] Fixed respecting simple client-side visibility logic
* [:backend:`1755`] Fixed removing field data for fields that are made visible/hidden by logic
* [:backend:`1957`] Fixed submission retry for submissions that failed registration, but exceeded
  the automatic retry limit
* [:backend:`1984`] Normalize the show/hide logic for components and only expose simple variants.
  The complex logic was not intended to be exposed.
* [:backend:`2066`] Re-add key validation in form builder
* Fixed some translation mistakes
* Only display application version for authenticated staff users, some pages still
  leaked this information
* Fixed styling of the password reset pages
* [:backend:`2154`] Fixed coloured links email rendering crash
* [:backend:`2117`] Fixed submission export for submissions with filled out subset of
  available fields
* [:backend:`1899`] Fixed validation problem on certain types of prefilled fields during
  anti-tampering check due to insufficient data normalization
* [:backend:`2062`] Fixed "print this page" CSP violation

**Project maintenance**

* Upgraded icon fonts version
* Upgraded CSS toolchain
* Frontend code is now formatted using ``prettier``
* [:backend:`1646`] Tweaked django-axes configuration
* Updated examples in the documentation
* Made Docker build smaller/more efficient
* Added the open-forms design-tokens package
* Bumped a number of (dev) dependencies that had security releases
* [:backend:`1615`] documented the CORS policy requirement for font files
* Added and improved the developer installation documentation
* Added pretty formatting of ``flake8`` errors in CI
* Configured webpack for 'absolute' imports
* Replaced deprected ``defusedxml.lxml`` usage
* [:backend:`1781`] Implemented script to dump the instance configuration for import into another
  environment
* Added APM instrumentation for better insights in endpoint performance
* Upgrade to zgw-consumers and django-simple-certmanager
* Improved documentation on embedding the SDK
* [:backend:`921`] Added decision tree docs
* Removed noise from test output in CI
* [:backend:`1979`] documented the upgrade process and added checks to verify consistency/state
  BEFORE migrating the database when upgrading versions
* [:backend:`2004`] Add post-processing hook to add CSRF token parameter
* [:backend:`2221`] Remove code for duplicated component key warnings
