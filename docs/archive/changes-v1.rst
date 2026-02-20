=============
Open Forms v1
=============

All changes related to the major version 1 of Open Forms.

.. warning:: Open Forms v1 is no longer maintained.

1.1.11 (2023-04-17)
===================

This release marks the end-of-life (EOL) of the 1.1.x series per our versioning policy.

**Bugfixes**

* [:backend:`2791`] Fixed long words overflowing in the confirmation PDF.
* [:backend:`2850`] Fixed a crash in the AVG log viewer when certain log records of deleted
  submissions are displayed.
* Fixed mutatiesoort when doing StUF ``UpdateZaak`` calls
* [:backend:`2977`] Fixed StUF postcode not being uppercase
* Updated the bundled SDK version to 1.1.4

**Project maintenance**

* CI no longer installs the codecov package from PyPI (obsolete)
* Ignored deleted branch in changelog during docs link checking

1.1.10 (2023-02-28)
===================

Bugfix release with some fixes from newer versions applied.

* [:backend:`2520`] Fixed bug in mimetype validation for ``application/ms-word`` (and similar) files
* Bump required SDK version
* [:backend:`2717`] Fixed crash on StUF-ZDS when updating the payment status
* [:backend:`2671`] Fixed QR code background in dark mode
* [:backend:`2709`] Fixed (bandaid) inconsistent dynamic product price logic

1.1.9 (2023-12-23)
==================

Periodic bugfix release, addressing some blocking defects and upgrade issues.

* [:backend:`2331`] Fixed incorrect key validation problem which would block upgrades to 2.0+
* [:backend:`2385`] Fixed incomplete logic handling which would block upgrades to 2.0+
* [:backend:`2413`] Fixed fields being made visible by selectboxes in frontend logic not being
  visible in summary/pdf/emails
* [:backend:`2422`] Fixed invalid postcode format being sent to StUF-ZDS
* [:backend:`2494`] Fixed person details not being sent to StUF-ZDS if the submitter was not
  authenticated but instead filled out details manually.
* Fix docs build due to legacy renegotiation being disabled in openssl 3

1.1.8 (2022-11-07)
==================

Open Forms 1.1.8 fixes some bugs for which no workaround exists

* [:backend:`1724`] Fixed content fields showing as "required" field
* [:backend:`2117`] Fixed exporting submissions with conditionally filled form steps
* [:backend:`1899`] Fixed prefill-data tampering check rejecting data due to difference in
  formatting logic between prefill plugin and form data
* [:backend:`1351`] Ensure that number and currency components can accept negative values
* [:backend:`2135`] Fixed submission steps being deleted when deleting form steps and/or restoring
  old form versions. This did not affect data sent to registration backends.
* [:backend:`1957`] Fixed retrying submission registration in the admin when the maximum number
  of attempts was already reached.
* [:backend:`2301`] Fixed identifying attributes still being hashed for paused-and-resumed
  submissions. This caused the hashes to be sent to registration backends rather than
  the actual BSN/KVK/Pseudo attribute.
* [:backend:`2219`] Fixed CSS units usage for logo design tokens in (confirmation) emails

1.1.7 (2022-10-04)
==================

1.1.6 was broken due to a bad merge conflict resolution.

* [:backend:`2095`] Fixed accidentally removing the OF layer on top of Formio
* [:backend:`1871`] Ensure that fields hidden in frontend don't end up in registration emails

1.1.6 (2022-09-29)
==================

Bugfix release + preparation for 2.0.0 upgrade

* [:backend:`1856`] Fixed crash on logic rule saving in the admin
* [:backend:`1842`] Fixed crash on various types of empty StUF-BG response
* [:backend:`1832`] Prevent and handle location service rate limit errors
* [:backend:`1960`] Ensure design tokens override default style
* [:backend:`1957`] Fixed not being able to manually retry errored submission registrations having
  exceeded the retry limit
* [:backend:`1867`] Added more StUF-ZDS/ZGW registration fields.
* Added missing translation for max files
* [:backend:`2011`] Worked around thread-safety issue when configuring Ogone merchants in the admin
* [:backend:`2066`] Re-added key validation in form builder
* [:backend:`2055`] Added management command to check for invalid keys
* [:backend:`1979`] Added model to track currently deployed version

