=========
Changelog
=========

.. note::

    The Dutch version of this changelog can be found :ref:`here <changelog-nl>`.

3.3.10 (2026-01-05)
===================

Regular bugfix release.

* [:backend:`5723`] Fixed automatic closing of map overlay configuration when changing
  the label.
* [:backend:`5818`] Added missing ``bsn`` element in StUF-BG XML request to retrieve
  children.
* [:backend:`5840`] Fixed ``null`` values being sent to ZGW APIs when nested values are
  empty in partners/children data.

3.2.9 (2026-01-05)
==================

Final bugfix release in the ``3.2.x`` series.

* [:backend:`5770`] Fixed a crash when registering data for the partners component with
  StUF-ZDS.
* [:backend:`5733`] Fixed outgoing requests for the Generic JSON registration not being
  logged.
* [:backend:`5818`] Added missing bsn element in StUF-BG XML request to retrieve
  children.

3.4.0 "Gemeentegoed" (2025-01-05)
=================================

Open Forms 3.4.0 is a feature release.

.. epigraph::

   "Gemeentegoed" is a pun on the Dutch word for "municipality" and "gemeengoed", loosely
   translating to "common property". It highlights the roots in the local governments and
   emphasizes that Open Formulieren belongs to all of us. Parallel to the technical
   improvements, the past months have seen big efforts to build up the community around
   Open Formulieren and establish "source control management (broncodebeheer)" to keep
   the Open Source project healthy.

This contains the changes from the alpha releases and fixes applied until the stable version.
BEFORE upgrading to 3.4.0, please read the release notes carefully and review the following
instructions.

Upgrade procedure
-----------------

To upgrade to 3.4, please:

* ⚠️ Ensure you are currently on Open Forms 3.3.x or newer.
* Review the :ref:`detailed release notes <installation_upgrade_340>` in the
  documentation under **Installation** > **Upgrade details to Open Forms 3.4.0** and
  prepare accordingly, especially if you've built custom NL DS themes, please review
  the above upgrade details.

.. warning:: If you've built dashboards using the metrics telemetry, you'll need to
   update them with the updated metric names. The new names are in the documentation.

Major features
--------------

**⚙️ New render engine**

We have replaced the engine responsible for displaying the form fields, managing the
submission data and keeping track of part of the form logic. The result is snappier
user interaction, improved accessibility and (lightly) updating styling, while
integrating more closely with NL Design System.

Both the old and new render engines are available, and you can enable the new engine on
an individual form basis.

We now have a solid foundation to pick up some long-standing issues and feature requests.

**🗨️ Open Klant 2 integration**

It's now possible to specify communication preferences in form submissions, making it
easier to comply with WMEBV requirements. While the pattern is generic and open to
support other vendors, we specifically support Open Klant 2 at this point.

Deprecations
------------

See the :ref:`detailed release notes <installation_upgrade_340>`.

Detailed changes
----------------

**New features**

* New render engine:

  - Implemented all remaining existing components in the new renderer.
  - Optimized performance.
  - Accessibility of the ``textfield`` and ``textarea`` components with
    ``showCharCount: true`` is improved.
  - In the email verificaton flow you now have feedback that the email is verified.
  - Some custom validation error messages set in the backend are now supported.
  - The default validation error messages are improved and provide better user feedback.
  - Validation errors for an item in a repeating group are now displayed "for the item"
    rather than near the first field in the item.
  - Components that are "read only" are now marked as such in an accessible manner
    instead of being "disabled" and removed from the accessibility tree.
  - Applied a number of quality-of-life improvements to components that weren't possible
    before, notably for ``addressNL`` .
  - Added support for the new ``customerProfile`` component for interaction with Open
    Klant 2/customer interaction services.
  - Map component geometry validation now restricts geometries to the bounds of The
    Netherlands.
  - The date picker for ``date`` and ``datetime`` components is now accessible through
    keyboard navigation and for screen reader users.
  - Added preparations to lazy-load more functionality to improve loading times for users
    on slow network connections.
  - Accessibility of ``number`` components with prefix/suffix is improved.
  - [:backend:`5815`] Added a management command to enable the new renderer in bulk for
    DevOps.
  - [:backend:`5814`] Implemented shims for backwards compatibility due to new design
    tokens being used.

* Customer profile/communication preferences:

  - Supports BSN and KVK based authentication and customer profiles.
  - [:backend:`5707`] Implemented prefill plugin to retrieve the preferences for the
    customer profile from customer interaction APIs like Open Klant.
  - [:backend:`5772`] Added API endpoint to retrieve customer profile communication
    preferences from prefilled data.
  - [:backend:`5708`] Added new ``customerProfile`` form component where users can
    specify there communication preferences.
  - [:backend:`5711`] Implemented writing back component data to Open Klant when updates
    are requested.
  - [:backend:`5795`] Added a global configuration options for the "portal" URL where
    users can update their preferences.

* Admin interface:

  - [:backend:`5704`] You can now filter forms based on the payment backend used.
  - [:backend:`4357`] You can now use theme-specific favicons, organization names and
    logos.

* Registration:

  - [:backend:`5643`] Added ``heeftAlsAanspreekpunt`` to the StUF-ZDS registration plugin.
  - The registration flow now supports a per-component registration hook.
  - [:backend:`5776`] You can now map any static or user defined variable to a StUF-ZDS
    ``extraElementen`` entry.

* [:backend:`5683`] The form import endpoint now returns the UUID of the imported form.
* [:backend:`5546`] Improved the accessibility toolbar layout:

  - Moved the "print page" button to the footer.
  - Aligned the "back to top" link with the navigation controls.
  - Added an optional visual separator between the form and accessibility toolbar.
  - Fixed the toolbar not being shown on mobile devices.
  - Added the missing navigation role label.
  - The appearance can be tweaked with a number of new design tokens.

* [:backend:`5598`] It is no longer possible to cosign your own submission.

* Performance:

  - [:backend:`2409`] User-defined variables are now persisted upon step submission
    rather than only when the submission is completed. In case of issues, the old
    behaviour can be reinstated with the
    ``PERSIST_USER_DEFINED_VARIABLES_UPON_STEP_COMPLETION=False`` feature flag.
  - [:backend:`5747`] Rework how submission variables are stored to prepare for further
    improvements.

* Appointments:

  - [:backend:`5687`] Added the initial structure of JCC (REST) API appointment plugin,
    which will eventually replace the SOAP API variant.
  - [:backend:`5694`] Address details for appointment locations are now available for display.

**Bugfixes**

* [:backend:`5134`] Fixed deriving the correct "empty value" value for date/time/datetime
  variables.
* Fixed a crash when trying to save a form with a component where the ``multiple``
  property was changed.
* [:backend:`3640`] Fixed a theoretical case where a submission would be able to be
  suspended while registration is in progress or completed.
* [:backend:`5429`] Fixed component label being truncated in the preview panel of the
  configuration modal.
* [:backend:`5391`] Fixed submission logs (incorrectly) reporting empty results for
  skipped prefill operations.
* [:backend:`3544`] Fixed submission pruning potentially deleting submissions that still
  have future appointments associated with them.
* Fixed a crash in the upgrade migrations for form variables pointing to a component
  that cannot be resolved.
* [:backend:`5722`] Fixed Worldline configuration not taking into account multiple
  webhook key ID + secret combinations when multiple PSPIDs are used.
