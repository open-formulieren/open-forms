=========
Changelog
=========

1.1.0-rc.0 (2022-05-XX)
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
  to generate the confirmation e-mails, PDFs, registration e-mails, exports...

  - You can now specify whether a component should be displayed in different modes
    (PDF, summary, confirmation e-mail)
  - Implemented sane defaults for configuration options
  - PDF / Confirmation e-mails / registration e-mails now have more structure,
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
* Improved development views to view how confirmation e-mails/PDFs will be rendered
* Refactor submission models
* Refactor form serializers file
* Moved some generic OIDC functionality to mozilla-django-oidc-db
* [#1366] default to allow CORS with docker-compose
* Remove SDK from docker-compose
* Add SMTP container to docker-compose stack for outgoing e-mails
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
