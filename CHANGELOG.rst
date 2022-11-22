=========
Changelog
=========

2.0.1 (2022-11-23)
==================

First maintenance release of the 2.0 series.

This patch fixes a couple of bugs encountered when upgrading from 1.1 to 2.0.

**Bugfixes**

* [#2301] Fixed identifying attributes still being hashed after a submission is resumed
* [#2135] Fixed submission step data being cascade deleted in certain edge cases
* [#2219] A fix was also attempted for bad CSS unit usage in confirmation e-mails, but
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
* [#1877] Registration e-mail subject is now configurable
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
* [#1787] You can now configure the "form pause" e-mail template to use
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
* [#2154] Fixed coloured links e-mail rendering crash
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
* [#1871] Ensure that fields hidden in frontend don't end up in registration e-mails

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
