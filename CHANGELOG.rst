=========
Changelog
=========

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

**Upgrade preprations**

The following additions are required to prepare upgrading to 2.0.0. Please see the
release notes of 2.0.0 on how to use them.

* [#2055] Added management command to check for invalid keys
* [#1979] Added model to track currently deployed version

.. note:: This is the FINAL 1.0.x release - support for this version has now ended. We
   recommend upgrading to 2.0.x.

1.0.13 (2022-08-09)
===================

Security fix release

This release fixes a potential reflected file download vulnerability.

* Bumped Django and django-sendfile2 versions with fixes for CVE-2022-36359
* Fixed the filename of submission attachment file downloads
* [#1833] Fixed submission being blocked on empty prefill data

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

1.0.10 (2022-06-16)
===================

Hotfix following 1.0.9

The patch validating uploaded file content types did not anticipate the explicit
wildcard configuration option in Formio to allow all file types. This caused files
uploaded by end-users to not be attached to the submission.

We've fixed the wildcard behaviour, but you should check your instances for incomplete
data. This involves a couple of steps with some pointers below.

1. The temporary uploads are automatically removed by the cronjobs at 3:30 UTC. The
   default setting is to do this after 2 days (48 hours). We have provided an example
   `management command <https://github.com/open-formulieren/open-forms/blob/issue/recover-missing-submission-attachments/src/openforms/utils/management/commands/check_restore_needed.py>`_ that you can use to check if you need to partially
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

1.0.9 (2022-06-13)
==================

Security release (CVE-2022-31040, CVE-2022-31041)

This bugfix release fixes two security issues in Open Forms. We recommend upgrading
as soon as possible.

* [CVE-2022-31040] Fixed open redirect in cookie-consent 'close' button
* [CVE-2022-31041] Perform upload content validation against allowed file types
* [#1670] Update error message for number validation
* [#1560] Fix prefill not working inside of nested/layout components

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
* [#1550] Fixed form desinger partial crash when adding a currency/number component
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
* Fixed bug in e-mail registration backend when using new formio formatters
* [#1293, #1179] "signature" components are now proper images in PDF/confirmation e-mail
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
* [#1363] User uploads as registration e-mail attachments is now configurable
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