* [Sentry#453174] Fixed a crash in the configuration overview for invalid Worldline
  merchants.
* [:backend:`5737`] Fixed a crash in the form builder UI when the "synchronize variables"
  logic action is used and fieldset components are present.
* [:backend:`5735`] Fixed a crash when converting raw JSON data to the Python types when
  variables don't exist in the database in certain circumstances.
* [:cve:`CVE-2025-64515`] Fixed missing logic evaluation before validating (step data)
  user input. See :ghsa:`GHSA-cp63-63mq-5wvf` for details.
* Fixed the performance of the email verifications page in the admin.
* Fixed some crashes due to enabling certain optimizations, notably when:

  - Looking up the nearest address for map coordinates.
  - Looking up addresses in the Kadaster API.
  - Processing (single) file attachments in the generic registration plugin.

* [:backend:`5757`] Fixed a crash when attempting to submit a submission step with file
  upload attachments.
* [:backend:`5754`] Fixed a date/datetime/time formatting regression in the
  ``extraElementen`` of the StUF-ZDS registration plugin.
* Fixed crash in the MS Graph/Sharepoint registration plugin because it couldn't handle
  date/datetime/time objects in the JSON serialization.
* Fixed a bug in the OpenID library breaking our legacy callback endpoint compatibility
  layer.
* Fixed a crash in the processing of family members components data because of a
  difference in data format between StUF-BG and Haal Centraal Personen bevragen.
* [:backend:`5748`] Fixed the handling of a difference in data between Haal Centraal
  Personen Bevragen API and StUF-BG when retrieving family members data, preventing
  valid submission data from being accepted in children and partners components.
* [:backend:`5756`] Fixed an issue where at most one child would be retrieved for the
  children prefill when using StUF-BG.
* [:backend:`5765`] Fixed a regression introduced in the 3.3.3 security fix that would
  prevent valid values from being accepted in radio, select and selectboxes components
  with options sourced from a variable.
* Fixed the Token Exchange extension no longer functioning due to the OpenID library rework.
* [:backend:`5770`] Fixed a crash when registering data for the ``partners`` component
  with StUF-ZDS.
* [:backend:`5778`] Fixed crashes during registration with Objects API when there are
  date or datetime fields inside a repeating group.
* [:backend:`5784`] Fixed Worldline credit card payments authorization mode not being
  set to ``SALE``.
* [:backend:`5733`] Fixed outgoing requests for the Generic JSON registration not being logged.
* [:backend:`5803`] Worked around date/time/datetime objects in submission data being automatically
  formatted according to the locale in Objects API V1 templates.
* [:backend:`5818`] Added missing ``bsn`` element in StUF-BG XML request to retrieve
  children.
* [:backend:`5840`] Fixed ``null`` values being sent to ZGW APIs when nested values are
  empty in partners/children data.
* [:backend:`5835`] Fixed the Worldline webhook admin not displaying the PSPID.

**Project maintenance**

* Updated and improved the form embedding documentation.
* Removed the deprecated privacy policy config endpoint.
* Removed some stale documentation.
* Updated compatible versions (backend/API/SDK) documentation.
* [:sdk:`445`] Updated the references to the new static assets locations in the SDK.
* [:backend:`5134`] Addressed some edge cases where logic rule evaluations could yield
  unexpected results, by fixing the ``clearOnHide`` behaviour implementation.
* Renamed the metrics to comply with OTel naming conventions.
* Updated zgw-consumers to support OAUTH2-enabled services.
* The container image is now also published to
  `ghcr.io <https://github.com/open-formulieren/open-forms/pkgs/container/open-forms>`_.
* Removed incorrect deprecation marker on address autocomplete endpoint.
* Upgraded frontend dependencies with their latest security updates, affecting
  development tooling.
* Upgraded to mozilla-django-oidc-db and its improved type annotations.
* Added ``openforms.authentication``, ``openforms.data_removal`` and ``openforms.emails``
  to type-checked packages in CI.
* Added documentation on how to develop UI components.
* Bumped security update versions:

  - Django
  - brotli
  - fonttools
  - urllib3

* [DH#817] Added more logging and error information captures in case the Worldline
  payment flow errors.
* Updated (development) frontend dependencies with their latest security fixes.
* Tweaked the CI pipeline to include a test run with stripped out ``assert`` statements.
* Enabled a linter rule that checks for possible bugs due to stripped out ``assert``
  statements.
* Banned ``typing.cast`` usage through linter rule.
* Enabled an option in the type checker to error when error suppression is no longer
  necessary.
* Cleaned up CI pipelines by using our own reusable actions.
* Docker Hub image description generation is now a fully standalone script, run with
  ``uv``.
* Updated VCR checklist template and added utility script to spin up all necessary
  scripts, using isolated port numbers.
* [:backend:`5739`] Removed/cleaned up obsolete migrations.
* Removed obsoleted fix/diagnostics scripts.
* Switched to django-test-migrations to test migrations.
* Removed NLX from the repo submodules.
* Added guards to recycle application worker processes in the event of memory leaks.
  We're investigating root causes.

3.3.9 (2025-12-11)
==================

Hotfix release.

* [:backend:`5733`] Fixed outgoing requests for the Generic JSON registration not being logged.
* [:backend:`5803`] Worked around date/time/datetime objects in submission data being automatically
  formatted according to the locale in Objects API V1 templates.

3.4.0-alpha.2 (2025-12-04)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

Upgrade procedure
-----------------

To upgrade to 3.4, please:

* ⚠️ Ensure you are currently on Open Forms 3.2.x or newer.
* if you've built custom NL DS themes, please review the deprecations in the SDK
  changelog.

.. warning:: If you've built dashboards using the metrics telemetry, you'll need to
   update them with the updated metric names. The new names are in the documentation.

New features
------------

* [:backend:`5704`] You can now filter forms in the admin based on the payment backend
  used.
* [:backend:`5643`] Added ``heeftAlsAanspreekpunt`` to the StUF-ZDS registration plugin.
* [:backend:`5707`] Implemented prefill plugin to retrieve the preferences for the
  customer profile from customer interaction APIs like Open Klant.
* Included the latest SDK with the latest (beta version of the) renderer. We'd like
  everyone to actively test this now. Some known limitations at this point:

  * the map component integration is not available yet.
  * the customer profile component integration is not available yet.
  * the datepicker (``date`` and ``datetime`` components) has known (UX) issues.
  * themes may be broken due to missing design token values in custom themes.

Bugfixes
--------

* [:backend:`5737`] Fixed a crash in the form builder UI when the "synchronize variables"
  logic action is used and fieldset components are present.
* [:backend:`5735`] Fixed a crash when converting raw JSON data to the Python types when
  variables don't exist in the database in certain circumstances.
* [:cve:`CVE-2025-64515`] Fixed missing logic evaluation before validating (step data)
  user input. See :ghsa:`GHSA-cp63-63mq-5wvf` for details.
* Fixed the performance of the email verifications page in the admin.
* Fixed some crashes due to enabling certain optimizations, notably when:

  - Looking up the nearest address for map coordinates.
  - Looking up addresses in the Kadaster API.
  - Processing (single) file attachments in the generic registration plugin.

* [:backend:`5757`] Fixed a crash when attempting to submit a submission step with file
  upload attachments.
* [:backend:`5754`] Fixed a date/datetime/time formatting regression in the
  ``extraElementen`` of the StUF-ZDS registration plugin.
* Fixed crash in the MS Graph/Sharepoint registration plugin because it couldn't handle
  date/datetime/time objects in the JSON serialization.
* Fixed a bug in the OpenID library breaking our legacy callback endpoint compatibility
  layer.
* Fixed a crash in the processing of family members components data because of a
  difference in data format between StUF-BG and Haal Centraal Personen bevragen.
* [:backend:`5748`] Fixed the handling of a difference in data between Haal Centraal
  Personen Bevragen API and StUF-BG when retrieving family members data, preventing
  valid submission data from being accepted in children and partners components.
* [:backend:`5756`] Fixed an issue where at most one child would be retrieved for the
  children prefill when using StUF-BG.
* [:backend:`5765`] Fixed a regression introduced in the 3.3.3 security fix that would
  prevent valid values from being accepted in radio, select and selectboxes components
  with options sourced from a variable.
* Fixed the Token Exchange extension no longer functioning due to the OpenID library rework.
* [:backend:`5770`] Fixed a crash when registering data for the ``partners`` component
  with StUF-ZDS.
* [:backend:`5778`] Fixed crashes during registration with Objects API when there are
  date or datetime fields inside a repeating group.
* [:backend:`5784`] Fixed Worldline credit card payments authorization mode not being
  set to ``SALE``.

Project maintenance
-------------------

* Updated (development) frontend dependencies with their latest security fixes.
* Tweaked the CI pipeline to include a test run with stripped out ``assert`` statements.
* Enabled a linter rule that checks for possible bugs due to stripepd out ``assert``
  statements.
* Banned ``typing.cast`` usage through linter rule.
* Enabled an option in the type checker to error when error suppression is no longer
  necessary.
* Cleaned up CI pipelines by using our own reusable actions.
* Updated backend dependencies with their latest security fixes:

  - fonttools
  - Django

3.3.8 (2025-12-02)
==================

Bugfix release.

* [:backend:`5784`] Fixed Worldline credit card payments authorization mode not being
  set to ``SALE``.
* [:backend:`5778`] Fixed crashes during registration with Objects API when there are
  date or datetime fields inside a repeating group.
* [:backend:`5770`] Fixed a crash when registering data for the ``partners`` component
  with StUF-ZDS.

3.3.7 (2025-11-21)
==================

Hotfix for the ``all-extensions`` build variant.

* Fixed the Token Exchange extension no longer functioning due to the OpenID library rework.

3.3.6 (2025-11-20)
==================

Hotfix release.

* [:backend:`5765`] Fixed a regression introduced in the 3.3.3 security fix that would
  prevent valid values from being accepted in radio, select and selectboxes components
  with options sourced from a variable.
* [:backend:`5756`] Fixed an issue where at most one child would be retrieved for the
  children prefill when using StUF-BG.
* [:backend:`5748`] Fixed the handling of a difference in data between Haal Centraal
  Personen Bevragen API and StUF-BG when retrieving family members data, preventing
  valid submission data from being accepted in children and partners components.
* Fixed a crash in the processing of family members components data because of a
  difference in data format between StUF-BG and Haal Centraal Personen bevragen.

3.2.8 (2025-11-20)
==================

Hotfix release.

* [:backend:`5765`] Fixed a regression introduced in the 3.3.3 security fix that would
  prevent valid values from being accepted in radio, select and selectboxes components
  with options sourced from a variable.
* [:backend:`5748`] Fixed the handling of a difference in data between Haal Centraal
  Personen Bevragen API and StUF-BG when retrieving family members data, preventing
  valid submission data from being accepted in children and partners components.

3.3.5 (2025-11-19)
==================

Hotfix release.

* Fixed crash in the MS Graph/Sharepoint registration plugin because it couldn't handle
  date/datetime/time objects in the JSON serialization.
* Fixed a bug in the OpenID library breaking our legacy callback endpoint compatibility
  layer.

3.3.4 (2025-11-18)
==================

Hotfix release.

* [:backend:`5754`] Fixed a date/datetime/time formatting regression in the
  ``extraElementen`` of the StUF-ZDS registration plugin.
* [:backend:`5757`] Fixed a crash when attempting to submit a submission step with file
  upload attachments.

3.3.3 (2025-11-18)
==================

Bugfix release.

This release addresses a security issue - we recommend upgrading as soon as possible.
See below for a workaround if that isn't feasible.

**Validation bypass issue and workaround**

When Open Formulieren retrieves data via prefill from an authentic source, form builders
can prevent tampering with this data by marking it as "read only". However, this mechanism
didn't work as intended when the component is marked as "read only" via form logic based
on certain conditions.

As a workaround, you can invert the logic - initially mark the field as "read only" and
use logic to make it writable if no prefill data is available.

**Bugfixes**

* [:cve:`CVE-2025-64515`] Fixed missing logic evaluation before validating (step data)
  user input. See :ghsa:`GHSA-cp63-63mq-5wvf` for details.
* [:backend:`5735`] Fixed a crash when converting raw JSON data to the Python types when
  variables don't exist in the database in certain circumstances.
* [:backend:`5737`] Fixed a crash in the form builder UI when the "synchronize variables"
  logic action is used and fieldset components are present.
* Fixed a crash in the configuration overview when Worldline merchants are misconfigured.
* Fixed some crashes due to enabling certain optimizations, notably when:

  - Looking up the nearest address for map coordinates.
  - Looking up addresses in the Kadaster API.
  - Processing (single) file attachments in the generic registration plugin.

3.2.7 (2025-11-18)
==================

Bugfix release.

This release addresses a security issue - we recommend upgrading as soon as possible.
See below for a workaround if that isn't feasible.

**Validation bypass issue and workaround**

When Open Formulieren retrieves data via prefill from an authentic source, form builders
can prevent tampering with this data by marking it as "read only". However, this mechanism
didn't work as intended when the component is marked as "read only" via form logic based
on certain conditions.

As a workaround, you can invert the logic - initially mark the field as "read only" and
use logic to make it writable if no prefill data is available.

**Bugfixes**

* [:cve:`CVE-2025-64515`] Fixed missing logic evaluation before validating (step data)
  user input. See :ghsa:`GHSA-cp63-63mq-5wvf` for details.
* [:backend:`5735`] Fixed a crash when converting raw JSON data to the Python types when
  variables don't exist in the database in certain circumstances.

3.4.0-alpha.1 (2025-11-10)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

Upgrade procedure
-----------------

To upgrade to 3.4, please:

* ⚠️ Ensure you are currently on Open Forms 3.2.x or newer.

.. warning:: If you've built dashboards using the metrics telemetry, you'll need to
   update them with the updated metric names. The new names are in the documentation.

New features
------------

* [:backend:`5687`] Added the initial structure of JCC (REST) API appointment plugin,
  which will replace the SOAP API variant.
* [:backend:`5694`] Address details for appointment locations are now available for display.
* [:backend:`5683`] The form import endpoint now returns the UUID of the imported form.
* [:backend:`4357`] You can now use theme-specific favicons, organization names and
  logos.
* [:backend:`5546`] Improved the accessibility toolbar layout:

  - Moved the "print page" button to the footer.
  - Aligned the "back to top" link with the navigation controls.
  - Added an optional visual separator between the form and accessibility toolbar.
  - Fixed the toolbar not being shown on mobile devices.
  - Added the missing navigation role label.
  - The appearance can be tweaked with a number of new design tokens.

Bugfixes
--------

* Fixed a crash in the upgrade migrations for form variables pointing to a component
  that cannot be resolved.
* [:backend:`5722`] Fixed Worldline configuration not taking into account multiple
  webhook key ID + secret combinations when multiple PSPIDs are used.
* [Sentry#453174] Fixed a crash in the configuration overview for invalid Worldline
  merchants.

Project maintenance
-------------------

* Renamed the metrics to comply with OTel naming conventions.
* Updated zgw-consumers to support OAUTH2-enabled services.
* The container image is now also published to
  `ghcr.io <https://github.com/open-formulieren/open-forms/pkgs/container/open-forms>`_.
* Removed incorrect deprecation marker on address autocomplete endpoint.
* Upgraded frontend dependencies with their latest security updates, affecting
  development tooling.
* Upgraded to mozilla-django-oidc-db and its improved type annotations.
* Added ``openforms.authentication``, ``openforms.data_removal`` and ``openforms.emails``
  to type-checked packages in CI.
* Added documentation on how to develop UI components.
* Bumped security update versions:

  - Django
  - brotli

* [DH#817] Added more logging and error information captures in case the Worldline
  payment flow errors.

3.3.2 (2025-11-05)
==================

Bugfix release.

* [:backend:`5134`] Fixed a crash occurring when processing empty date/datetime/time values.
* Upgraded Django to the latest security release.

3.3.1 (2025-10-29)
==================

Regular bugfix release.

* Fixed a crash in the upgrade migrations for form variables pointing to a component
  that cannot be resolved.
* [:backend:`5613`] You can now specify the ``SESSION_COOKIE_DOMAIN`` setting as an
  environment variable.
* [:backend:`5722`] Fixed Worldline configuration not taking into account multiple
  webhook key ID + secret combinations when multiple PSPIDs are used.

3.2.6 (2025-10-29)
==================

Regular bugfix release.

* [:backend:`5613`] You can now specify the ``SESSION_COOKIE_DOMAIN`` setting as an
  environment variable.
* [:backend:`5722`] Fixed Worldline configuration for transition not taking into account
  multiple webhook key ID + secret combinations when multiple PSPIDs are used.

3.4.0-alpha.0 (2025-10-10)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

Bugfixes
--------

* [:backend:`5134`] Fixed deriving the correct "empty value" value for date/time/datetime
  variables.
* Fixed a crash when trying to save a form with a component where the ``multiple``
  property was changed.
* [:backend:`3640`] Fixed a theoretical case where a submission would be able to be
  suspended while registration is in progress or completed.
* [:backend:`5429`] Fixed component label being truncated in the preview panel of the
  configuration modal.
* [:backend:`5391`] Fixed submission logs (incorrectly) reporting empty results for
  skipped prefill operations.
* [:backend:`3544`] Fixed submission pruning potentially deleting submissions that still
  have future appointments associated with them.

Project maintenance
-------------------

* Removed the deprecated privacy policy config endpoint.
* Removed some stale documentation.
* Updated compatible versions (backend/API/SDK) documentation.
* [:sdk:`445`] Updated the references to the new static assets locations in the SDK.
* [:backend:`5134`] Addressed some edge cases where logic rule evaluations could yield
  unexpected results, by fixing the ``clearOnHide`` behaviour implementation.

3.2.5 (2025-10-09)
==================

Regular bugfix release.

* [:backend:`5615`] Fixed the ZGW API's registration reporting as failure when case
  properties are used.
* Fixed Ogone Legacy merchant ID labels not being displayed in dropdown.
* [:backend:`5507`] Fixed mimetype detection for .msg files.
* [:backend:`5624`] Fixed broken StUF-BG request for children (family members)
  prefill request.
* [:backend:`5464`] Fixed a crash that occurred when incomplete options were used in
  JSON schema generation.

3.1.9 (2025-10-06)
==================

Final bugfix release in the ``3.1.x`` series.

* [:backend:`5615`] Fixed the ZGW API's registration reporting as failure when case properties are used.
* Fixed Ogone Legacy merchant ID labels not being displayed in dropdown.
* [:backend:`5507`] Fixed mimetype detection for .msg files.

3.3.0 "Donders mooi" (2025-10-02)
=================================

Open Forms 3.3.0 is a feature release.

.. epigraph::

   Donders mooi – an expression from the Twents dialect for ‘very beautiful’. This name is a reference
   to the origin of Open Formulieren by Dimpact and we thereby emphasize the cooperation
   with this partnership, located in Enschede, the biggest city of Twente.

This contains the changes from the alpha releases and fixes applied until the stable version.
BEFORE upgrading to 3.3.0, please read the release notes carefully and review the following
instructions.

Upgrade procedure
-----------------

To upgrade to 3.3, please:

* ⚠️ Ensure you upgrade to Open Forms 3.2.x before upgrading to the 3.3 release series.
* ⚠️ Plan an upgrade window to address the warnings below.
* ⚠️ An automatic Ogone-to-Worldline merchant migration requires unique merchant PSPIDs. This is
  automatically verified *before* performing the upgrade, but ideally you should run the check script of
  older patch versions in preparation.

.. warning:: The Open Telemetry SDK is enabled by default. If you don't have an endpoint to send system
    telemetry to, update your deployment code to disable it by setting the environment variable
    ``OTEL_SDK_DISABLED=true``.

    If you don't do this, warnings will be emitted to the container logs. The application will continue to work
    as usual.

.. warning:: Schedule the upgrade for off-peak hours. Some of the database migrations
   need to lock the entire table and/or can take a long time depending on the amount of
   data. We ran some benchmarks to get an idea of the duration.

   ============================================================= ============== ========
   Resource(s)                                                   Num records    Duration
   ============================================================= ============== ========
   Email messages + logs                                         50,000         ~30s
   Submissions, submission variables                             150,000        ~2s
   Submissions, submission variables                             13,600,000     ~10min
   Authentication infos                                          1,500          ~0.1s
   Authentication infos                                          230,000        ~2s
   ============================================================= ============== ========

.. warning::

    In this release, we reworked the internal data type information. To ensure submitted
    data of existing submissions is formatted correctly, the matching variables need to be
    processed. Note that we include this script instead of a data migration, so it can be
    run separately as it takes quite some time for large environments.

    .. code-block:: bash

        # in the container via ``docker exec`` or ``kubectl exec``:
        python /app/bin/fix_submission_value_variable_missing_fields.py

    See our benchmarks to get an indication of the execution time:

    ====================== ========
    Number of submissions  Duration
    ====================== ========
    7,000                  3.5min
    ====================== ========

.. warning::

    For the email and confirmation templates, and the registration backends, we changed
    the way that the data is generated. In case of key conflicts between static, component,
    and user-defined variables, the static variables will take precedence. Previously, the
    component and user-defined variables would override the static variables. Our validation
    guards against the use of keys that are already present in the static variables, but this
    does not cover old forms and newly-added static variables.

Major features
--------------

**💳 Worldline (Ogone replacement) support**

We implemented support for the Worldline payment provider as the Ogone Legacy payment provider
is being sunset on December 31st 2025 by Worldline.

We've provided automatic migrations as much as possible, and you can prepare for the migration as
of Open Forms 3.2.3 or 3.1.8. The documentation contains further details.

**🗺️ Map layers and advanced interactions**

You can now define your own overlay layers for the map component, e.g. to show BAG location on
top of the map base layer.

Additionally, the submission PDF now contains an equivalent image of the map instead of the raw
coordinates, including any defined overlays.

**🚸 Children component with prefill**

The previous minor release already introduced support for the partners component and this release adds
support for the new children component. Like the partners component, information like initials, last name, BSN and
date of birth of a child can be shown or provided.

This component also supports being prefilled through the family members prefill plugin, introduced in the previous
minor release and completes the support for the family members plugin.

**📈 Added application metrics**

We've built further on the previous observability improvements. Now metrics are emitted by
the application (for example the duration of HTTP requests, active requests, but also amount of forms,
submissions and user attachment metadata).

These metrics are exported using the Open Telemetry standard and can be incorporated in your existing
monitoring and visualization infrastructure.

Detailed changes
----------------

**New features**

* [:backend:`4480`] Improved the background/overlay layers in the map component:

  * [:backend:`5253`] The BRT (grey, pastel, water) background tile layers are now available by
    default in an Open Forms instance.
  * [:backend:`5251`] The identifier field from the map background tile layer is now automatically
    populated from its label.
  * [:backend:`4951`] The map component in the summary PDF is now an image instead of the textual location
    coordinates.
  * [:backend:`5618`] Added support for WMS on map image in submission pdf.

* [:backend:`5359`] Added support for the children component:

  * [:sdk:`825`] Added children component and updated email digest.
  * [:backend:`5268`] The registration plugins now support the ``children`` component type.
  * [:backend:`5269`] You can now use the ``children`` component data as source data for a
    repeating group to provide additional information with the new "synchronize variables" logic
    action type.

* [:backend:`4879`] Added support for Worldline as payment provider:

  - Support for Worldline's ``variant`` and ``descriptor`` fields.
  - The merchant reference is generated by Open Forms, similar to the Ogone plugin.
  - Ogone merchants are automatically migrated where possible.
  - Webhook configuration (if configured in a older patch release) is automatically migrated.
  - Added a bulk action to migrate forms from Ogone to Worldline.

* [:backend:`5478`] Added additional Yivi documentation.
* [:backend:`5428`] Updated the eIDAS (OIDC) LoA-Levels.
* [:backend:`5515`] Yivi Attribute groups now have a system-generated unique identifier.
* [:backend:`5515`] You can now export and import Yivi attribute groups.
* [:backend:`5479`] The eIDAS (via OIDC) configuration is now simplified - you can specify
  which claims can contain a BSN and/or Pseudo ID.
* [:backend:`5419`] Added prefill plugins for the new Yivi and eIDAS authentication backends.

* [:backend:`3999`] Added support for Open Telemetry metrics. All available metrics and details can be
  found in the "Observability" documentation.

* [:backend:`5095`] When authenticated via OpenID Connect (DigiD, eHerkenning, organization), upon
  submission completion you are now logged out at the identity provider.
* [:backend:`5133`] Added a feature flag to enable the new *experimental* renderer.
* [:backend:`5268`] Added "Partners Roltype" and "Partners omschrijving" registration
  configuration options for the ZGW APIs and StUF-ZDS registration plugins.
* [:backend:`5060`] Redis Sentinel is now supported as high availability strategy for the background
  jobs message broker.
* [:backend:`2324`] Reworked part of the logic engine in preparation of further
  performance improvements, so that we can correctly reason about variable data types.
* [:backend:`5382`] Forms now have an internal remarks field.

**Bugfixes**

* [:backend:`5225`] Fixed formio date and datetime components not having localized placeholders.
* [:backend:`5615`] Fixed the ZGW API's registration reporting as failure when case properties are used.
* [:backend:`5507`] Fixed mimetype detection for .msg files.
* [:backend:`5624`] Fixed broken StUF-BG request for children (family members) prefill request.
* [:backend:`5574`] Authentication-related static variables are no longer exposed to the
  confirmation email context.
* [:backend:`5464`] Fixed a crash that occurred when incomplete options were used in JSON schema generation.
* [:backend:`5605`] Fixed missing default value for DigiD ``loa`` causing a crash when trying to login.
* [:backend:`5572`] Fixed a crash in the StUF-ZDS registration plugin when another
  form has family member components in its configuration.
* [:backend:`5557`] Fixed uploaded filename sanitization.
* [:backend:`5439`] Removed warning message for deprecated feature to retrieve
  location via text fields.
* [:backend:`5384`] Fixed form export references to Objects API groups which can be
  provisioned through setup-configuration.
* [:backend:`5527`] Fixed all step data being returned during logic check of saved
  submission step instead of only the data that has changed.
* [:backend:`5475`] Fixed Yivi claims with periods not being usable in logic.
* [:backend:`5271`] Fixed false positives being reported in the digest email when you
  have logic rules that use the ``reduce`` operation.
* [:backend:`5481`] Fixed user defined variables not being queried based on the form of
  the current submission.
* [:backend:`5471`] Fixed BRP "doelbinding" advanced options not becoming available
  when using family members components.
* [:backend:`5340`] Fixed error handling during the validation of registration backends.
* [:backend:`5454`] Fixed Piwik Pro debug mode no longer working.
* [:backend:`5413`] Fixed uploading filenames with soft-hyphens not passing form validation.
* Fixed a crash when rendering e-mail HTML where links (anchor tags) contain bold or
  italic formatting elements.

**Project maintenance**

* Added a progressbar to the data backfill upgrade script.
* Added reusable github actions for i18n checks.
* Cleaned up and squashed migrations where possible.
* [:backend:`5325`] Update family members example in manual.

* [:backend:`5513`] Updated the OTel documentation and added various examples:

  - Basic nginx metrics and traces.
  - PostgreSQL metrics.
  - Redis metrics.

* [:backend:`5544`] Added documentation and examples on how to collect Flower metrics.
* Updated the documentation regarding the used SOAP operations for the StUF-ZDS plugin.

* Updated frontend dependencies:

  - Bumped @open-formulieren/formio-builder to 0.45.0.

* Updated backend dependencies:

  * Bumped Redis to version 8 for CI builds and the docker-compose setup.
  * Bumped zgw-consumers to version 1.0.
  * Upgraded to Django security release 4.2.25.
  * [:backend:`5356`, :backend:`5131`] Upgraded django-digid-eherkenning from 0.22.1 to 0.24.0.
  * [:backend:`5131`] Upgraded mozilla-django-oidc-db from 0.22.0 to 0.25.0.
  * [:backend:`5131`] Upgraded django-setup-configuration from 0.6.0 to 0.8.2.

* It's now possible to serve static assets with the reverse proxy (nginx) instead of the
  application server (uwsgi) through the ``STATIC_ROOT_VOLUME`` environment variable.
  Check the ``docker-compose.yml`` for a sample setup.
* Addressed some more test flakiness.
* [:backend:`5331`] Enabled extra type checking and fixed several type checking errors.
* Changed some primary key fields to bigint for tables that are frequently inserted into.
* Applied several best practices to the ``uwsgi`` configuration.
* Added CI check to detect missing frontend translations.
* Removed obsolete Ansible deployment example.
* [:backend:`5447`] Added an upgrade check to require version 3.2.0 before upgrading to
  3.3.0.
* Removed unused validation code.
* Enabled django-specific linter rules and fixed the violations.

* Replaced several code components with maykin-common dependency equivalent.

  * PDF generation
  * Admin env info
  * Server error page
  * System checks
  * Schema hook
  * Admin MFA integration
  * Admin index integration

* Removed the obsoleted form price logic model.

3.3.0-alpha.1 (2025-09-24)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

Upgrade procedure
-----------------

To upgrade to 3.3, please:

* ⚠️ Ensure you upgrade to Open Forms 3.2.x before upgrading to the 3.3 release series.
* ⚠️ Plan an upgrade window to address the warnings below.
* ⚠️ An automatic Ogone-to-Worldline merchant migration requires unique merchant PSPIDs. This is
  automatically verified *before* performing the upgrade, but ideally you should run the check script of
  older patch versions in preparation.

.. warning:: Schedule the upgrade for off-peak hours. Some of the database migrations
   need to lock the entire table and/or can take a long time depending on the amount of
   data. Some benchmarks on one million of rows in the submission variables table
   (~ 120K submissions) showed a migration time of around 20 seconds, so anywhere
   between 10 seconds - 5 minutes can be expected as a normal completion time depending
   on your data and available resources for the database.

.. warning::

    In this release, we reworked the internal data type information. To ensure submitted
    data of existing submissions is formatted correctly, submitted variables need to be
    processed. Note that we include this script instead of a data migration, so it can be
    run separately, as it can take up to an hour to complete the entire operation for large
    environments.

    .. code-block:: bash

        # in the container via ``docker exec`` or ``kubectl exec``:
        python /app/bin/fix_submission_value_variable_missing_fields.py

.. warning::

    For the email and confirmation templates, and the registration backends, we changed
    the way that the data is generated. In case of key conflicts between static, component,
    and user-defined variables, the static variables will take precedence. Previously, the
    component and user-defined variables would override the static variables. Our validation
    guards against the use of keys that are already present in the static variables, but this
    does not cover old forms and newly-added static variables.

Detailed changes
----------------

**New features**

* [:backend:`5268`] The registration plugins now support the ``children`` component type.
* [:backend:`5095`] When authenticated via OpenID Connect (DigiD, eHerkenning, organization), upon
  submission completion you are now logged out at the identity provider.
* [:backend:`4951`] The map component in the summary PDF is now an image instead of the textual location
  coordinates.
* [:backend:`5269`] You can now use the ``children`` component data as source data for a
  repeating group to provide additional information with the new "synchronize variables" logic
  action type.
* [:backend:`5575`] Added support for WMS tile layers in the map component, along
  with import/export functionality.
* [:backend:`5479`] The eIDAS (via OIDC) configuration is now simplified - you can specify
  which claims can contain a BSN and/or Pseudo ID.
* [:backend:`5060`] Redis Sentinel is now supported as high availability strategy for the background
  jobs message broker.
* [:backend:`5419`] Added prefill plugins for the new Yivi and eIDAS authentication backends.
* [:backend:`5515`] Yivi Attribute groups now have a system-generated unique identifier.
* [:backend:`5515`] You can now export and import Yivi attribute groups.
* [:backend:`5253`] The BRT (grey, pastel, water) background tile layers are now available by
  default in an Open Forms instance.
* [:backend:`5251`] The identifier field from the map background tile layer is now automatically
  populated from its label.

* [:backend:`4879`] Finished the support for Worldline as payment provider:

    - Support for Worldline's ``variant`` and ``descriptor`` fields.
    - The merchant reference is generated by Open Forms, similar to the Ogone plugin.
    - Ogone merchants are automatically migrated where possible.
    - Webhook configuration (if configured in a older patch release) is automatically migrated.
    - Moved the location in the admin of the feedback URL's used for the Worldline
      payment webhooks to the webhook configuration page.
    - Added a bulk action to migrate forms from Ogone to Worldline.

* [:backend:`5133`] Added a feature flag to enable the new *experimental* renderer.
* [:backend:`3999`] Added support for Open Telemetry metrics. All available metrics and details can be
  found in the "Observability" documentation.

**Bugfixes**

* [:backend:`5574`] Authentication-related static variables are no longer exposed to the
  confirmation email context.
* [:backend:`5464`] Fixed a crash that occurred when incomplete options were used in JSON schema generation.
* [:backend:`5605`] Fixed missing default value for DigiD ``loa`` causing a crash when trying to login.
* [:backend:`5572`] Fixed a crash in the StUF-ZDS registration plugin when another
  form has family member components in its configuration.
* [:backend:`5557`] Fixed uploaded filename sanitization.
* [:backend:`5439`] Removed warning message for deprecated feature to retrieve
  location via text fields.

**Project maintenance**

* [:backend:`5513`] Updated the OTel documentation and added various examples:

    - Basic nginx metrics and traces.
    - PostgreSQL metrics.
    - Redis metrics.

* [:backend:`5544`] Added documentation and examples on how to collect Flower metrics.
* Updated the documentation regarding the used SOAP operations for the StUF-ZDS plugin.
* Updated backend dependencies:

  - Bumped Redis to version 8 for CI builds and the docker-compose setup.
  - Bumped zgw-consumers to version 1.0.
  - Bumped @open-formulieren/formio-builder to 0.43.0.
  - Bumped mozilla-django-oidc-db to 0.25.1.
  - Bumped django-digid-eherkenning to 0.24.0.
  - Upgraded to Django security release 4.2.24.

3.2.4 (2025-09-10)
==================

Hotfix for DigiD login flow.

* [:backend:`5605`] Fixed a potential crash when attemping to log in to a form with
  DigiD. Explicitly setting the LOA for the form can be used as workaround.

3.2.3 (2025-09-09)
==================

Regular bugfix release.

.. note:: This release contains the ``report_duplication_merchant_pspids.py`` script.
   This script allows administrators to detect Ogone merchants that have the same
   ``PSPID`` value. As support for Ogone legacy will end at the end of 2025, this script
   allows administrators to prepare for the migration to Worldline merchants, which will
   not allow multiple merchants with the same ``PSPID`` value.

    .. code-block:: bash

        # in the container via ``docker exec`` or ``kubectl exec``:
        python /app/bin/report_duplication_merchant_pspids.py

* [:backend:`4879`] Added a report script to detect duplicate Ogone merchants.
* [:backend:`5572`] Fixed a crash in the StUF-ZDS registration plugin when another
  form has family member components in its configuration.
* [:backend:`4879`] Renamed the "Ogone webhook configuration" admin to "Worldline
  webhook configuration (transition)".

3.1.8 (2025-09-09)
==================

Regular bugfix release.

.. note:: This release contains the ``report_duplication_merchant_pspids.py`` script.
   This script allows administrators to detect Ogone merchants that have the same
   ``PSPID`` value. As support for Ogone legacy will end at the end of 2025, this script
   allows administrators to prepare for the migration to Worldline merchants, which will
   not allow multiple merchants with the same ``PSPID`` value.

    .. code-block:: bash

        # in the container via ``docker exec`` or ``kubectl exec``:
        python /app/bin/report_duplication_merchant_pspids.py

* [:backend:`4879`] Added a report script to detect duplicate Ogone merchants.
* [:backend:`4879`] Renamed the "Ogone webhook configuration" admin to "Worldline
  webhook configuration (transition)".

3.2.2 (2025-09-01)
==================

Hotfix release to fix file upload validation bug.

* Fixed a bug where link extraction from WYSIWYG elements could crash.
* [:backend:`5557`] Fixed a bug introduced in 3.1.5 causing non-alphanumeric characters
  in file upload names to trigger invalid validation errors.

3.1.7 (2025-09-01)
==================

Hotfix release to fix file upload validation bug.

* Fixed a bug where link extraction from WYSIWYG elements could crash.
* [:backend:`5557`] Fixed a bug introduced in 3.1.5 causing non-alphanumeric characters
  in file upload names to trigger invalid validation errors.

3.3.0-alpha.0 (2025-08-25)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

Upgrade procedure
-----------------

To upgrade to 3.3, please:

* ⚠️ Ensure you upgrade to Open Forms 3.2.x before upgrading to the 3.3 release series.
* ⚠️ Plan an upgrade window to address the warnings below.

.. warning:: Schedule the upgrade for off-peak hours. Some of the database migrations
   need to lock the entire table and/or can take a long time depending on the amount of
   data. Some benchmarks on one million of rows in the submission variables table
   (~ 120K submissions) showed a migration time of around 20 seconds, so anywhere
   between 10 seconds - 5 minutes can be expected as a normal completion time depending
   on your data and available resources for the database.

.. warning::

    In this release, we reworked the internal data type information. To ensure submitted
    data of existing submissions is formatted correctly, submitted variables need to be
    processed. Note that we include this script instead of a data migration, so it can be
    run separately, as it can take up to an hour to complete the entire operation for large
    environments.

    .. code-block:: bash

        # in the container via ``docker exec`` or ``kubectl exec``:
        python /app/bin/fix_submission_value_variable_missing_fields.py

.. warning::

    For the email and confirmation templates, and the registration backends, we changed
    the way that the data is generated. In case of key conflicts between static, component,
    and user-defined variables, the static variables will take precedence. Previously, the
    component and user-defined variables would override the static variables. Our validation
    guards against the use of keys that are already present in the static variables, but this
    does not cover old forms and newly-added static variables.

Detailed changes
----------------

**New features**

* [:backend:`5478`] Added additional Yivi documentation.
* [:backend:`5451`, :backend:`3999`] Added Open Telemetry support. The following metrics
  are now exposed:

    - HTTP request durations.
    - Number of "active requests".
    - Number of users, logins, logouts, failed logins, axes lockouts.
    - Submission starts, completions, paused and steps submitted.
    - Total amount of submissions by form or lifecycle stage.
    - Attachment file sizes and amount uploaded.

* [:backend:`2324`] Reworked part of the logic engine in preparation of further
  performance improvements, so that we can correctly reason about variable data types.
* [:backend:`4879`] You can now use the "Worldline" payment provider, which is the
  successor to Ogone legacy.
* [:sdk:`825`] Added children component and updated email digest.
* [:backend:`5382`] Forms now have an internal remarks field.
* [:backend:`5268`] Added "Partners Roltype" and "Partners omschrijving" registration
  configuration options for the ZGW APIs and StUF-ZDS registration plugins.
* [:backend:`5428`] Updated the eIDAS (OIDC) LoA-Levels.

**Bugfixes**

* [:backend:`5384`] Fixed form export references to Objects API groups which can be
  provisioned through setup-configuration.
* [:backend:`5527`] Fixed all step data being returned during logic check of saved
  submission step instead of only the data that has changed.
* [:backend:`5475`] Fixed Yivi claims with periods not being usable in logic.
* [:backend:`5271`] Fixed false positives being reported in the digest email when you
  have logic rules that use the ``reduce`` operation.
* [:backend:`5481`] Fixed user defined variables not being queried based on the form of
  the current submission.
* [:backend:`5471`] Fixed BRP "doelbinding" advanced options not becoming available
  when using family members components.
* [:backend:`5340`] Fixed error handling during the validation of registration backends.
* [:backend:`5454`] Fixed Piwik Pro debug mode no longer working.
* [:backend:`5413`] Fixed uploading filenames with soft-hyphens not passing form validation.
* Fixed a crash when rendering e-mail HTML where links (anchor tags) contain bold or
  italic formatting elements.

**Project maintenance**

* It's now possible to serve static assets with the reverse proxy (nginx) instead of the
  application server (uwsgi) through the ``STATIC_ROOT_VOLUME`` environment variable.
  Check the ``docker-compose.yml`` for a sample setup.
* Addressed some more test flakiness.
* [:backend:`5131`] Upgraded OIDC related packages.
  * django-digid-eherkenning from 0.22.1 to 0.23.0
  * mozilla-django-oidc-db from 0.22.0 to 0.25.0
  * django-setup-configuration from 0.6.0 to 0.8.2
* [:backend:`5356`] Updated django-digid-eherkenning which contains various UX improvements.
* [:backend:`5331`] Enabled extra type checking and fixed several type checking errors.
* Changed some primary key fields to bigint for tables that are frequently inserted into.
* Applied several best practices to the ``uwsgi`` configuration.
* Added CI check to detect missing frontend translations.
* Removed absolete ansible deployment example.
* Upgraded frontend dependencies reported by ``npm audit``.
* [:backend:`5447`] Added an upgrade check to require version 3.2.0 before upgrading to
  3.3.0.
* Removed unused validation code.
* Enabled django-specific linter rules and fixed the violations.
* Replaced several code components with maykin-common dependency equivalent.
  * PDF generation
  * Admin env info
  * Server error page
  * System checks
  * Schema hook
  * Admin MFA integration
  * Admin index integration
* Removed the obsoleted form price logic model.

3.2.1 (2025-08-19)
==================

Regular bugfix release.

.. note:: Worldline is ending support for Ogone Legacy at the end of 2025. Open Forms 3.3.0 will
   have support for the replacement. To make migrating easier, we've added new configuration options
   for the replacement:

   * *API Key* and *API Secret* fields for the merchants
   * Webhook configuration

   You can find these via configuration overview page. They are currently not used, but will make the
   automatic migration easier in Open Forms 3.3.0.

* [:backend:`4879`] Added fields to the `Ogone Merchant` and added the
  `Ogone webhook configuration`.
* [:backend:`5413`] Fixed uploading filenames with soft-hyphens not passing form validation.
* [:backend:`5471`] Fixed BRP "doelbinding" advanced options not becoming available
  when using family members components.
* [:backend:`5481`] Fixed incorrect lookup of the prefill-variable for a partners
  component variable.
* [:backend:`5271`] Fixed false positives being reported in the digest email when you
  have logic rules that use the ``reduce`` operation.
* [:backend:`5454`] Fixed Piwik Pro debug mode no longer working.


3.1.6 (2025-08-19)
==================

Regular bugfix release.

.. note:: Worldline is ending support for Ogone Legacy at the end of 2025. Open Forms 3.3.0 will
   have support for the replacement. To make migrating easier, we've added new configuration options
   for the replacement:

   * *API Key* and *API Secret* fields for the merchants
   * Webhook configuration

   You can find these via configuration overview page. They are currently not used, but will make the
   automatic migration easier in Open Forms 3.3.0.

* [:backend:`4879`] Added fields to the `Ogone Merchant` and added the
  `Ogone webhook configuration`.
* [:backend:`5271`] Fixed false positives being reported in the digest email when you
  have logic rules that use the ``reduce`` operation.


3.1.5 (2025-07-24)
==================

Regular bugfix release.

* [:backend:`5466`] Fixed translations for the cookie banner.
* [:backend:`5454`] Fixed Piwik Pro debug mode no longer working.
* [:backend:`5413`] Fixed uploading filenames with soft-hyphens not passing form validation.


3.2.0 "Nimma" (2025-07-11)
==========================

Open Forms 3.2.0 is a feature release.

.. epigraph::

    "Nimma" is an informal, affectionate nickname for one of the oldest cities in the Netherlands: Nijmegen.
    The name is often used by locals and conveys a sense of pride, solidarity, and personal identity.
    Naturally, we are also proud of the fact that Nijmegen contributes to Open Forms.

This contains the changes from the alpha releases and fixes applied until the stable version.
BEFORE upgrading to 3.2.0, please read the release notes carefully and review the following
instructions.

Upgrade procedure
-----------------

.. warning::

   The Camunda registration backend will be removed in Open Forms 4.0. There is no
   replacement scheduled - if you rely on this plugin, please get in touch.

.. warning::

    For the Generic JSON registration plugin, we changed the way that the data is generated.
    In case of key conflicts between static, component, and user-defined variables,
    the static variables will take precedence. Previously, the component and user-defined
    variables would override the static variables. Our validation guards against the use of
    keys that are already present in the static variables, but this does not cover old forms
    and newly-added static variables.

Major features
--------------

**🔊 Improved logging**

    We improved the logs that are emitted by the application, which enable better integration with observability
    tooling like Grafana.

**🛂 Authentication using Yivi and eIDAS**

    We implemented support for `Yivi <https://yivi.app/>`_ and `eIDAS <https://en.wikipedia.org/wiki/EIDAS>`_
    authentication via the OpenID Connect protocol. With support for Yivi authentication, end-users can decide which
    personal information they want to share with Open Forms.

    Support for eIDAS will allow European citizens without a DigiD (and/or BSN) to have access to forms which
    require authentication.

**👫 Partners component with prefill**

    We added a partners component, where information such as initials, last name, and date of birth of a
    partner can be shown or provided.

    This component can be prefilled using a new family members prefill plugin, that allows retrieving data from
    "Haal Centraal BRP personen bevragen" (version 2) or "StUF-BG" (version 3.1).

**📝 JSON schema generation**

    We added the possibility to generate a JSON schema of a form. It describes the submission data of all user-defined
    and component variables, and can be generated for the Generic JSON and Objects API registrations in the shape of
    the data produced by either of those plugins.

    The schemas of component variables also include a description and validation rules if they were specified
    in the configuration of these components.

Detailed changes
----------------

**New features**

* [:backend:`4966`, :backend:`5285`, :backend:`5334`] Improved the logs emitted by the application to better integrate
  with observability tooling like Grafana.

* [:backend:`5140`] Reworked the authentication module architecture to make it possible to add support for
  new plugins based on the OpenID Connect protocol (Yivi and eIDAS).

* [:backend:`5132`] Added support for authentication using Yivi via the OpenID Connect protocol.

    - Allows logging in to forms using DigiD, eHerkenning, or anonymously.
    - Additional attribute groups can be defined in the Yivi configuration, and relevant ones can be selected per form.
      These groups allow end-users to, optionally, provide additional personal or company details.

* [:backend:`4453`] Added support for authentication using eIDAS via the OpenID connect protocol. Allows European
  citizens without a DigiD (and/or BSN) to have access to forms which require authentication.

* [:backend:`5254`] Added new family members prefill plugin.

    - The data can be retrieved from "Haal Centraal BRP personen bevragen" (version 2) or "StUF-BG" (version 3.1).
    - Partners or children of the authenticated user can be stored in a user-defined variable.
    - The retrieved data of children can be filtered by age and whether they are deceased.

* [:backend:`4944`, :backend:`5268`, :sdk:`824`] Added partners component.

    - It is possible to manually add a partner, or to prefill the component using the new family members prefill plugin.
    - Partners can be registered through the StUF-ZDS registration.
    - Partner details are included in the email registration.
    - Configuration issues will be reported in the digest email.

* [:backend:`4923`, :backend:`5312`, :backend:`5027`] Added JSON schema generation of a form.

    - The schema can be generated from the **Registration** tab for the Objects API and Generic JSON plugins,
      and it represents the shape of the data produced by either of these plugins.
    - All user-defined and component variables are included in the schema.
    - The component schemas include validation rules and a description when available.

* [:backend:`5174`] Added possibility to configure a description for 'zaakbetrokkenen' (registrators, cosigners, or
  partners) in the StUF-ZDS plugin.
* [:backend:`4877`] Added support for attaching a copy of the confirmation email(s) sent to the initiator to a created
  case in the ZGW API's and StUF-ZDS registrations.
* [:backend:`5193`] Added `exp` claim to JWT in ZGW APIs.
* [:backend:`5283`] Cleaned up the displayed columns in the admin form list to improve the UX.

**Bugfixes**

* [:backend:`5394`] Fixed crash when saving DigiD or eHerkenning configuration in the admin.
* [:backend:`5041`] Fixed components with a period in their key not being added to the data in the Generic JSON
  registration.
* Fixed hidden selectboxes component being present in the submission data as an empty object.
* [:backend:`5326`] Fixed out-of-memory errors during email clean-up.
* Fixed default value of the ``clearOnHide`` option not matching the frontend.
* [:backend:`5303`] Fixed user-defined variables jumping around because of the auto-sort.
* [:backend:`4401`] Fixed infinite redirect loop on misconfigured OIDC authentication backend.
* [:backend:`5300`] Fixed a regression in the previous alpha release where nested submission data was not being saved.
* [:backend:`4933`] Fixed missing Cosign v2 information for registration email templates.
* [:backend:`5245`] Fixed broken variable-mapping configuration when multiple registration backends
  are available on a form.
* [:backend:`5214`] Fixed employee ID not being used in the authentication context when the
  organization-via-OIDC plugin is used.
* [:backend:`5238`] Fixed the order of form versions in version history.
* [:backend:`5263`] Fixed double encoding of data in generic JSON registration plugin.
* [:backend:`5202`] Removed appointment information from the submission tab in the admin.
* [:backend:`5207`] Fixed two bugs regarding reference-list integration:

    - Fixed JSON schema generation for components that use reference lists as a data source in the
      generic JSON registration plugin.
    - Fixed valid items of invalid table being shown for components that use reference lists as a
      data source.

* Fixed the ‘transform to list’ setting for the Objects API variable options being available for all
  components.
* Fixed the ‘map to geometry field’ setting for the Objects API variable options being available for
  all components.
* [:backend:`5181`, :backend:`5235`, :backend:`5289`] Fixed incorrect ``null`` values in components.
* [:backend:`5243`] Fixed non-existing variables being included in the 'transform to list'
  option of the generic JSON registration and Objects API plugins.
* [:backend:`5239`] Fixed ``kvkNummer`` attribute not being sent in ZGW API's registration.
* [:backend:`4917`] Fixed the backwards-compatibility issues of the reworked form
  navigation. See `the SDK storybook <https://open-formulieren.github.io/open-forms-sdk/?path=/docs/developers-upgrade-notes-3-1-0--docs>`_
  for detailed upgrade documentation.
* Fixed API spec for strings with format 'uri' having an empty string as default value.
* Fixed HTML sanitization of design tokens.

**Project maintenance**

* [:backend:`5252`] Renamed JSON Dump plugin to Generic JSON registration.
* [:backend:`5179`, :backend:`5221`, :backend:`5139`] Optimized creation and access of data structures.
* [:backend:`5407`] Added note in the 3.1.0 upgrade procedure about migrations (possibly) taking a long time to
  complete.
* Enabled most of bugbear linter rules.
* Replaced OAS checks in CI with a re-usable workflow.
* Archived old release notes.
* Prepared migration to django-upgrade-check.
* Switched to bump-my-version from bump2version.
* Switched to ruff from black, isort, and flake8.
* Added script to verify that fix scripts work as expected.
* Fixed test flakiness.
* Fixed type checking.
* Enabled pyupgrade linter rules.
* Updated backend dependencies:

    - Bumped django to 4.2.23.
    - Bumped urllib3 to 2.5.0.
    - Bumped requests to 2.32.4.
    - Bumped vcrpy to 7.0.0.
    - Bumped h11 to 0.16.0.
    - Bumped httpcore to 1.0.9.
    - Bumped tornado to 6.5.
    - Bumped zgw-consumers to 0.38.0.
    - Bumped celery to 5.5.0.
    - Bumped django-privates to 3.1.1

* Updated frontend dependencies:

    - Bumped @open-formulieren/design-tokens to 0.59.0.
    - Bumped @open-formulieren/formio-builder to 0.41.1.


3.1.4 (2025-07-10)
==================

Regular bugfix release.

* [:backend:`5394`] Fixed crash when saving DigiD or eHerkenning configuration in the admin.
* [:backend:`5407`] Added note in the 3.1.0 upgrade procedure about migrations (possibly) taking a long time to
  complete.
* Fixed broken link.
* Updated backend dependencies:

    - Bumped django to 4.2.23.
    - Bumped requests to 2.32.4.
    - Bumped urllib3 to 2.5.0.
    - Bumped vcrpy to 7.0.0.
    - Bumped django-privates to 3.1.1.


3.0.9 (2025-07-09)
==================

Final bugfix release in the ``3.0.x`` series.

* Fixed broken link.
* Updated backend dependencies:

    - Bumped django to 4.2.23.
    - Bumped requests to 2.32.4.
    - Bumped urllib3 to 2.5.0.
    - Bumped vcrpy to 7.0.0.


3.1.3 (2025-06-06)
==================

Hotfix addressing a backport issue.

* [:backend:`5193`] Fixed missing backport of the zgw-consumers upgrade, causing a crash
  when editing services.
* [:backend:`5303`] Fixed user defined variables jumping around because of the auto-sort.
* Upgraded Django to the latest security release.


3.2.0-alpha.1 (2025-05-23)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

.. warning::

   The Camunda registration backend will be removed in Open Forms 4.0. There is no
   replacement scheduled - if you rely on this plugin, please get in touch.

.. warning::

    For the generic JSON registration plugin, we changed the way that the data is generated.
    In case of key conflicts between static, component, and user-defined variables,
    the static variables will take precedence. Previously, the component and user-defined
    variables would override the static variables. Our validation guards against the use of
    keys that are already present in the static variables, but this does not cover old forms
    and newly-added static variables.

**New features**

* [:backend:`5285`] Improved the logs emitted by the application to better integrate with observability tooling like
  Grafana.
* [:backend:`5140`] Reworked the authentication module architecture to make it possible to add support for
  new plugins based on the OpenID Connect protocol (Yivi and eIDAS).
* [:backend:`5283`] Cleaned up the displayed columns in the admin form list to improve the UX.
* [:backend:`5254`] Added new family-members prefill plugin.

    - The data can be retrieved from "Haal Centraal BRP personen bevragen" (version 2) or "StUF-BG" (version 3.1).
    - Partners or children of the authenticated user can be stored in a user-defined variable.
    - The retrieved data of children can be filtered by age and whether they are deceased.

* [:backend:`4923`] Added support for JSON schema generation of a form in the API.

    - The schema represents the submission data and includes all user-defined and component variables.
    - The component schemas include validation rules and a description when available.

**Bugfixes**

* [:backend:`5300`] Fixed a regression in the previous alpha release where nested submission data was not being saved.
* [:backend:`4933`] Fixed missing Cosign v2 information for registraton email templates.

**Project maintenance**

* [:backend:`5252`] Renamed JSON Dump plugin to Generic JSON registration.
* Enabled most of bugbear linter rules.
* Fixed test flakiness.
* Fixed type checking.
* Replaced OAS checks in CI with a re-usable workflow.
* Updated backend dependencies:

    - Bumped h11 to 0.16.0.
    - Bumped httpcore to 1.0.9.
    - Bumped django to 4.2.21.
    - Bumped tornado to 6.5.


3.1.2 (2025-05-23)
==================

Regular bugfix release.

**Bugfixes**

* [:backend:`5289`] Fixed crash in fix-script.
* [:backend:`4933`] Fixed missing Cosign v2 information for registraton email templates.

**Project maintenance**

* Upgraded django to 4.2.21 with the latest security patches.


3.0.8 (2025-05-23)
==================

Regular bugfix release.

**Minor security improvements**

On request the low severity security patches from 3.1.0 are backported.

* Administrators are no-longer able to change the submission summary PDF through the
  admin interface.
* SVGs uploaded through the admin interface, used for logos and favicons, are now
  automatically sanitized.
* The form preview seen by form designers in the admin now applies extra HTML sanitation
  on the client side. The backend already properly escaped this and the public UI was
  never affected.

**Bugfixes**

* [:backend:`5289`] Fixed crash in fix-script.
* [:backend:`4933`] Fixed missing Cosign v2 information for registraton email templates.

**Project maintenance**

* Upgraded django to 4.2.21 with the latest security patches.


3.2.0-alpha.0 (2025-04-25)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

.. warning::

   The Camunda registration backend will be removed in Open Forms 4.0. There is no
   replacement scheduled - if you rely on this plugin, please get in touch.

.. warning::

    For the generic JSON registration plugin, we changed the way that the data is generated.
    In case of key conflicts between static, component, and user-defined variables,
    the static variables will take precedence. Previously, the component and user-defined
    variables would override the static variables. Our validation guards against the use of
    keys that are already present in the static variables, but this does not cover old forms
    and newly-added static variables.

.. warning:: Manual intervention required

    In the 3.1.1 bugfix release we fixed a bug regarding the default values of some components
    being ``null``. We added a script to fix any forms that still might be affected by these
    issues. You should run this script after deploying the patch release, to make sure the
    default values of affected components are fixed.

    .. code-block:: bash

        # in the container via ``docker exec`` or ``kubectl exec``:
        python /app/bin/fix_component_default_values.py


**New features**

* [:backend:`5027`] Added support for broader range of GeoJSON in JSON schema generation for the
  map component: includes points, lines, and polygons.
* [:backend:`5193`] Added `exp` claim to JWT in ZGW APIs.

**Bugfixes**

* [:backend:`5245`] Fixed broken variable-mapping configuration when multiple registration backends
  are available on a form.
* [:backend:`5214`] Fixed employee ID not being used in the authentication context when the
  organization-via-OIDC plugin is used.
* [:backend:`5238`] Fixed the order of form versions in version history.
* [:backend:`5263`] Fixed double encoding of data in generic JSON registration plugin.
* [:backend:`5202`] Removed appointment information from the submission tab in the admin.
* [:backend:`5207`] Fixed two bugs regarding reference-list integration:

    - Fixed JSON schema generation for components that use reference lists as a data source in the
      generic JSON registration plugin.
    - Fixed valid items of invalid table being shown for components that use reference lists as a
      data source.

* Fixed the ‘transform to list’ setting for the Objects API variable options being available for all
  components.
* Fixed the ‘map to geometry field’ setting for the Objects API variable options being available for
  all components.
* [:backend:`5181`, :backend:`5235`, :backend:`5289`] Fixed incorrect ``null`` values in components.
* [:backend:`5243`] Fixed non-existing variables being included in the 'transform to list'
  option of the generic JSON registration and Objects API plugins.
* [:backend:`5239`] Fixed ``kvkNummer`` attribute not being sent in ZGW API's registration.
* [:backend:`4917`] Fixed the backwards-compatibility issues of the reworked form
  navigation. See `the SDK storybook <https://open-formulieren.github.io/open-forms-sdk/?path=/docs/developers-upgrade-notes-3-1-0--docs>`_
  for detailed upgrade documentation.

**Project maintenance**

* Archived old release notes.
* Prepared migration to django-upgrade-check.
* [:backend:`5179`, :backend:`5221`, :backend:`5139`] Optimized creation and access of data structures.
* Switched to bump-my-version from bump2version.
* Switched to ruff from black, isort, and flake8.
* Added script to verify that fix scripts work as expected.
* Fixed test flakiness.
* Updated backend dependencies:

    - Bumped zgw-consumers to 0.38.0.
    - Bumped celery to 5.5.0.

* Updated frontend dependencies:

    - Bumped @open-formulieren/design-tokens to 0.59.0.
    - Bumped @open-formulieren/formio-builder to 0.40.0.


3.1.1 (2025-04-16)
==================

Regular bugfix release.

.. warning:: Manual intervention required

    In this bugfix release we fixed a bug regarding the default values of some components
    being ``null``. We added a script to fix any forms that still might be affected by these
    issues. You should run this script after deploying the patch release, to make sure the
    default values of affected components are fixed.

    .. code-block:: bash

        # in the container via ``docker exec`` or ``kubectl exec``:
        python /app/bin/fix_component_default_values.py

**Bugfixes**

* [:backend:`5214`] Fixed employee ID not being used in the authentication context when
  the organization-via-OIDC plugin is used.
* [:backend:`5238`] Fixed the order of form versions in version history.
* [:backend:`5263`] Fixed double encoding of data in generic JSON registration plugin.
* [:backend:`5243`] Fixed non-existing variables being included in the 'transform to list'
  option of the generic JSON registration and Objects API plugins.
* [:backend:`5181`] Fixed incorrect ``null`` default values in components.
* [:backend:`5239`] Fixed ``kvkNummer`` attribute not being sent in ZGW API's registration.
* [:backend:`4917`] Fixed the backwards-compatibility issues of the reworked form
  navigation. See `the SDK storybook <https://open-formulieren.github.io/open-forms-sdk/?path=/docs/developers-upgrade-notes-3-1-0--docs>`_
  for detailed upgrade documentation.
* [:backend:`5245`] Fixed broken variable mapping configuration when multiple registration
  backends are available on a form.

**Project maintenance**

* Fixed test flakiness.

3.0.7 (2025-04-16)
==================

.. warning:: Manual intervention required

    In this bugfix release we fixed a bug regarding the default values of some components
    being ``null``. We added a script to fix any forms that still might be affected by these
    issues. You should run this script after deploying the patch release, to make sure the
    default values of affected components are fixed.

    .. code-block:: bash

        # in the container via ``docker exec`` or ``kubectl exec``:
        python /app/bin/fix_component_default_values.py

**Bugfixes**

* [:backend:`5214`] Fixed employee ID not being used in the authentication context when
  the organization-via-OIDC plugin is used.
* [:backend:`5238`] Fixed the order of form versions in version history.
* [:backend:`5181`] Fixed incorrect ``null`` default values in components.
* [:backend:`5239`] Fixed ``kvkNummer`` attribute not being sent in ZGW API's registration.
* [:backend:`5188`] Fixed wrong prefill fields/attributes being logged.
* [:backend:`5155`] Fixed ``initial_date_reference`` being lost on language change while
  filling out a form.
* [:backend:`4662`, :backend:`5147`] Fixed not-required selectboxes field preventing
  pausing the form.
* Fixed SAMLv2 metadata generation when multiple certificates are configured.
* Fixed the NLX directory URLs.
* [:backend:`5245`] Fixed broken variable mapping configuration when multiple registration
  backends are available on a form.

**Project maintenance**

* Fixed test flakiness.
* Updated backend dependencies:

    - Bumped zgw-consumers to 0.38.0
    - Bumped django-digid-eherkenning to 0.21.0

2.8.8 (2025-04-16)
==================

Final bugfix release in the ``2.8.x`` series.

.. warning:: Manual interventions required

    We included a script to remove corrupt API group configuration to make the upgrade
    to Open Forms 3.0 easier. This script removes API groups (Objects API and ZGW APIs)
    for which *no* services have been configured.

    In this bugfix release we fixed a bug regarding the default values of some components
    being ``null``. We added a script to fix any forms that still might be affected by
    these issues. You should run this script after deploying the patch release, to make
    sure the default values of affected components are fixed.

    .. code-block:: bash

        # in the container via ``docker exec`` or ``kubectl exec``:
        python /app/bin/delete_empty_api_groups.py
        python /app/bin/fix_component_default_values.py

**Bugfixes**

* [:backend:`5181`] Fixed incorrect ``null`` default values in components.
* [:backend:`5239`] Fixed ``kvkNummer`` attribute not being sent in ZGW API's registration.
* [:backend:`4662`, :backend:`5147`] Fixed not-required selectboxes field preventing
  pausing the form.

3.1.0 "Lente" (2025-03-31)
==========================

Open Forms 3.1.0 is a feature release.

.. epigraph::

    "Lente" is Dutch for "Spring". We've planted some seeds that will take time to
    bloom before their full potential is visible, but here and there you can already
    spot some flowers. Spring is typically a time in the year that's lighter and brings
    more joy, and we hope this release will do too.

This contains the changes from the alpha and fixes applied until the stable version.
BEFORE upgrading to 3.1.0, please read the release notes carefully and review the
following instructions.

Upgrade procedure
-----------------

To upgrade to 3.1, please:

* ⚠️ Ensure you upgrade to Open Forms 3.0.1 before upgrading to the 3.1 release series.

* ⚠️ Verify the amount of log records before applying the upgrade. [:backend:`4931`]
  introduced a migration which processes log records and therefore could take a
  long time to complete.

* We recommend running the ``bin/report_component_problems.py`` and
  ``bin/report_form_registration_problems.py`` scripts to diagnose any problems in
  existing form definitions. These will be patched up during the upgrade, but it's good
  to know which form definitions will be touched in case something looks odd. The scripts
  are also available in the latest 3.0.x patch release, so you can run them before
  starting the upgrade process.

* Due to some UX rework in the SDK, you may need to define additional design tokens if
  you use a custom theme.

* We never deliberately supported HTML in component labels/tooltips. Due to some
  additional sanitation being added, some elements may now be escaped. We urge you to
  **NOT** use HTML in places that don't have a rich text editor.

Where possible, we have included upgrade checks that can you inform about detected problems before
any database changes are made.

Major features
--------------

**📒 Referentielijsten API integration**

We added support for the Referentielijsten API to Open Forms. In that API, you can
centrally manage (semi) fixed lists of data, such as districts, communication channels,
days of the week...

These reference lists can be used in Open Forms to populate the possible options in
select, selectboxes and radio components, making it easier to re-use these across forms.

**📦 JSON Dump registration**

We added a new registration plugin that allows for the simple transfer of form
variables and metadata in JSON format to a configured service. Form designers can select
which variabels to send to this external API, and then the values and schema describing
the structure of the variables is sent as JSON, making it easy to process the data.

**🗺 Map component rework**

The map component has undergone a major rework to support a wider range of use cases.

The most notable change is the expanded range of possible interactions users can have
with the map component. Previously, only pin placement was supported. This has now been
extended to include drawing multi-point lines and polygons.

You can now also use alternative background ("tile") layers (e.g. aerial imagery)
instead of the default BRT layer from the Kadaster.

.. note:: The ``map`` component rework is not complete yet and some more improvements
   are needed to optimize the user experience.

**♿️ Accessibility improvements**

Improving accessibility is a continuous effort, but in this release in particular we
could focus on it more. The submission summary PDFs have been made much more accessible
and informative. The form navigation for end-users has had an overhaul - backed by
proper research and user tests - particularly improving the experience on wide screen
devices.

The form designers should also see some (smaller) UX improvements, making it a bit
easier to manage form variables and creating a better overview.

**New features**

* [:backend:`5137`] The request header name for the ``OIN`` sent in "Haal Centraal BRP
  Personen bevragen" is now configurable.
* [:backend:`5122`] Clarified the help-text for the Ogone legacy ``TITLE`` and ``COM``
  parameters.
* [:backend:`5074`] Added an option to send the data from the selectboxes component as
  a list to the Objects API and JSON Dump registrations.
* UX: variables are now grouped by form step in the variables tab.
* [:backend:`5047`] Improved the accessibility of the submission summary PDF.

    - Added a textual alternative to the logo.
    - Provided an semantic relationship between the form field label and user provided
      value.
    - The PDF displays "No information provided" for form fields that haven't been
      filled in by the user.

* [:backend:`4991`, :backend:`4993`, :backend:`5016`, :backend:`5107`, :backend:`5106`,
  :backend:`5178`] Added Referentielijsten API support. You can now use reference lists
  as source for select, radio and selectboxes component options.

    - Allow using the referentielijsten as data source, which requires selecting a service
      and table to use.
    - We're prepared for multi-language support already.
    - Administrators get notified of expiring/expired tables and/or items.

* [:backend:`4518`] Added prefill attempts to the submission log entries.
* Performance improvements regarding fetching and processing form data.
* [:backend:`4990`] Registration variables in the form variables tab now show from which
  registration backend they originate.
* [:backend:`5093`, :backend:`5184`] Improved user experience when working with array or
  object values in the form variables table.
* [:backend:`5024`] Loosened validation on ZGW APIs and Objects API registration
  backends to support a broader range of vendors.
* [:backend:`2177`] Changed the map component output to GeoJSON geometry, allowing lines
  and polygons to be drawn on map components in addition to point markers.
* [:backend:`4908`, :backend:`4980`, :backend:`5012`, :backend:`5066`] Added new
  JSON Dump registration plugin.

    - Form designers control which variables get sent to the configured service.
    - The form/component information is used to automatically document the schema of
      each variable.
    - Includes fixed and configurable metadata of the form/submission.

* [:backend:`4931`] Upgraded the form submission statistics to reflect actual submissions
  and added the ability to export the results based on various filters.
* [:backend:`4785`] Updated the eHerkenning metadata generation to match the latest
  standard version(s).

**Minor security improvements**

We addressed some minor security concerns in case a rogue employee has access to the
admin interface.

* Administrators are no-longer able to change the submission summary PDF through the
  admin interface.
* SVGs uploaded through the admin interface, used for logos and favicons, are now
  automatically sanitized.
* The form preview seen by form designers in the admin now applies extra HTML sanitation
  on the client side. The backend already properly escaped this and the public UI was
  never affected.

**Bugfixes**

* [:backend:`5186`, :backend:`5188`] Fixed bugs regarding audit logs inadvertedly being
  created or not containing all expected information.
* [:backend:`5155`] Fixed the url parameter ``initial_data_reference`` being lost after
  switching the form language.
* [:backend:`5151`] Fixed hidden map components triggering validation errors.
* [:backend:`4662`, :backend:`5147`] Fixed bugs regarding the validation of selectboxes
  when "Minimum selected checkboxes" is configured:

    - Fixed optional selectboxes not passing validation when a minimum number is
      configured.
    - Fixed being unable to pause a form when it contains a selectboxes component with
      ``Minimum selected checkboxes >= 1``.

* [:backend:`5157`] Fixed warning being shown about missing co-sign translations when
  all translations are provided.
* [:backend:`5158`] Fixed a bug preventing removal of a ZGW API group.
* [:backend:`5142`] Fixed logic triggers being deleted when a selectboxes component is
  deleted.
* [:backend:`5105`] Fixed a minor styling bug in the admin that caused the asterisk icons
  for required fields to appear on top of dropdown menus.
* [:backend:`5124`] Fixed prefill fields causing validation errors when they are hidden
  and read-only.
* [:backend:`5031`] Fixed missing configuration in Objects API registration v2.
* [:backend:`5136`] Fixed eHerkenning "Dienstcatalogus" being generated using old
  certificates.
* [:backend:`5040`] Fixed a bug in the JSON logic where, when multiple logic actions were
  configured on the same trigger, deleting the first logic action caused its JSON logic
  to be assigned to the next logic action within the same trigger.
* [:backend:`5104`] Fixed ``null`` default value for radio fields.
* [:backend:`4871`] Fixed error messages not being shown in the variable mapping of the
  Objects API prefill and the JSON logic DMN configuration.
* [:backend:`5039`] Fixed error messages not being shown in the Email registration
  plugin.
* [:backend:`5090`] Fixed soft-required component blocking going to the next form step.
* [:backend:`5089`] Fixed service fetch automatically changing the configured query
  parameters from ``snake_case`` into ``camelCase``.
* [:backend:`5077`, :backend:`5084`] Fixed some performance issues regarding loading
  logic rules in the admin, and saving form steps/definitions with large numbers of
  components.
* [:backend:`4510`] Fixed error messages not shown properly on the form summary page.
* [:backend:`5037`] Fixed submission PDF not being able to format date values.
* [:backend:`5058`] Fixed race conditions and database errors being caused when editing
  forms, originally because of :backend:`4900`.
* [:backend:`4689`] Fixed file uploads in repeating groups not being processed correctly.
* [:backend:`5034`] Fixed Objects API registration plugin crashing by validating object's
  ownership only when the object should be updated.
* Fixed a misconfiguration for AddressNL end-to-end testing in CI.
* Fixed registration management command.
* Fixed styling of clearable react-select component.
* Fixed an upgrade check not blocking the database migrations from starting.
* [:backend:`5035`] Fixed duplicate values being sent by legacy Objects API registration
  plugin.
* [:backend:`4825`] Fixed prefill reporting false failures to daily digest when multiple
  authentication flows are used.

**Project maintenance**

* Reduced flakyness in the tests.
* Removing old upgrade checks, which won't be needed when upgrading from 3.0.x to 3.1.x.
* Some settings can now be configured with environment variables: ``AXES_FAILURE_LIMIT``
  and ``EMAIL_TIMEOUT``.
* [:sdk:`76`] Use ESM modules instead of UMD for the SDK, if the browser supports it.
* [:backend:`4927`] Added system check for missing configuration on non-required
  serializer fields.
* [:backend:`4882`] Added documentation on how to use django-setup-configuration.
* [:backend:`4654`] Cleaned up and squashed migrations where possible.
* Added constraint for requiring 3.0.1 before upgrading to 3.1.0.
* Updated backend dependencies

    - Bumped playwright to 1.49.1.
    - Bumped typing-extensions to 4.12.2.
    - Bumped django to 4.2.18.
    - Bumped django-digid-eherkenning to 0.21.0.
    - Bumped kombu to 5.5.
    - Bumped jinja2 to 3.1.6.
    - Bumped tzdata to 2025.1.

* Updated frontend dependencies

    - Bumped undici to 5.28.5.
    - Bumped @utrecht/components to 7.4.0.
    - Bumped @open-formulieren/design-tokens to 0.57.0.
    - Bumped storybook to 8.6.4.

3.0.6 (2025-03-17)
==================

Regular bugfix release.

.. warning:: Manual intervention required

    In the 3.0.2 bugfix release we fixed a bug regarding Objects API registration not
    being shown in the variables tab, and in 3.0.6 we fixed a bug regarding the default
    values of radio fields being ``null``. In this bugfix we added scripts to fix any forms
    that still might be affected by these issues. You should run these scripts after
    deploying the patch release, to make sure all Objects API registrations are correctly
    configured, and the default values of radio fields are fixed.

    .. code-block:: bash

        # in the container via ``docker exec`` or ``kubectl exec``:
        python /app/bin/fix_objects_api_form_registration_variables_mapping.py
        python /app/bin/fix_radio_component_default_values.py

    Alternatively, you can also manually edit all the affected forms in the
    admin interface. For the Objects API, this would require you to remove the Objects API
    registrations, and re-define them. For the radio fields, this would require you to change
    the ``defaultValue`` of all radio components from ``null`` to an empty string ``""``.


**Bugfixes**

* [:backend:`5158`] Fixed not being able to delete ZGW API groups.
* [:backend:`5142`] Fixed logic tab crashing and incorrectly displaying 0 component
  variables when removing fields from the form.
* [:backend:`5124`] Fixed hidden prefill fields triggering validation.
* [:backend:`5031`] Fixed missing ``variables_mapping`` in the Objects API registration
  plugin.
* [:backend:`5104`] Fixed ``null`` default values for radio fields.

2.8.7 (2025-03-17)
==================

Regular bugfix release.

.. warning:: Manual intervention required

    In the 2.8.4 bugfix release we fixed a bug regarding Objects API registration not
    being shown in the variables tab, and in 2.8.7 we fixed a bug regarding the default
    values of radio fields being ``null``. In this bugfix we added scripts to fix any forms
    that still might be affected by these issues. You should run these scripts after
    deploying the patch release, to make sure all Objects API registrations are correctly
    configured, and the default values of radio fields are fixed.

    .. code-block:: bash

        # in the container via ``docker exec`` or ``kubectl exec``:
        python /app/bin/fix_objects_api_form_registration_variables_mapping.py
        python /app/bin/fix_radio_component_default_values.py

    Alternatively, you can also manually edit all the affected forms in the
    admin interface. For the Objects API, this would require you to remove the Objects API
    registrations, and re-define them. For the radio fields, this would require you to change
    the ``defaultValue`` of all radio components from ``null`` to an empty string ``""``.

**Bugfixes**

* [:backend:`5158`] Fixed not being able to delete ZGW API groups.
* [:backend:`5142`] Fixed logic tab crashing and incorrectly displaying 0 component
  variables when removing fields from the form.
* [:backend:`5124`] Fixed hidden prefill fields triggering validation.
* [:backend:`5031`] Fixed missing ``variables_mapping`` in the Objects API registration
  plugin.
* [:backend:`5104`] Fixed ``null`` default values for radio fields.

3.0.5 (2025-03-03)
==================

Regular bugfix release.

.. warning:: Manual intervention required

    We fixed a bug that would mess with the validation of the soft-required components.
    A script is included to fix the forms that are affected - you need to run this
    after deploying the patch release.

    .. code-block:: bash

        # in the container via ``docker exec`` or ``kubectl exec``:
        python /app/bin/fix_softrequired_component_required_validation.py

    Alternatively, you can also manually edit all the affected forms in the
    admin interface. Simply edit the soft-required components by opening the ``JSON`` view
    and within the ``validate`` key change ``required: true`` to ``required: false``.

**Bugfixes**

* [:backend:`5086`, :backend:`5090`] Fixed soft-required errors being shown for hidden
  upload fields and blocking going to the next form step.
* [:backend:`5039`] Fixed some error messages not shown properly in the Email
  Registration plugin.
* Worked around some performance issues while evaluating form logic.
* [:backend:`5089`] Fixed service fetch configuration automatically changing from
  snake-case to camel-case.

2.8.6 (2025-03-03)
==================

Regular bugfix release.

* Worked around some performance issues while evaluating form logic.
* [:backend:`5089`] Fixed service fetch configuration automatically changing from
  snake-case to camel-case.

3.1.0-alpha.1 (2025-02-20)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

Hotfix release for a build issue in the previous sdk version.

* Fixed build issue in the sdk, causing errors when used with the backend.

3.1.0-alpha.0 (2025-02-17)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

Upgrade procedure
-----------------

⚠️ Ensure you upgrade to Open Forms 3.0.1 before upgrading to the 3.1.0 release series.

Detailed changes
----------------

**New features**

* [:backend:`5093`] Improved user experience when working with array values in the form
  variables table.
* [:backend:`5024`] Loosened validation on ZGW APIs and Objects API registration
  backends. Allowing configured domains to contain lowercase characters.
* [:backend:`4622`] Improved accessibility for logo used in submission report PDF.
* [:backend:`4882`] Added documentation on how to use django-setup-configuration.
* [:backend:`4993`] Retrieving select/selectboxes components values/options from
  Referentielijsten API.
* [:backend:`2177`] Changed the map component output to geoJson geometry. It's now
  possible to place pins, lines and polygons in the map component.
* Added the ability to configure ``AXES_FAILURE_LIMIT`` environment variable for defining
  the number of login attempts.
* [:backend:`4908`, :backend:`4980`, :backend:`5012`, :backend:`5066`] Added new
  JSON Dump registration plugin. Allowing submitted form data to be sent as a
  ``JSON object`` to a configured service.

    - Added documentation on how to use the JSON Dump registration plugin.
    - It's possible to quickly add all form variables to the data sent
      to the configured service, using a button in the plugin configuration.
    - You can include metadata when submitting data to a configured service.
    - Added JSON schema definitions to be sent along the submitted data to the configured
      service.
* [:backend:`4931`] Upgraded the form submission statistics to reflect actual submissions
  and added the ability to export the results based on various filters.
* [:backend:`4991`] Added selection of Referentielijsten API services to global
  configuration.
* [:backend:`4785`] Updated the eHerkenning metadata generation to match the latest
  standard version(s).

**Bugfixes**

* [:backend:`5077`] Fixed the performance issues when loading logic rules in the admin.
* [:backend:`5084`] Fixed the performance issues when saving form steps/definitions with
  large numbers of components (30-100), especially if they are reusable form definitions
  used in many (20+) forms. This was caused by an earlier patch for :backend:`5058`.
* [:backend:`4375`] Reverted "Removed environment variable
  ``DISABLE_SENDING_HIDDEN_FIELDS`` for Objects API."
* [:backend:`4510`] Fixed error messages not shown properly on the form summary page.
* [:backend:`5037`] Fixed submission PDF not able to format date values.
* [:backend:`5058`] Fixed race conditions and database errors being caused when editing
  forms, originally because of :backend:`4900`.
* [:backend:`4689`] Fixed file uploads in repeating groups not being processed correctly.
* [:backend:`5034`] Fixed Objects API registration plugin crashing by validating object's
  ownership only when the object should be updated.
* Fixed a misconfiguration for AddressNL end-to-end testing in CI.
* Fixed registration management command.
* Fixed styling of clearable react-select component.
* Fixed an upgrade check not blocking the database migrations from starting.
* [:backend:`5035`] Fixed duplicate values being sent by legacy Objects API registration
  plugin.
* Fixed default version handling for Objects API registration.
* [:backend:`4825`] Fixed prefill reporting false failures to daily digest when multiple
  authentication flows are used.

**Project maintenance**

* [:sdk:`76`] Use ESM modules instead of UMD for the SDK, if the browser supports it.
* Removed unused ``celery_worker.sh`` command line arguments.
* Addressed proptype warnings in SubmissionLimitFields components.
* [:backend:`4927`] Added system checking for missing configuration on non-required
  serializer fields.
* [:backend:`4654`] Cleaned up and squashed migrations where possible.
* Added constraint for requiring 3.0.1 before upgrading to 3.1.0.
* Updated bug report issue template according to new GitHub's types.
* Removed 2.7.x from supported versions in Docker Hub description.
* Added 3.0.x to Docker Hub description.
* Updated backend dependencies

    - Bumped playwright to 1.49.1.
    - Bumped typing-extensions to 4.12.2.
    - Bumped django to 4.2.18 patch release.
* Updated frontend dependencies

    - Bumped undici to 5.28.5.

3.0.4 (2025-02-06)
==================

Hotfix release for performance problems in the admin.

* [:backend:`5084`] Fixed the performance issues when saving form steps/definitions with
  large numbers of components (30-100), especially if they are reusable form definitions
  used in many (20+) forms. This was caused by an earlier patch for :backend:`5058`.

2.8.5 (2025-02-06)
==================

Hotfix release for performance problems in the admin.

* [:backend:`5084`] Fixed the performance issues when saving form steps/definitions with
  large numbers of components (30-100), especially if they are reusable form definitions
  used in many (20+) forms. This was caused by an earlier patch for :backend:`5058`.

3.0.3 (2025-02-05)
==================

Bugfix release on request.

* [:backend:`4375`] Reverted "Removed environment variable
  ``DISABLE_SENDING_HIDDEN_FIELDS`` for Objects API."

3.0.2 (2025-01-31)
==================

Regular bugfix release.

* [:backend:`4689`] Fixed file uploads in repeating groups not being processed correctly.
* [:backend:`5034`] Fixed Objects API registration plugin crashing when
  "update existing object" is not enabled.
* [:backend:`5035`] Fixed duplicate values being sent by legacy Objects API registration
  plugin.
* [:backend:`5058`] Fixed race conditions and database errors being caused when editing
  forms, originally because of :backend:`4900`.
* [:backend:`5021`] Fixed Objects API registration plugin not being shown in the
  variables tab when it has just been added.

2.8.4 (2025-01-31)
==================

Regular bugfix release

* [:backend:`5035`] Fixed duplicate values being sent by legacy Objects API registration
  plugin.
* [:backend:`5058`] Fixed race conditions and database errors being caused when editing
  forms, originally because of :backend:`4900`.

2.8.3 (2025-01-09)
==================

Regular bugfix release

* Backported check scripts for 3.0 upgrade.
* [:backend:`4795`] Fixed not always being able to upload ``.msg`` files.
* [:backend:`4900`] Fixed submission value variables recoupling for reusable form
  definitions.
* [:backend:`4579`] Fixed wrong steps being blocked when logic uses the "trigger from
  step" option.
* [:backend:`4825`] Fixed logging to only log empty retrieved data for the
  authentication flow that is used in the submission.
* [:backend:`4863`] Fixed authentication flow of an employee via OIDC.
* [:backend:`4955`] Fixed the order of coordinates in Objects API and in ZGW APIs.
* [:backend:`4821`] Fixed email digest for addressNL component, in combination with BRK
  validator.
* [:backend:`4886`] Fixed certain variants of CSV files not passing validation.
* [:backend:`4949`] Fixed modal close button on dark mode.
* [:backend:`4832`] Fixed json schema matcher in Objects API.
* [:backend:`4853`] Fixed registration backends serializers concerning non required
  fields.
* [:backend:`4824`] Ensured that the form variables are in line with the state of the
  form definitions after saving a form.
* [:backend:`4874`] Updated Dockerfile with missing scripts.
* Bumped packages to their latest (security) releases.
* [:backend:`4862`] Fixed unintended hashing of identifying attributes when the cosigner
  logs out.

3.0.1 (2025-01-10)
==================

Hotfix release addressing a potential upgrade issue.

* Fixed an upgrade check not blocking the database migrations from starting.

3.0.0 "Heerlijkheid" (2025-01-09)
=================================

Open Forms 3.0.0 is a feature release.

.. epigraph::

   Until the 19th century, the countryside of North and South Holland was divided into
   hundreds of small legal-administrative units, the 'lordships' (Heerlijkheid). The current
   municipalities can be considered as a kind of successors of the former lordships. The release
   name reflects the influence of various large and smaller municipalities on this release.
   This is also a "lordly" release with many features, improvements and clean-ups.

This contains the changes from the alpha and fixes applied until the stable version.
BEFORE upgrading to 3.0.0, please read the release notes carefully and review the instructions
in the documentation under **Installation** > **Upgrade details to Open Forms 3.0.0**.

Upgrade procedure
-----------------
Open Forms 3.0 is a major version and contains a number of breaking changes. We've done a lot of
internal cleanups and removed old and deprecated features. Of course we were mindful in removing
only obsolete/unused features and we expect the impact to be minor.

To upgrade to 3.0, please:

* ⚠️ Ensure you upgrade to Open Forms 2.8.2 before upgrading to the 3.0 release series.

* ⚠️ Please review the instructions in the documentation under **Installation** >
  **Upgrade details to Open Forms 3.0.0** before and during upgrading. You can find
  details for the deprecated code and how this might affect you.

Where possible, we have included upgrade checks that can you inform about detected problems before
any database changes are made. We will add (some) of these checks to the next 2.8.x patch release
to so you can run them to explore possible impact.

Major features
--------------

**📥 Objects API Prefill (a.k.a. product prefill)**

If you store information about requests/products for users in the Objects API, you can now use this data
to populate a form. For example to request or renew the product (object) again. Bits of information from the referenced
record are prefilled into form fields and variables.

Additionally, you can opt to update the existing object rather than create a new one during registration!

An example is defined in :ref:`Prefill examples <examples_objects_prefill>`.

**🖋️ Cosign flow improvements**

We now provide a much more intuitive user experience to have someone cosign a form submission - users need
to click less and in general we removed a lot of friction for this process.

On top of that, the new configuration options for cosign allow you to tweak the content of emails and screens
when cosigning is enabled in a form - from inviting someone to cosign to the confirmation page they get.

**💳 More powerful price calculations**

We made it simpler and more intuitive for form designers to define dynamic price logic rules - these are now
part of the regular logic rules. This also enables you to perform more complex calculations and interact with
external systems to retrieve pricing information!

**🛑 Limiting the amount of submissions**

You can now specify a maximum number of submissions for a given form, useful for limited availability/capacity
situations, such as raffles or sign-ups to events. Related to that, we expanded the statistics to allow exporting
the successfully registered submissions.

**🤖 Automatic technical configuration**

We're shipping some tooling for infrastructure teams that deploy Open Forms - this makes it possible to
provision some configuration aspects that previously had to be done in the admin interface via point-and-click.

We're still expanding on the covered configuration aspects, so stay tuned for more!

**🚸 User Experience improvements**

We have made a ton of user experience improvements in registration and prefill plugin configurations! No
more copying of URLs from other systems - instead, you select the relevant option in a dropdown.
Dropdowns that support a search field to wade through those tens or hundreds of available case types!

And, wherever you need to choose a form variable, you now have the options grouped by type of variable
*and* the context of where this variable occurs, topped of with a search field.

Detailed changes
----------------

**Breaking changes**

* [:backend:`4375`] Removed environment variable ``DISABLE_SENDING_HIDDEN_FIELDS`` for
  Objects API.
* Removed automatic patching for ``cosign_information`` template tag.
* [:backend:`3283`] Removed deprecated code (please review the instructions in the documentation
  under **Installation** > **Upgrade details to Open Forms 3.0.0** for all the necessary details):

    - ``registration_backend`` and ``registration_backend_options`` fields from form.
    - Old API location url.
    - Conversion of ``stuf-zds-create-zaak:ext-utrecht`` to ``stuf-zds-create-zaak`` during import.
    - Objecttype URL to UUID import conversion.
    - Backwards compatible styling.
    - Password Formio component.
    - Legacy formio translation converter.
    - Deprecated/disabled legacy OIDC callback endpoints by default.
    - Documented registration backend migration procedure.
    - Made Objects API and ZGW APIs group fields non-nullable where this is necessary.
    - Normalized API endpoints to use kebab-case instead of snake-case.
    - Removed unnecessary filter behaviour on form definitions endpoint.
    - Removed legacy machtigen context.
    - Removed old appointments flow and refactored code according to the new one.
    - Made submission in temporary file uploads non-nullable.
    - Removed conversion of form step URL to form step UUID.
    - Made form definition name read only.
* [:backend:`4771`] Removed price logic rules in favour of normal logic rules.

**New features**

* [:backend:`4969`] Improved the UX of the form designer:

    - The base form configuration tab now groups related fields and collapses them to declutter the UI.
    - Moved the introduction page configuration to clarify the difference with the introduction text fields.
* Registration plugins:

    * [:backend:`4686`] All the registration plugin configuration options are now consistently managed in a
      modal with better UX.

    * Email:

        * [:backend:`4650`] The email registration plugin now allows setting the recipient using form variables.
    * Objects API:

        * [:backend:`4978`] The "variables mapping" configuration is now the default - this does not affect existing
          forms.
        * Updated technical configuration documentation for Objects API.
        * [:backend:`4398`] You can now update a referenced existing object rather than create a new record.
          When the object is being updated, the BSN of the authenticated user is verified against the existing
          object data.
        * [:backend:`4418`] You can now map individual parts of the addressNL component.
    * ZGW APIs:

        * [:backend:`4606`] Improved the user experience of the plugin:

          - All dropdowns/comboboxes now have a search field.
          - You can now select which catalogue to use, which enables you to select the case and
            document types in dropdowns that show only relevant options.
          - During registration the plugin will now automatically select the right version of a case and
            document type.
          - The URL-based configuration can still be used, but it's deprecated and will be removed in the
            future.
        * [:backend:`4796`] You can now select a product to be set on the created case from the selected case
          type in the ZGW APIs registration plugin.
        * [:backend:`4344`] You can now select which Objects API group to use rather than "the first one"
          being used always.
    * StUF-ZDS:

        * [:backend:`4319`] You can now provide a custom document title for StUF-ZDS via the component
          configuration.
        * [:backend:`4762`] The cosigner identifier (BSN) is now included in the created case.
* Prefill plugins:

    * Added documentation for product prefill in user manual.

    * Objects API:

        * [:backend:`4396`, :backend:`4693`, :backend:`4608`, :backend:`4859`] You can now configure a variable
          to be prefilled from the Objects API (a.k.a. "product prefill"):

          - It's possible to assign individual properties from the object type to particular form variables.
          - To avoid duplicating configuration, you can copy the configuration from a configured registration
            backend.

* Payment plugins:

    * Ogone:

        * [:backend:`3457`] Custom ``title`` and ``com`` parameters can now be defined in Ogone payment plugin.
* [:backend:`4785`] Updated the eHerkenning metadata generation to match the latest standard version(s).
* [:backend:`4930`] It's now possible to export registered submission metadata via the form statistics
  admin page. This can be based on specific date range.
* The documentation of Open Forms is now available for offline access too. You can find a PDF link
  on the bottom of the page.
* [:backend:`2173`] The map component now supports using a different background/tile layer.
* [:backend:`4321`] Forms can now have a submission limit. The SDK displays appropriate messages when
  this limit is reached.
* [:backend:`4895`] Added metadata to the outgoing confirmation and cosign request emails.
* [:backend:`4789`, :backend:`4788`, :backend:`4787`] Added ``django-setup-configuration`` to programmatically
  configure Open Forms' connection details to the Objects and ZGW APIs. You can load a confguration file via
  the ``setup_configuration`` management command. Additional information/instructions are provided in
  :ref:`installation_configuration_cli`.
* [:backend:`4798`] Made the confirmation box consistent with other modals and improved the UX.
* [:backend:`4320`] Improved the cosign flow and the texts used in cosign flows, while adding more
  flexibility:

    - You can now use templates specifically for cosigning for the confirmation screen content,
      with the ability to include a 'cosign now' button.
    - You can now use templates specifically for cosigning for the confirmation email subject and content.
    - When links are used in the cosign request email, the cosigner can now directly click through without
      having to enter a code to retrieve the submission.
    - Updated the default templates with better text/instructions.
    - Updated translations of improved texts.
* [:backend:`4815`] The minimum submission removal limit is now 0 days, allowing submissions to be deleted on the
  same day they were created.
* [:backend:`4717`] Improved accessibility for site logo, error message element and PDF documents.
* [:backend:`4719`] Improved accessibility in postcode fields.
* [:backend:`4707`] You can now resize the Json Logic widgets.
* [:backend:`4720`] Improved accessibility for the skiplink and the PDF report.
* [:backend:`4764`] Added the ability to set the submission price calculation to variable.
* [:backend:`4716`] Added translations for form fields and associated error messages improvements.
* [:backend:`4524`, :backend:`4675`] Selecting a form variable is now more user friendly. Variables
  are logically grouped and a search box was added.
* [:backend:`4709`] Improved the error feedback if unexpected errors happening during form saving
  in the form designer.

**Bugfixes**

* [:backend:`4978`] Fixed accidental HTML escaping in summary PDF/confirmation email and marking a
  variable as a geometry one.
* Fixed help texts in Objects API prefill.
* [:backend:`4579`] Fixed wrong steps being blocked when logic uses the "trigger from step" option.
* [:backend:`4900`] Fixed submission value variables recoupling for reusable form definitions.
* [:backend:`4795`] Fixed not always being able to upload ``.msg`` and ``.zip`` files.
* [:backend:`4825`] Log prefill failures only for the relevant authentication flow applied in a form.
* [:backend:`4863`] Fixed a crash when organisation login is used for a form.
* [:backend:`4955`] Fixed wrong lat/long coordinates order being used in Objects API and ZGW APIs
  registration.
* [:backend:`4821`] Fixed the email digest incorrectly reporting BRK/addressNL configuration issues.
* [:backend:`4949`] Fixed Modal's close button on dark mode.
* [:backend:`4886`] Fixed certain variants of CSV files not passing validation on Windows.
* [:backend:`4832`] Fixed certain object type properties not being available in the registration variable
  mapping.
* [:backend:`4853`, :backend:`4899`] Fixed empty optional configuration fields not passing validation
  in multiple registration backends.
  backends.
* [:backend:`4884`] Ensured that no form variables are created for soft required errors
  component.
* [:backend:`4874`] Fixed Dockerfile concerning missing scripts.
* [:backend:`3901`] Fixed cosign state not taking the logic/dynamic behaviour of cosign
  component into account.
* [:backend:`4824`] Ensured that the FormVariables are in line with the state of the
  FormDefinitions after saving.
* Fixed Django admin form field markup after Django v4.2.
* Fixed long words taking a lot of place and pushing icons.
* Fixed markup of checkboxes with help text.
* Fixed migration for update summary tag.
* [:backend:`4320`] Fixed ambiguous langugage in the summary PDF when the submission
  still requires cosigning.
* Fixed variables mapping by applying fallback for missing form values.
* [:backend:`4862`] Fixed unintended hashing of identifying attributes when the cosigner
  logs out.
* [:backend:`4732`] Fixed CSP issues for Expoints and Govmetric analytics.
* Fixed examples in the documentation for logic with date and duration calculations.
* [:backend:`4745`] Fixed missing registration variable to the Objects API with all
  the attachment URLs.
* [:backend:`4823`] Fixed uploaded files with leading or trailing whitespaces in the
  filename.
* [:backend:`4810`] Fixed uppercase component variable values turing lowercase.
* [:backend:`4772`] Fixed select components with integer values being treated as numbers
  instead of strings.
* [:backend:`4727`] Fixed crash when a user defined variable was changed to an array
  datatype.
* Fixed type error in the preset nested validate schema for components.
* [:backend:`4802`] Fixed some dropdowns taking up more horizontal space than intended.
* [:backend:`4763`] Fixed temporary file uploads not being delete-able in the admin interface.
* [:backend:`4726`] Fixed the styling for form delete buttons.
* [:backend:`4744`] Fixed a performance regression in the logic check calls and general
  submission processing.
* [:backend:`4774`] Fixed ``textfield`` data not being converted to a string when numeric
  data is received from a prefill plugin.
* Fixed docs concerning invalid SSL certs and broken links.
* [:backend:`4765`] Fixed bug in components migration converter when multiple is True.
* [:backend:`4546`] Fixed the soft-required validation errors being shown in the summary PDF.
* Fixed validation error when saving a new form definition via the admin.
* [:backend:`4659`] Fixed ``null`` default values for text-based fields.
* [:backend:`4528`] Fixed vague error/log out situation when logging in with OIDC.
* [:backend:`3629`] Fixed submission bulk export crashing when the form has repeating
  groups.
* [:backend:`3705`] Updated timestamps in str representations.
* [:backend:`4713`] Fixed pre-request hook not running for all "Haal Centraal BRP
  Personen bevragen" operations (fixes Token Exchange extension).
* [:backend:`4600`] Fixed not all the content on the page getting translated after changing
  the form language.
* [:backend:`4733`] Fixed a segmentation fault that could occur in dev environments.
* [:backend:`4628`] Fixed a crash when copying a form with a "block next step" logic.
* [:backend:`4711`] Fixed broken submission form row styling.
* [:backend:`4695`] Fixed a performance issue during legacy Objects API registration
  plugin validation.
* [:backend:`4652`] Fixed misaligned validation errors in the form designer UI.
* [:backend:`4658`] Fixed certain variants of ZIP files not passing validation on Windows.
* [:backend:`4656`] Fixed a crash during validation when you have file upload components
  inside repeating groups.

**Project maintenance**

* Updated documentation concerning frontend toolchains and formio search strategies.
* [:backend:`4907`] Improved developer installation documentation.
* Improved the Storybook setup to be closer to the actual Django admin usage.
* [:backend:`4920`] Cleaned up and squashed migrations where this was possible.
* De-duplicated Open Forms version upgrade path checks.
* Documented expired domains for VCR testing.
* Reduced flakiness in test suite.
* [:backend:`3457`] Extended type checking to most of the payments app.
* Removed migration tests which relied on real models.
* Addressed warnings in DMN components.
* Removed duplicated MS Graph stories/plugin options.
* Removed unused ``uiSchema`` property from registration fields.
* Deleted obsoleted `.admin-fieldset` styling.
* Removed the custom helptext-as-tooltip styling and applied the default styling of Django.
* Replaced ``summary`` tag implementation with ``confirmation_summary``.
* Refactored/updated variables editor stories.
* [:backend:`4398`] Refactored the ``TargetPathSelect`` component.
* [:backend:`4849`] Updated prepare release template with missing VCR paths.
* Updated API endpoints concerning the language (NL -> En).
* [:backend:`4431`] Improved addressNL mapping backwards compatibility and refactored ObjectsAPI v2
  handler.
* Fixed recursion issues in component search strategies.
* Replaced duplicated code for payment/registration plugin configuration option forms, by adding a
  generic component.
* Now, we use explicit React config form for MS Graph registration options.
* Refactored demo plugins configuration to use modal.
* Cleaned up CI workflow.
* Removed 2.6.x from supported versions in Docker Hub description.
* Added 2.8.x to Docker Hub description.
* [:backend:`4721`] Updated the screenshots in the documentation for prefill and the
  Objects API manual.
* Moved 2.5 to unsupported versions in developer docs and documented 2.5.x EOL status.
* Updated frontend dependencies

    - Upgraded to MSW 2.x.
    - Dropped RJSF.
    - Storybook 8.3.5.
* Updated backend dependencies

    - Bumped Jinja2 to 3.1.5.
    - Bumped Django to 4.2.17 patch release.
    - Bumped tornado version.
    - Bumped lxml html cleaner.
    - Bumped waitress.
    - Bumped django-silk version to be compatible with Python 3.12.
    - Updated trivy-action to 0.24.0.

3.0.0-alpha.1 (2024-11-28)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

Detailed changes
----------------

**New features**

* [:backend:`4606`] Improved the user experience of the ZGW APIs registration plugin:

    - All dropdowns/comboboxes now have a search field.
    - You can now select which catalogue to use, which enables you to select the case and
      document types in dropdowns that show only relevant options.
    - During registration the plugin will now automatically select the right version of a case and
      document type.
    - The URL-based configuration can still be used, but it's deprecated and will be removed in the
      future.
* [:backend:`4418`] You can now map individual parts of the addressNL component in the Objects API
  registration plugin.
* [:backend:`4396`, :backend:`4693`] You can now configure a variable to be prefilled from the Objects API
  (a.k.a. "product prefill"):

    - It's possible to assign individual properties from the object type to particular form variables.
    - To avoid duplicating configuration, you can copy the configuration from a configured registration
      backend.
* [:backend:`4796`] You can now select a product to be set on the created case from the selected case type
  in the ZGW APIs registration plugin.
* [:backend:`4762`] The cosigner identifier (BSN) is now included in the created case in the StUF-ZDS
  registration plugin.
* [:backend:`4798`] Made the confirmation box consistent with other modals and improved the UX.
* [:backend:`4344`] You can now select which Objects API group to use in the ZGW APIs registration plugin
  rather than "the first one" being used always.
* [:backend:`4320`] Improved the cosign flow and the texts used in cosign flows, while adding more flexibility:

    - You can now use templates specifically for cosigning for the confirmation screen content,
      with the ability to include a 'cosign now' button.
    - You can now use templates specifically for cosigning for the confirmation email subject and content.
    - When links are used in the cosign request email, the cosigner can now directly click through without
      having to enter a code to retrieve the submission.
    - Updated the default templates with better text/instructions.
* [:backend:`4815`] Changed submission removal limit to 0, allowing submissions to be deleted after 0 days
  (i.e. on the same day).
* [:backend:`4717`] Improved accessibility for site logo, error message element and PDF documents.
* [:backend:`4707`] You can now resize the Json Logic widgets.
* [:backend:`4686`} All the registration plugin configuration options are now consistently managed in a
  modal with better UX.
* [:backend:`4720`] Improved accessibility for the skiplink and the PDF report.
* [:backend:`4719`] Improved accessibility in postcode fields.

**Bugfixes**

* [:backend:`4732`] Fixed CSP issues for Expoints and Govmetric analytics.
* Fixed examples in the documentation for logic with date and duration calculations.
* [:backend:`4745`] Fixed missing registration variable to the Objects API with all
  the attachment URLs.
* [:backend:`4810`] Fixed uppercase component variable values turing lowercase.
* [:backend:`4823`] Fixed uploaded files with leading or trailing whitespaces in the
  filename.
* [:backend:`4826`] Added a workaround for translatable defaults in database migrations.
* [:backend:`4772`] Fixed select components with integer values being treated as numbers
  instead of strings.
* [:backend:`4727`] Fixed crash when a user defined variable was changed to an array
  datatype.
* [:backend:`4802`] Fixed some dropdowns taking up more horizontal space than intended.
* Fixed some pre-configured component configurations not being applied entirely when adding them to the form.
* [:backend:`4763`] Fixed temporary file uploads not being delete-able in the admin interface.
* [:backend:`4726`] Fixed the styling for form delete buttons.
* [:backend:`4546`] Fixed the soft-required validation errors being shown in the summary PDF.

**Project maintenance**

* Upgraded to MSW 2.x.
* Bumped formio-builder version.
* [:backend:`3283`] Removed password Formio component.
* Upgraded some dependencies to their latest security releases.
* Dropped RJSF dependency.
* Bumped waitress.
* Replaced duplicated code for payment/registration plugin configuration option forms, by adding a generic
  component.
* Fixed recursion issues in component search strategies.

2.8.2 (2024-11-25)
==================

Regular bugfix release

.. warning:: Manual intervention required

    We fixed a bug that would mess with the default values of selectboxes components.
    A script is included to fix the forms that are affected - you need to run this
    after deploying the patch release.

    .. code-block:: bash

        # in the container via ``docker exec`` or ``kubectl exec``:
        python /app/bin/fix_selectboxes_component_default_values.py

    Alternatively, you can also manually open and save all the affected forms in the
    admin interface.

**Bugfixes**

* [:backend:`4732`] Fixed CSP issues for Expoints and Govmetric analytics.
* [:backend:`4745`] Fixed missing registration variable to the Objects API with all
  the attachment URLs.
* [:backend:`4810`] Fixed uppercase component variable values turing lowercase. See the
  remark above for additional instructions.
* [:backend:`4823`] Fixed uploaded files with leading or trailing whitespaces in the
  filename.
* [:backend:`4727`] Fixed crash when a user defined variable was changed to an array
  datatype.
* [:backend:`4320`] Fixed ambiguous langugage in the summary PDF when the submission
  still requires cosigning.

2.8.1 (2024-10-29)
==================

Regular bugfix release.

* [:backend:`4628`] Fixed a crash when copying a form with a "block next step" logic
  action.
* [:backend:`4713`] Fixed pre-request hook not running for all "Haal Centraal BRP
  Personen bevragen" operations (fixes Token Exchange extension).
* [:backend:`3629`] Fixed submission bulk export crashing when the form has repeating
  groups.
* [:backend:`4528`] Fixed vague error/log out situation when logging in with OIDC.
* [:backend:`4764`] Added ability to configure a form variable to use for the
  (calculated) submission price.
* [:backend:`4744`] Fixed a performance regression in the logic check calls and general
  submission processing.
* [:backend:`4774`] Fixed ``textfield`` data not being converted to a string when
  numeric data is received from a prefill plugin.

3.0.0-alpha.0 (2024-10-25)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

Detailed changes
----------------

**Breaking changes**

* [:backend:`4375`] Removed environment variable ``DISABLE_SENDING_HIDDEN_FIELDS`` for
  Objects API.

**New features**

* [:backend:`4546`] Added configuration options for soft-required validation of (file upload)
  fields to the form designer.
* [:backend:`4709`] Improved the error feedback if unexpected errors happening during form
  saving in the form designer.
* [:backend:`4524`, :backend:`4675`] Selecting a form variable is now more user friendly.
  Variables are logically grouped and a search box was added.
* [:backend:`4764`] You can now use a form variable as the source of the submission price
  to be paid.

**Bugfixes**

* [:backend:`3705`] Ensure timestamps are consistently displayed in the correct timezone
  in the admin interface.
* [:backend:`4600`] Fixed not all the content on the page getting translated after changing
  the form language.
* [:backend:`4659`] Fixed ``null`` default values for text-based fields.
* [:backend:`4733`] Fixed a segmentation fault that could occur in dev environments.
* [:backend:`4711`] Fixed broken submission form row styling.
* [:backend:`4695`] Fixed performance regression in Objects API (legacy) validation.
* [:backend:`4628`] Fixed a crash when copying a form with a "block next step" logic
  action.
* [:backend:`4713`] Fixed pre-request hook not running for all "Haal Centraal BRP
  Personen bevragen" operations (fixes Token Exchange extension).
* [:backend:`3629`] Fixed submission bulk export crashing when the form has repeating
  groups.

* [:backend:`4528`] Fixed vague error/log out situation when logging in with OIDC.
* [:backend:`4744`] Fixed a performance regression in the logic check calls and general
  submission processing.
* [:backend:`4774`] Fixed ``textfield`` data not being converted to a string when
  numeric data is received from a prefill plugin.

**Project maintenance**

* Updated Trivy image scanning CI pipeline.
* [:backend:`4588`] Reduced code duplication in payment related code.
* [:backend:`4721`] Updated the screenshots in the documentation for prefill and the
  Objects API manual.

2.8.0 "Drupa" (2024-10-02)
==========================

Open Forms 2.8.0 is a feature release.

.. epigraph::

   "Drupa" is an establishment close to the offices of the Open Forms development team.
   They have provided us with the necessary caffeinated beverages and occasional snack,
   and thus indirectly and unknowingly powered the development of Open Forms 😉.

   -- ☕

Upgrade notes
-------------

There are no manual actions required - all upgrades and migrations are automatic.

.. note:: The UX rework in the ZGW APIs registration plugin is not entirely finished
   yet. The Objects API integration in particular can be a bit confusing since it's not
   possible yet to select which Objects API should be used. The plugin now uses the API
   group that's listed first in the admin interface (**Admin** > **Miscellaneous** >
   **Objects API Groups**).

Major features
--------------

**📧 Email verification**

We added an additional (optional) layer of robustness for (confirmation) email delivery
and provide stronger guarantees about ownership of an email address.

You can now require email verification on email fields. Users submitting the form
receive a verification code on the provided email address, which they must enter to
confirm that it is indeed their email address. Forms with unverified email addresses
fail to submit and display useful error messages to the user.

**📜 Introduction page**

You can now define an optional introduction page that is shown *before* the users
starts the form submission. This is the ideal place to inform the users of the required
documents, what the procedure looks like or how long it typically takes to fill out the
form, for example.

**🚸 User experience (UX) improvements**

With Open Forms, we have every ambition to make work easier for form designers.
When setting up the registration plugins that process the form submissions especially
we knew we could make substantial improvements. For the Objects API's and ZGW API's
plugins, we have reduced the need to copy-and-paste "magic" hyperlinks and aim to remove
this need entirely in the future.

For the ZGW API's, this even means you don't have to worry anymore of updating the
configuration when you publish a new version of a "zaaktype" - the right version will
now automatically be selected.

Detailed changes
----------------

This contains the changes from the alpha, beta and fixes applied between the beta and
stable version.


**New features**

* [:backend:`4267`, :backend:`4567`, :backend:`4577`] Improved the UX of the Objects
  API registration options:

    - Configuration is now in a modal and changes in configuration require an explicit
      confirmation, meaning you can now explore more without potentially breaking the
      configuration.
    - Upgraded the API group, object type and object type version dropdowns with search
      functionality.
    - Configuration fields are now logically grouped. Optional settings are shown in a
      collapsed group to declutter the UI.
    - You can now select a catalogue from a dropdown (with search functionality) that
      contains the document types to use.
    - API groups (admin): you can now specify a catalogue and the descriptions of
      document types to use rather than entering the API URL to a specific version.

  These UX and configuration improvements are still work-in-progress, more will become
  available in next releases and we will also rework the ZGW API registration options.
* [:backend:`4051`] Added a better JSON-editor in a number of places, bringing them up
  to parity with the editor in the form builder:

    - Editing JSON logic triggers.
    - Editing JSON logic variable assignment expressions.
    - Editing service fetch mapping expressions.
    - Viewing the JSON-definition of logic rules and/or actions.
* [:backend:`4555`] Improved the UX of pre-fill configuration on the variables tab:

    - There is now a single summary column for the prefill configuration, instead of
      three separate columns.
    - Improved the wording/language used to differentiate between authorizee/authorised
      roles.
    - Editing the configuration is now done in a separate modal.

* [:backend:`4456`] The admin interface now clearly displays which environment you are
  on. You can disable displaying this information, and you can change the text and
  colors to easily differentiate between acceptance/production environments.
* [:backend:`4488`] The submisson report PDF now no longer opens in a new tab/window,
  the browser is forced to download it.
* [:backend:`4432`] Improved robustness in form designer interface when crashes occur
  because of external systems.
* [:backend:`4442`] Improved certificate handling and DigiD/eHerkenning via SAML
  configuration:

    - You can now upload password-protected private keys.
    - You can now configure multiple certificates for DigiD/eHerkenning. The "next"
      certificate will be included in the generated metadata so you can seamlessly
      transition when your old certificate is about to expire.
    - The metadata files are now forced as download to prevent formatting and copy/paste
      errors.

* You can now configure some django-log-outgoing-requests settings with environment
  variables.
* [:backend:`4575`] You can now configure the ``SENDFILE_BACKEND`` with an environment
  variable.
* [:backend:`4577`] We improved the user experience when configuring the Objects API
  registration plugin. Copy-pasting URLs is being phased out - you can now select the
  relevant configurations in dropdowns.
* [:backend:`4606`] Improved the user experience of the ZGW APIs registration plugin.
  We're making this consistent with the Objects API. More improvements will be done in
  the future.
* [:backend:`4542`] Email components now support optional verification - when enabled,
  users must verify their email address before they can continue submitting the form.
* [:backend:`4582`] The SAML metadata for the DigiD/eHerkenning identity providers is
  now automatically refreshed on a weekly basis.
* [:backend:`4380`] The StUF-ZDS registration plugin now supports sending payment
  details in the ``extraElementen`` data. For 2.7 this was available in an extension,
  which has been merged in core - migrating is automatic.
* [:backend:`4545`] You can now optionally configure an introduction page, which is
  displayed before the start of the form.
* [:backend:`4543`] You can now optionally enable a short progress summary showing the
  current step number and the total number of steps in a form.

.. note:: The ``addressNL`` component is not yet a fully capable replacement for
   individual address fields. Currently, it's only recommended for BRK-validation
   purposes.

**Bugfixes**

* Fixed a crash in the validation of form variables used in logic rules.
* [:backend:`4516`] Fixed imports (and error feedback) of legacy exports with Objects
  API registration backends. It should now be more clear that admins possibly need to
  check the Objects API groups configuration.
* [:backend:`4191`] Fixed a couple of bugs when adding a company as initator in the
  ZGW API's registration plugin:

    - Fixed the datatype of ``vestiging`` field in ZGW registration rollen/betrokkenen.
    - Fixed the ``aoaIdentificatie`` being empty - this is not allowed.

* [:backend:`4533`] Fixed Objects API registration options checkboxes not toggling.
* [:backend:`4502`] Fixed a problem where the registration-backend routing logic is not
  calculated again after pausing and resuming a submission.
* [:backend:`4334`] Fixed the email registration plugin not sending a payment-received
  email when "wait for payment to register" is enabled. This behaviour is to ensure that
  financial departments can always be informed of payment administration.
* [:backend:`4519`] Fixed form variable dropdowns taking up too much horizontal space.
* Backend checks of form component validation configuration are mandatory. All components
  support the same set of validation mechanism in frontend and backend.
* [:backend:`4560`] Fixed more PDF generation overlapping content issues. The layout no
  longer uses two columns, but just stacks the labels and answers below each other since
  a compromise was not feasible.
* Fixed upgrade check scripts for 2.7.x.
* [:backend:`4597`] Revert message for not-filled-in-fields in confirmation PDF back to
  just empty space.
* Fixed processing of empty file upload components in the Objects API registration plugin.
* Fixed an upgrade check incorrectly reporting problems.
* [:backend:`4627`] Fixed a crash in the eHerkenning-via-OIDC plugin if no ActingSubjectID
  claim is present.
* [:backend:`4602`] Fixed missing Dutch translation for minimum required checked items
  error message in the selectboxes component.
* [:backend:`4587`] Fixed the product not being copied along when copying a form.

**Project maintenance**

* [:backend:`4267`] Converted more existing tests from mocks to VCR.
* Added static type checking to the CI pipeline. We will continue to improve the
  type-safety of the code, which should result in fewer bugs and improve the developer
  experience.
* Upgraded a number of third-party packages.
* Simplified testing tools to test translation-enabled forms.
* [:backend:`4492`] Upload IDs are no longer stored in the session, which was obsoleted
  by relating uploads to a submission.
* [:backend:`4534`] Applied some memory-usage optimizations when interacting with the
  Catalogi API.
* Swapped out pip-tools with `uv <https://github.com/astral-sh/uv>`_ because it has much
  better performance.
* [:backend:`3197`] Upgraded to Python 3.12 from Python 3.10.
* Fixed some more sources of test flakiness.
* The random state from factory boy is now reported in CI to help reproduce test
  flakiness issues.
* [:backend:`4380`] There is now a mock service (docker-compose based) for a StUF-ZDS
  server.
* Added CI job to test upgrade check scripts/machinery.
* Addressed broken test isolation in CI leading to flaky tests.
* Upgraded a number of dependencies to their latest (security) releases.
* Improved the static type annotations in the codebase.
* Failing end-to-end tests now produce Playwright traces in CI to help debug the problem.
* Added a utility script to find VCR cassette directories.
* [:backend:`4646`, :backend:`4396`] Restructured the Objects API configuration to be
  in a shared code package, which can be used by the registration and prefill plugins.
* [:backend:`4648`] Corrected the documentation about the minimum PostgreSQL version
  (v12) and confirmed support for PostgreSQL 15.
* Squashed migrations.

2.8.0-beta.0 (2024-09-17)
=========================

The (first) beta version for 2.8.0 is available for testing now.

.. warning:: We encourage you to test out this beta version on non-production
   environments and report your findings back to use. This release is not suitable for
   production yet though.

Upgrade notes
-------------

There are no manual actions required - all upgrades and migrations are automatic.

.. note:: The UX rework in the ZGW APIs registration plugin is not entirely finished
   yet. The Objects API integration in particular can be a bit confusing since it's not
   possible yet to select which Objects API should be used. The plugin now uses the API
   group that's listed first in the admin interface (**Admin** > **Miscellaneous** >
   **Objects API Groups**).

Detailed changes
----------------

**New features**

* [:backend:`4577`] We improved the user experience when configuring the Objects API
  registration plugin. Copy-pasting URLs is being phased out - you can now select the
  relevant configurations in dropdowns.
* [:backend:`4606`] Improved the user experience of the ZGW APIs registration plugin.
  We're making this consistent with the Objects API. More improvements will be done in
  the future.
* [:backend:`4542`] Email components now support optional verification - when enabled,
  users must verify their email address before they can continue submitting the form.
* [:backend:`4582`] The SAML metadata for the DigiD/eHerkenning identity providers is
  now automatically refreshed on a weekly basis.
* [:backend:`4380`] The StUF-ZDS registration plugin now supports sending payment
  details in the ``extraElementen`` data. For 2.7 this was available in an extension,
  which has been merged in core - migrating is automatic.
* [:backend:`4545`] You can now optionally configure an introduction page, which is
  displayed before the start of the form.
* [:backend:`4543`] You can now optionally enable a short progress summary showing the
  current step number and the total number of steps in a form.

.. note:: The ``addressNL`` component is not yet a fully capable replacement for
   individual address fields. Currently, it's only recommended for BRK-validation
   purposes.

**Bugfixes**

* [:backend:`4597`] Revert message for not-filled-in-fields in confirmation PDF back to
  just empty space.
* Fixed processing of empty file upload components in the Objects API registration plugin.
* Fixed an upgrade check incorrectly reporting problems.
* [:backend:`4627`] Fixed a crash in the eHerkenning-via-OIDC plugin if no ActingSubjectID
  claim is present.
* [:backend:`4602`] Fixed missing Dutch translation for minimum required checked items
  error message in the selectboxes component.
* [:backend:`4587`] Fixed the product not being copied along when copying a form.

**Project maintenance**

* Addressed broken test isolation in CI leading to flaky tests.
* Upgraded a number of dependencies to their latest (security) releases.
* Improved the static type annotations in the codebase.
* Failing end-to-end tests now produce Playwright traces in CI to help debug the problem.
* Added a utility script to find VCR cassette directories.
* [:backend:`4646`, :backend:`4396`] Restructured the Objects API configuration to be
  in a shared code package, which can be used by the registration and prefill plugins.
* [:backend:`4648`] Corrected the documentation about the minimum PostgreSQL version
  (v12) and confirmed support for PostgreSQL 15.
* Squashed migrations.

2.8.0-alpha.0 (2024-08-09)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

Detailed changes
----------------

**New features**

* [:backend:`4267`, :backend:`4567`, :backend:`4577`] Improved the UX of the Objects
  API registration options:

    - Configuration is now in a modal and changes in configuration require an explicit
      confirmation, meaning you can now explore more without potentially breaking the
      configuration.
    - Upgraded the API group, object type and object type version dropdowns with search
      functionality.
    - Configuration fields are now logically grouped. Optional settings are shown in a
      collapsed group to declutter the UI.
    - You can now select a catalogue from a dropdown (with search functionality) that
      contains the document types to use.
    - API groups (admin): you can now specify a catalogue and the descriptions of
      document types to use rather than entering the API URL to a specific version.

  These UX and configuration improvements are still work-in-progress, more will become
  available in next releases and we will also rework the ZGW API registration options.
* [:backend:`4051`] Added a better JSON-editor in a number of places, bringing them up
  to parity with the editor in the form builder:

    - Editing JSON logic triggers.
    - Editing JSON logic variable assignment expressions.
    - Editing service fetch mapping expressions.
    - Viewing the JSON-definition of logic rules and/or actions.
* [:backend:`4555`] Improved the UX of pre-fill configuration on the variables tab:

    - There is now a single summary column for the prefill configuration, instead of
      three separate columns.
    - Improved the wording/language used to differentiate between authorizee/authorised
      roles.
    - Editing the configuration is now done in a separate modal.

* [:backend:`4456`] The admin interface now clearly displays which environment you are
  on. You can disable displaying this information, and you can change the text and
  colors to easily differentiate between acceptance/production environments.
* [:backend:`4488`] The submisson report PDF now no longer opens in a new tab/window,
  the browser is forced to download it.
* Support pre-filling form fields from existing data in the Objects API:

    - [:backend:`4397`] Added ability to store an object reference on the submission so
      that the information can be retrieve and pre-filled.
    - [:backend:`4395`] Added a flag to specify if an existing object needs to be
      updated during registration, or a new record should be created.

  This feature is currently under heavy development.
* [:backend:`4432`] Improved robustness in form designer interface when crashes occur
  because of external systems.
* [:backend:`4442`] Improved certificate handling and DigiD/eHerkenning via SAML
  configuration:

    - You can now upload password-protected private keys.
    - You can now configure multiple certificates for DigiD/eHerkenning. The "next"
      certificate will be included in the generated metadata so you can seamlessly
      transition when your old certificate is about to expire.
    - The metadata files are now forced as download to prevent formatting and copy/paste
      errors.

* [:backend:`4380`] You can now include more payment details/information in the StUF-ZDS
  and Objects API registration plugins:

    - Added support for storing and including the payment ID from the payment provider.
    - Added support to send the order ID, payment status and payment amount as
      ``extraElementen`` in StUF-ZDS.

  .. note:: Currently this requires the ``open-forms-ext-stuf-zds-payments`` extension,
     but it will land in Open Forms core in the future.

* You can now configure some django-log-outgoing-requests settings with environment
  variables.
* [:backend:`4575`] You can now configure the ``SENDFILE_BACKEND`` with an environment
  variable.

**Bugfixes**

* Fixed a crash in the validation of form variables used in logic rules.
* [:backend:`4516`] Fixed imports (and error feedback) of legacy exports with Objects
  API registration backends. It should now be more clear that admins possibly need to
  check the Objects API groups configuration.
* [:backend:`4191`] Fixed a couple of bugs when adding a company as initator in the
  ZGW API's registration plugin:

    - Fixed the datatype of ``vestiging`` field in ZGW registration rollen/betrokkenen.
    - Fixed the ``aoaIdentificatie`` being empty - this is not allowed.

* [:backend:`4533`] Fixed Objects API registration options checkboxes not toggling.
* [:backend:`4502`] Fixed a problem where the registration-backend routing logic is not
  calculated again after pausing and resuming a submission.
* [:backend:`4334`] Fixed the email registration plugin not sending a payment-received
  email when "wait for payment to register" is enabled. This behaviour is to ensure that
  financial departments can always be informed of payment administration.
* [:backend:`4519`] Fixed form variable dropdowns taking up too much horizontal space.
* Backend checks of form component validation configuration are mandatory. All components
  support the same set of validation mechanism in frontend and backend.
* [:backend:`4560`] Fixed more PDF generation overlapping content issues. The layout no
  longer uses two columns, but just stacks the labels and answers below each other since
  a compromise was not feasible.
* Fixed upgrade check scripts for 2.7.x.

**Project maintenance**

* [:backend:`4267`] Converted more existing tests from mocks to VCR.
* Added static type checking to the CI pipeline. We will continue to improve the
  type-safety of the code, which should result in fewer bugs and improve the developer
  experience.
* Upgraded a number of third-party packages.
* Simplified testing tools to test translation-enabled forms.
* [:backend:`4492`] Upload IDs are no longer stored in the session, which was obsoleted
  by relating uploads to a submission.
* [:backend:`4534`] Applied some memory-usage optimizations when interacting with the
  Catalogi API.
* Swapped out pip-tools with `uv <https://github.com/astral-sh/uv>`_ because it has much
  better performance.
* [:backend:`3197`] Upgraded to Python 3.12 from Python 3.10.
* Fixed some more sources of test flakiness.
* The random state from factory boy is now reported in CI to help reproduce test
  flakiness issues.
* [:backend:`4380`] There is now a mock service (docker-compose based) for a StUF-ZDS
  server.
* Added CI job to test upgrade check scripts/machinery.