1.1.5 (2022-08-09)
==================

Security fix release

This release fixes a potential reflected file download vulnerability.

* Bumped Django and django-sendfile2 versions with fixes for :cve:`2022-36359`.
* [:backend:`1833`] Fixed submission being blocked on empty prefill data

1.1.4 (2022-07-25)
==================

Bugfix release

Note that this release includes a fix for Github security advisory :ghsa:`GHSA-g936-w68m-87j8`.

* Upgraded to latest Django security release
* [:backend:`1730`] Update allowed headers for nonce CSP header
* [:backend:`1325`] Added management command to check number of forms with duplicate component
  keys (required for upgrade to 1.2 when it's available)
* [:backend:`1723`] StUF-ZDS registration: a number of configuration options are now optional
* [:backend:`1769`] StUF-ZDS registration: you can now configure the confidentiality level of a
  document attached to the zaak
* [:backend:`1617`] Fixed crash on StUF onvolledige datum
* [:ghsa:`GHSA-g936-w68m-87j8`] Perform additional permission checks if the form requires
  login
* Backported Submission.is_authenticated from :backend:`1418`.

1.1.3 (2022-07-01)
==================

Periodic bugfix release

* [:backend:`1681`] Use a unique reference number every time for StUF-ZDS requests
* [:backend:`1687`] Added explicit submission step validate endpoint
* Fixed unintended camelization of response data
* Bumped API version to 1.1.1
* [:backend:`1693`] Fixed postcode validation errors by applying input mask normalization to prefill values
* [:backend:`1731`] Fixed crash with non-latin1 characters in StUF-calls (such as StUF-ZDS)

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

1.1.1 (2022-06-13)
==================

Security release (:cve:`2022-31040`, :cve:`2022-31041`)

This bugfix release fixes two security issues in Open Forms. We recommend upgrading
as soon as possible.

* [:cve:`2022-31040`] Fixed open redirect in cookie-consent 'close' button
* [:cve:`2022-31041`] Perform upload content validation against allowed file types
* [:backend:`1670`] Update error message for number validation

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

* [:backend:`1624`] Fixed list of prefill attributes refresh on prefill plugin change
* Fixed styling issue with card components in non-admin pages
* [:backend:`1628`] Make fieldset labels stand out in emails
* [:backend:`1628`] Made styling of registration email consistent with confirmation email
* Added raw_id_fields to submissions admin for a performance boost
* [:backend:`1627`] Fixed CSRF error when authenticating in the admin after starting a form
* Fixed cookie ``SameSite=None`` being used in non-HTTPS context for dev environments
* [:backend:`1628`] Added missing form designer translations for display/summary options
* [:backend:`1628`] Added vertical spacing to confirmation PDF pages other than the first page

.. note:: :backend:`1627` caused session authentication to no longer be available in the API
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

* [:backend:`1418`] Expose ``Submission.isAuthenticated`` in the API
* [:backend:`1404`] Added configuration options for required fields

  - Configure whether fields should be marked as required by default or not
  - Configure if an asterisk should be used for required fields or not

* [:backend:`565`] Added support for DigiD/eHerkenning via OpenID Connect protocol
* [:backend:`1420`] Links created by the form-builder now always open in a new window (by default)
* [:backend:`1358`] Added support for Mutual TLS (mTLS) in service configuration - you can now
  upload client/server certificates and relate them to JSON/SOAP services.
* [:backend:`1495`] Reworked admin interface to configure mTLS for SOAP services
* [:backend:`1436`] Expose ``Form.submissionAllowed`` as public field in the API
* [:backend:`1441`] Added submission-specific user logout endpoint to the API. This now clears the
  session for the particular form only, leaving other form session untouched. For
  authenticated staff users, this no longer logs you out from the admin interface. The
  existing endpoint is deprecated.
* [:backend:`1449`] Added option to specify maximum number of files for file uploads
* [:backend:`1452`] Added option to specify a validation regular-expression on telefone field
* [:backend:`1452`] Added phone-number validators to API for extensive validation
* [:backend:`1313`] Added option to auto redirect to selected auth backend
* [:backend:`1476`] Added readonly option to BSN, date and postcode components
* [:backend:`1472`] Improved logic validation error feedback in the form builder
* [:backend:`1482`, `backend`:`1510`] Added bulk export and import of forms functionality to the admin interface
* [:backend:`1483`] Added support for dark browser theme
* [:backend:`1471`] Added support for DigiD Machtigen and eHerkenning Bewindvoering with OIDC
* [:backend:`1453`] Added Formio specific file-upload endpoint, as it expects a particular
  response format for success/failure respones. The existing endpoint is deprecated.
* [:backend:`1540`] Removed "API" and "layout" tabs for the content component.
* [:backend:`1544`] Improved overview of different components in the logic rule editor.
* [:backend:`1541`] Allow some NL Design System compatible custom CSS classes for the content
  component.
* [:backend:`1451`] Completely overhauled "submission rendering". Submission rendering is used
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

* [:backend:`1458`] Submission registration attempts are now limited to a configurable upper
  bound. After this is reached, there will be no automatic retries anymore, but manual
  retries via the admin interface are still possible.
* [:backend:`1584`] Use the original filename when downloading submission attachments
* [:backend:`1308`] The admin interface now displays warnings and proper error messages if your
  session is about to expire or has expired. When the session is about to expire, you
  can extend it so you can keep working for longer times in the UI.

**Bugfixes**

All the bugfixes up to the ``1.0.8`` release are included.

* [:backend:`1422`] Prevent update of custom keys on label changes for radio button components
  in the form builder
* [:backend:`1061`] Fixed duplicate 'multiple' checkbox in email component options
* [:backend:`1480`] Reset steps with data if they turn out to be not applicable
* [:backend:`1560`] Fix prefill fields in columns not working (thanks @rbakels)

**Documentation**

* [:backend:`1547`] Document advanced rules for selectboxes
* [:backend:`1564`] Document how logic rules are evaluated

**Project maintenance**

* [:backend:`1414`] Removed ``GlobalConfiguration.enable_react_form`` feature flag
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
* [:backend:`1366`] default to allow CORS with docker-compose
* Remove SDK from docker-compose
* Add SMTP container to docker-compose stack for outgoing emails
* [:backend:`1444`] resolve media files locally too with WeasyPrint
* Update momentjs version (dependabot alert)
* [:backend:`1574`] Dropped Django 2.x SameSiteNoneCookieMiddlware

**Deprecations**

* [:backend:`1441`] The ``/api/v1/authentication/session`` endpoint is now deprecated. Use the
  submission-specific endpoint instead.
* [:backend:`1453`] The  ``/api/v1/submissions/files/upload`` endpoint is now deprecated. Use the
  formio-specific endpoint instead.
* ``Submission.nextStep`` is deprecated as it's unused, all the information to determine
  this is available from other attributes.

1.0.14 (2022-09-29)
===================

Final bugfix release in the ``1.0.x`` series.

* [:backend:`1856`] Fixed crash on logic rule saving in the admin
* [:backend:`1842`] Fixed crash on various types of empty StUF-BG response
* [:backend:`1832`] Prevent and handle location service rate limit errors
* [:backend:`1960`] Ensure design tokens override default style
* [:backend:`1957`] Fixed not being able to manually retry errored submission registrations having
  exceeded the retry limit
* [:backend:`1867`] Added more StUF-ZDS/ZGW registration fields.
* Added missing translation for max files
* [:backend:`2011`] Worked around thread-safety issue when configuring Ogone merchants in the admin
* [:backend:`2066`] Re-added key validation in form builder
* [:backend:`2055`] Added management command to check for invalid keys
* [:backend:`1979`] Added model to track currently deployed version

.. note:: This is the FINAL 1.0.x release - support for this version has now ended. We
   recommend upgrading to the latest major version.

1.0.13 (2022-08-09)
===================

Security fix release

This release fixes a potential reflected file download vulnerability.

* Bumped Django and django-sendfile2 versions with fixes for :cve:`2022-36359`.
* Fixed the filename of submission attachment file downloads
* [:backend:`1833`] Fixed submission being blocked on empty prefill data


1.0.12 (2022-07-25)
===================

Bugfix release

Note that this release includes a fix for Github security advisory :ghsa:`GHSA-g936-w68m-87j8`.

* Upgraded to latest Django security release
* [:backend:`1730`] Update allowed headers for nonce CSP header
* [:backend:`1325`] Added management command to check number of forms with duplicate component
  keys (required for upgrade to 1.2 when it's available)
* [:backend:`1723`] StUF-ZDS registration: a number of configuration options are now optional
* [:backend:`1769`] StUF-ZDS registration: you can now configure the confidentiality level of a
  document attached to the zaak
* [:backend:`1617`] Fixed crash on StUF onvolledige datum
* [:ghsa:`GHSA-g936-w68m-87j8`] Perform additional permission checks if the form requires
  login
* Backported Submission.is_authenticated from :backend:`1418`.

1.0.11 (2022-06-29)
===================

Periodic bugfix release

* [:backend:`1681`] Use a unique reference number every time for StUF-ZDS requests
* [:backend:`1687`] Added explicit submission step validate endpoint
* Fixed unintended camelization of response data
* Bumped API version to 1.0.2
* [:backend:`1693`] Fixed postcode validation errors by applying input mask normalization to
  prefill values
* [:backend:`1731`] Fixed crash with non-latin1 characters in StUF-calls (such as StUF-ZDS)

1.0.10 (2022-06-16)
===================

Hotfix following 1.0.9 - this is the same patch as 1.1.2.

1.0.9 (2022-06-13)
==================

Security release (:cve:`2022-31040`, :cve:`2022-31041`)

This bugfix release fixes two security issues in Open Forms. We recommend upgrading
as soon as possible.

* [:cve:`2022-31040`] Fixed open redirect in cookie-consent 'close' button
* [:cve:`2022-31041`] Perform upload content validation against allowed file types
* [:backend:`1670`] Update error message for number validation
* [:backend:`1560`] Fix prefill not working inside of nested/layout components

1.0.8 (2022-05-16)
==================

Bugfix maintenance release

* [:backend:`1568`] Fixed logic engine crash when form fields are removed while someone is
  filling out the form
* [:backend:`1539`] Fixed crash when deleting a temporary file upload
* [:backend:`1344`] Added missing translation for validation error key
* [:backend:`1593`] Update nginx location rules for fileuploads
* [:backend:`1587`] Fixed analytics scripts being blocked by the CSP
* Updated to SDK version 1.0.3 with frontend bugfixes
* Fixed API schema documentation for temporary upload GET

1.0.7 (2022-05-04)
==================

Fixed some more reported issues

* [:backend:`1492`] Fixed crashes when using file upload components with either a maximum filesize
  specified as empty string/value or a value containing spaces.
* [:backend:`1550`] Fixed form designer partial crash when adding a currency/number component
* Bump uwsgi version
* Ensure uwsgi runs in master process mode
* [:backend:`1453`] Fixed user feedback for upload handler validation errors
* [:backend:`1498`] Fixed duplicate payment completion updates being sent by registration backend(s)

1.0.6 (2022-04-25)
==================

Periodic bugfix release

* Bumped to SDK version 1.0.2 with frontend bugfixes
* Updated DigiD/eHerkenning/eIDAS integration library for breaking changes in some
  brokers per May 1st
* Bumped to latest Django security releases
* [:backend:`1493`] Fixed form copy admin (bulk/object) actions not copying logic
* [:backend:`1489`] Fixed layout of confirmation emails
* [:backend:`1527`] Fixed clearing/resetting the data of fields hidden by server-side logic

1.0.5 (2022-03-31)
==================

Fixed some critical bugs

* [:backend:`1466`] Fixed crash in submission processing for radio and select fields with numeric values
* [:backend:`1464`] Fixed broken styles/layout on some admin pages, such as the import form page

1.0.4 (2022-03-17)
==================

Fixed a broken build and security vulnerabilities

* [:backend:`1445`] ``libexpat`` had some security vulnerabilities patched in Debian which lead to broken
  XML parsing in the StUF-BG prefill plugin. This affected version 1.0.1 through 1.0.3, possibly
  also 1.0.0.

There are no Open Forms code changes, but this release and version bump includes the
newer versions of the fixed OS-level dependencies and updates to Python 3.8.13.

1.0.3 (2022-03-16)
==================

Fixed some more bugs discovered during acceptance testing

* [:backend:`1076`] Fixed missing regex pattern validation for postcode component
* [:backend:`1433`] Fixed inclusion/exclusion of components in confirmation emails
* [:backend:`1428`] Fixed edge case in data processing for email registration backend
* Updated Pillow dependency with :cve:`2022-22817` fix
* Bump required SDK release to 1.0.1

1.0.2 (2022-03-11)
==================

Fixed some issues with the confirmation PDF generation

* [:backend:`1423`] The registration reference is not available yet at PDF generation time,
  removed it from the template
* [:backend:`1423`] Fixed an issue with static file resolution while rendering PDFs, causing the
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

* [:backend:`1376`] Fixed straat/woonplaats attributes in Haal Centraal prefill plugin
* [:backend:`1385`] Avoid changing case in form data
* [:backend:`1322`] Demo authentication plugins can now only be used by staff users
* [:backend:`1395`, :backend:`1367`] Moved identifying attributes hashing to on_completion cleanup stage,
  registrations backends now no longer receive hashed values
* Fixed bug in email registration backend when using new formio formatters
* [:backend:`1293`, :backend:`1179`] "signature" components are now proper images in PDF/confirmation email
* Fixed missing newlines in HTML-mail-to-plain-text conversion
* [:backend:`1333`] Removed 'multiple'/'default value' component options where they don't make sense
* [:backend:`1398`] File upload size limit is now restricted to integer values due to broken
  localized number parsing in Formio
* [:backend:`1393`] Prefill data is now validated against tampering if marked as "readonly"
* [:backend:`1399`] Fixed KVK (prefill) integration by fetching the "basisprofiel" information
* [:backend:`1410`] Fixed admin session not being recognized by SDK/API for demo auth plugins
* [:backend:`840`] Fixed hijack functionality in combination with 2FA

  - Hijack and enforced 2FA can now be used together (again)
  - Hijacking and releasing users is now logged in the audit log

* [:backend:`1408`] Hardened TimelineLogProxy against disappeared content object

New features/improvements
-------------------------

* [:backend:`1336`] Defined and implemented backend extension mechanism
* [:backend:`1378`] Hidden components are now easily identifiable in the form builder
* [:backend:`940`] added option to display 'back to main website' link
* [:backend:`1103`] Plugin options can now be managed from a friendly user interface in the
  global configuration page
* [:backend:`1391`] Added option to hide the fieldset header
* [:backend:`988`] implemented permanently deleting forms after soft-delete
* [:backend:`949`] Redesigned/styled the confirmation/summary PDF - this now applies the
  configured organization theming

Project maintenance
-------------------

* [:backend:`478`] Published django-digid-eherkenning to PyPI and replaced the Github dependency.
* [:backend:`1381`] added targeted elasticapm instrumentation to get better insights in
  performance bottlenecks
* Cleaned up admin overrides CSS in preparation for dark-theme support
* [:backend:`1403`] Removed the legacy formio formatting feature flag and behaviour

1.0.0-rc.4 (2022-02-25)
=======================

Release candidate 4.

A couple of fixes in the previous release candidates broke new things, and thanks to
the extensive testing some more issues were discovered.

Bugfixes
--------

* [:backend:`1337`] Made the component key for form fields required
* [:backend:`1348`] Fixed restoring a form with multiple steps/logics attached
* [:backend:`1349`] Fixed missing admin-index menu in import form and password change template
* [:backend:`1368`] Updated translations
* [:backend:`1371`] Fixed Digid login by upgrading django-digid-eherkenning package

New features
------------

* [:backend:`1264`] Set up and documented the Open Forms versioning policy
* [:backend:`1348`] Improved interface for form version history/restore
* [:backend:`1363`] User uploads as registration email attachments is now configurable
* [:backend:`1367`] Implemented hashing identifying attributes when they are not actively used

Project maintenance
-------------------

* Ignore some management commands for coverage
* Add (local development) install instruction
* Open redirect is fixed in cookie-consent, our monkeypatch is no longer needed
* Further automation to bundling the correct SDK release in the Open Forms image
  This simplifies deployment quite a bit.
* [:backend:`1301`] Extensive testing of a new approach to display the submitted data, still opt-in.
* Add more specific Formio component type hints

1.0.0-rc.3 (2022-02-16)
=======================

Release candidate 2 had some more bugfixes.

* [:backend:`1254`] Fixed columns component to not depend on bootstrap
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

* [:backend:`1207`] Fixed excessive remote service calls in prefill machinery
* [:backend:`1255`] Fixed warnings being displayed incorrectly while form editing
* [:backend:`944`] Display submission authentication information in logevent logging
* [:backend:`1275`] Added additional warnings in the form designer for components requiring
  authentication
* [:backend:`1278`] Fixed Haal Centraal prefill according to spec
* [:backend:`1269`] Added SESSION_EXPIRE_AT_BROWSER_CLOSE configuration option
* [:backend:`807`] Implemented a strict Content Security Policy

    - allow script/style assets from own source
    - allow script/style assets from SDK base url
    - allow a limited number of inline script/style via nonce

* Allow for configurable DigiD XML signing
* [:backend:`1288`] Fixed invalid map component markup
* Update the NUM_PROXIES configuration option default value to protect against
  X-Forwarded-For header spoofing
* [:backend:`1285`] Remove the multiple option from signature component
* Handle KvK non-unique API roots
* [:backend:`1127`] Added ``clearOnHide`` configuration option for hidden fields
* [:backend:`1222`] Fixed visual state when deleting logic rules
* [:backend:`1273`] Fixed various logs to be readonly (even for superusers)
* [:backend:`1280`] Fixed reusable definition handling when copying form
* [:backend:`1099`] Fixed rendering submission data when duplicate labels exist (PDF, confirmation email)
* [:backend:`1193`] Fixed file upload component/handling

    - configured and documented webserver upload size limit
    - ensured file uploads are not attached to emails but are instead downloadable from
      the backend. A staff account is required for this.
    - ensured individually configured component file size limits are enforced
    - ensured file uploads are deleted from the storage when submission data is pruned/
      stripped from sensitive data

* [:backend:`1272`] Hardened XML submission export to handle multiple values
* [:backend:`1299`] Updated to celery 5
* [:backend:`1216`] Fixed retrieving deleted forms in the API
* Fixed docker-compose with correct non-privileged nginx SDK port numbers
* [:backend:`1251`] Fixed container file system polution when using self-signed certificates
* Fixed leaking of Form processing configuration
* [:backend:`1199`] Handle possible OIDC duplicate user email problems
* [:backend:`1018`] WCAG added title attribute to header logo
* [:backend:`1330`] Fixed dealing with component/field configuration changes when they are used
  in logic
* [:backend:`1296`] Refactor warning component
* Bumped to Django 3.2 (LTS) and update third party packages

New features
------------

* [:backend:`1291`] Privacy policy link in footer is now configurable

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
* [:backend:`1243`] Fixed an admin bug that made form definitions crash
* [:backend:`1206`] Fixed StUF-BG configuration check to allow empty responses
* [:backend:`1208`] Fixed exports to use dynamic file upload URLs
* [:backend:`1247`] Updated admin menu structure to fit on screens (1080 pixels height) again
* [:backend:`1237`] Updated admin version info to show proper version
* [:backend:`1227`] Removed option to allow multiple options in selectboxes
* [:backend:`1225`] Updated admin formbuilder: Moved some fields to a new catagory
* [:backend:`1123`] Updated admin formbuilder: Fieldset now has a logic tab
* [:backend:`1212`] Updated prefilling to be more graceful
* [:backend:`986`] Fixed form definitons to handle unique URLs better
* [:backend:`1217`] Fixed import with duplicate form slug
* [:backend:`1168`] Fixed import with "form specific email" option enabled
* [:backend:`1214`] Fixed eIDAS ID storage field
* [:backend:`1213`] Added prefill tab to date field
* [:backend:`1019`] Added placeholder for text field
* [:backend:`1083`] Avoid checking logic on old data


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
