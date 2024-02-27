=========
Changelog
=========

2.2.10 (2024-02-27)
==================

Final release in the 2.2.x series.

* [#3863] Fixed the generated XML for StUF-BG requests when retrieving partners/children.
* [#3858] Fixed a race condition that would manifest during parallel file uploads,
  leading to permission errors.

2.2.9 (2024-02-06)
==================

Bugfix release

This release addresses a security weakness. We believe there was no way to actually
exploit it.

* [CVE-2024-24771] Fixed (non-exploitable) multi-factor authentication weakness.
* [SDK#642] Fixed DigiD error message via SDK patch release.
* Upgraded dependencies to their latest available security releases.

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

2.2.6 (2023-11-09)
==================

Hotfix release

* Upgraded bundled SDK version
* [#3580] Fixed incorrect attributes being sent in ZWG registration backend when
  creating the rol/betrokkene.

2.2.5 (2023-10-30)
==================

* [#3279] Added robustness to the admin that retrieves data from external APIs.
* Bumped dependencies to their latest security fixes.

2.2.4 (2023-09-29)
==================

Hotfix for WebKit based browsers

* [#3511] Fixed user input "flickering" in forms with certain (backend) logic on Safari
  & other WebKit based browsers (via SDK patch).

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

2.2.2 (2023-08-24)
==================

Periodic bugfix release

* [#3319] Fixed forms possibly sending a DigiD SAML request without assurance level due
  to misconfiguration.
* [#3358] Fixed display of appointment time in correct timezone.
* [#3368] Fixed a crash when empty values are returned from StUF-BG.
* Fixed JQ documentation URL for sorting.

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
