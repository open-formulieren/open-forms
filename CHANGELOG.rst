=========
Changelog
=========

.. note::

    The Dutch version of this changelog can be found :ref:`here <changelog-nl>`.

3.1.5 (2025-07-11)
==================

Regular bugfix release.

* [:backend:`5454`] Fixed crash when saving DigiD or eHerkenning configuration in the admin.
* [:backend:`5413`] Fixed uploading files with soft-hyphens not passing form validation.

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

3.1.3 (2025-06-06)
==================

Hotfix addressing a backport issue.

* [:backend:`5193`] Fixed missing backport of the zgw-consumers upgrade, causing a crash
  when editing services.
* [:backend:`5303`] Fixed user defined variables jumping around because of the auto-sort.
* Upgraded Django to the latest security release.


3.1.2 (2025-05-23)
==================

Regular bugfix release.

**Bugfixes**

* [:backend:`5289`] Fixed crash in fix-script.
* [:backend:`4933`] Fixed missing Cosign v2 information for registraton email templates.

**Project maintenance**

* Upgraded django to 4.2.21 with the latest security patches.


3.1.1 (2025-04-16)
===================

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

2.7.11 (2025-01-09)
===================

Final bugfix release in the ``2.7.x`` series.

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

2.7.10 (2024-11-25)
===================

Periodic bugfix release

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

* [:backend:`4732`] Fixed CSP issues for Expoints/other analytics.
* [:backend:`4745`] Fixed missing registration variable for the Objects API plugin.
* [:backend:`4810`] Fixed uppercase selectboxes options being lowercased if the component is
  in a step that's being skipped. See the instructions below on how to patch existing forms.
* [:backend:`4823`] Fixed uploading files with leading or trailing whitespace in the
  filename.
* [:backend:`4727`] Fixed a crash in the form designer UI when a user defined variable was
  changed to an array datatype.

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

2.7.9 (2024-10-29)
==================

Periodic bugfix release

* [:backend:`4695`] Fixed a performance issue during legacy Objects API registration
  plugin validation.
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

2.6.15 (2024-10-08)
===================

Final bugfix release in the ``2.6.x`` series.

* [#4602] Fixed missing Dutch translation for minimum required checked items error
  message in the selectboxes component.
* [#4658] Fixed certain variants of ZIP files not passing validation on Windows.
* [#4652] Fixed misaligned validation errors in the form designer UI.

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

2.7.8 (2024-09-23)
==================

Hotfix for 2.7.7 issue

.. warning::

    If you updated to 2.7.7 before, please update to 2.7.8 and then run the
    ``/app/bin/fix_globalconfig_zip.py`` script to fix the misconfiguration.

    If you update from a version older than 2.7.7, you don't need to run this script.

* [:backend:`4658`] Fixed missing global configuration update, causing runtime crashes
  when ZIP files are enabled in the global configuration.

2.5.13 addendum (2024-09-24)
============================

2.5.13 was the final bugfix release in the ``2.5.x`` series.

Since then, no bugfixes become available to release. This version is now no longer
supported.

2.7.7 (2024-09-23)
==================

Periodic bugfix release

* [:backend:`4653`] Fixed the missing paragraph/headings style options in WYSIWYG
  editors.
* [:backend:`4602`] Fixed missing Dutch translation for minimum required checked items
  error message in the selectboxes component.
* [:backend:`4680`] Fixed a crash that can occur with certain Formio broken
  configurations when upgrading from 2.6 to 2.7.
* [:backend:`4656`] Fixed a crash during validation when you have file upload components
  inside repeating groups.
* [:backend:`4658`] Fixed certain variants of ZIP files not passing validation on
  Windows.
* [:backend:`4652`] Fixed misaligned validation errors in the form designer UI.
* Fixed a misconfiguration for automated end-to-end testing in CI.

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

2.7.6 (2024-09-05)
==================

Hotfix release.

* [:backend:`4627`] The previous patch was incomplete, fixed another crash that would
  occur if no ActingSubjectID is present.

2.7.5 (2024-09-02)
==================

Periodic bugfix release

* Applied the latest security patches for dependencies.
* [:backend:`4380`] Added missing ability to store payment provider payment ID references.
* [:backend:`4597`] Revert message for not-filled-in-fields in confirmation PDF back to
  just empty space.
* Fixed processing of empty file upload components in the Objects API registration plugin.
* Fixed an upgrade check incorrectly reporting problems.
* [:backend:`4627`] Fixed a crash in the eHerkenning-via-OIDC plugin if no ActingSubjectID
  claim is present.

2.6.14 (2024-09-02)
===================

Periodic bugfix release

* [:backend:`4597`] Revert message for not-filled-in-fields in confirmation PDF back to
  just empty space.
* Fixed processing of empty file upload components in the Objects API registration plugin.

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

2.7.4 (2024-08-06)
==================

Fixed a crash in upgrade check script and set up CI to prevent these problems in the
future.

2.7.3 (2024-08-05)
==================

Fixed a typo in upgrade check script name.

2.7.2 (2024-08-05)
==================

Fixed a build error where some upgrade check scripts were not included in the Docker
image.


2.7.1 (2024-07-29)
==================

First bugfix release for 2.7.x.

* [:backend:`4533`] Fixed Objects API registration options checkboxes not toggling.
* [:backend:`4516`] Fixed imports (and error feedback) of legacy exports with Objects
  API registration backends. It should now be more clear that admins possibly need to
  check the Objects API groups configuration.
* [:backend:`4191`] Fixed the datatype of ``vestiging`` field in ZGW registration
  rollen/betrokkenen.
* [:backend:`4334`] Fixed the email registration plugin not sending a payment-received
  email when "wait for payment to register" is enabled. This behaviour is to ensure that
  financial departments can always be informed of payment administration.
* [:backend:`4502`] Fixed a problem where the registration-backend routing logic is not
  calculated again after pausing and resuming a submission.
* [:backend:`4560`] Fixed more PDF generation overlapping content issues. The layout no
  longer uses two columns, but just stacks the labels and answers below each other since
  a compromise was not feasible.
* [:backend:`4519`] Fixed form variable dropdowns taking up too much horizontal space.
* Backend checks of form component validation configuration are mandatory. All components
  support the same set of validation mechanism in frontend and backend.

2.6.13 (2024-07-29)
===================

Bugfix release.

* [:backend:`4191`] Fixed the datatype of ``vestiging`` field in ZGW registration
  rollen/betrokkenen.
* [:backend:`4334`] Fixed the email registration plugin not sending a payment-received
  email when "wait for payment to register" is enabled. This behaviour is to ensure that
  financial departments can always be informed of payment administration.
* [:backend:`4502`] Fixed a problem where the registration-backend routing logic is not
  calculated again after pausing and resuming a submission.
* [:backend:`4560`] Fixed more PDF generation overlapping content issues. The layout no
  longer uses two columns, but just stacks the labels and answers below each other since
  a compromise was not feasible.
* [:backend:`4519`] Fixed form variable dropdowns taking up too much horizontal space.
* Backend checks of form component validation configuration are mandatory. All
  components support the same set of validation mechanism in frontend and backend.

2.5.13 (2024-07-29)
===================

Bugfix release.

* [:backend:`4334`] Fixed the email registration plugin not sending a payment-received
  email when "wait for payment to register" is enabled. This behaviour is to ensure that
  financial departments can always be informed of payment administration.
* [:backend:`4502`] Fixed a problem where the registration-backend routing logic is not
  calculated again after pausing and resuming a submission.
* [:backend:`4560`] Fixed more PDF generation overlapping content issues. The layout no
  longer uses two columns, but just stacks the labels and answers below each other since
  a compromise was not feasible.

2.6.12 (2024-07-12)
===================

Bugfix release to address PDF generation issue.

* [:backend:`4191`] Fixed missing required ``aoaIdentificatie`` field to ZGW registration.
* [:backend:`4450`] Fixed submission PDF rows overlapping when labels wrap onto another line.
* Updated dependencies to their latest security patches.

2.5.12 (2024-07-12)
===================

Bugfix release to address PDF generation issue.

* [:backend:`4191`] Fixed missing required ``aoaIdentificatie`` field to ZGW registration.
* [:backend:`4450`] Fixed submission PDF rows overlapping when labels wrap onto another line.
* Updated dependencies to their latest security patches.

2.7.0 "Berlage" (2024-07-09)
============================

Open Forms 2.7.0 is a feature release.

.. epigraph::

   Maykin was founded in 2008 and originally located in the 'Beurs van Berlage' in
   Amsterdam. The monumental building, designed by Hendrik Petrus Berlage and build
   around 1900, inspired us to create innovative applications, of which some are still
   maintained and in production to this day.

Upgrade notes
-------------

* ⚠️ The feature flag to disable backend validation is now removed, instances relying
  on it should verify that their forms still work now that validation is enforced.

* ⚠️ If you make use of the Objects API - even the legacy configuration, you now need
  to have a valid configuration for the objecttypes API service. The plugin
  accesses this API during registration. You can configure this for each api group via
  **Admin > Overige > Objecten API-groepen** after upgrading to 2.7.

* We're consolidating the OpenID Connect *Redirect URI* endpoints into a single
  endpoint: ``/auth/oidc/callback/``. The legacy endpoints are still enabled,
  but scheduled for removal in Open Forms 3.0.

  You can opt-in to the new behaviour through three environment variables (and we
  recommend doing so on fresh instances):

  - ``USE_LEGACY_OIDC_ENDPOINTS=false``: admin login
  - ``USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS=false``: DigiD/eHerkenning plugins
  - ``USE_LEGACY_ORG_OIDC_ENDPOINTS=false``: Organization OIDC plugin

  Note that the OpenID applications need to be updated on the identity provider,
  specifically the allowed "Redirect URIs" setting needs to be updated with the
  following path replacements:

  - ``/oidc/callback/`` -> ``/auth/oidc/callback/``
  - ``/digid-oidc/callback/`` -> ``/auth/oidc/callback/``
  - ``/eherkenning-oidc/callback/`` -> ``/auth/oidc/callback/``
  - ``/digid-machtigen-oidc/callback/`` -> ``/auth/oidc/callback/``
  - ``/eherkenning-bewindvoering-oidc/callback/`` -> ``/auth/oidc/callback/``
  - ``/org-oidc/callback/`` -> ``/auth/oidc/callback/``

* We are deprecating location autofill in ``textfield`` components. Instead, use the
  ``addressNL`` component and enable address derivation.

Major features
--------------

**🛂 Mandates ("machtigen") for DigiD and eHerkenning**

We now provide better integration for DigiD Machtigen and eHerkenning Bewindvoering (
via OpenID Connect). Open Forms registers the details in which capacity a user is
logged in and whether a mandate is used or not.

This information is available during the registration of a form submission, making it
possible to register it to the Objects API and ZGW API's for further processing.

**📍 Dutch addresses**

We're making it easier to deal with Dutch addresses.

The ``addressNL`` component is meant for these - it (optionally) integrates with the
Kadaster API to derive street name and city from the provided postcode and house number,
while making sure the full address details are sent to the registration plugins.

Support for single-column layout was added so that the layout can adapt to your
organization's form design.

We're adding more flexbility to better integrate with registration plugins, so keep an
eye on this component for Open Forms 2.8.

**🚸 User experience improvements in the form designer**

Staff users typically spend a lot of time in the form designer to create or update
forms. We're making some changes to improve the user experience so that it becomes
easier to:

* configure forms, and make configuration less error-prone with better UI elements
* export and import forms across environments (staging -> production, for example)
* detect problems and configuration issues

Detailed changes
----------------

**New features**

* Submission registration improvements:

    - Objects API's:

        * [:backend:`4031`] Added a warning when switching back to the legacy configuration.
        * [:backend:`4041`] Improved robustness of document registration.
        * [:backend:`4267`] Add support for multiple Documents API's.
        * [:backend:`4323`] Added envvar/setting to disable sending hidden fields to
          Objects API. This is a temporary workaround - the proper solution is to update
          your object type definitions.
        * Added missing ``public_reference`` registration variable.
        * [:backend:`4475`] Added submission UUID and language code static variables.
        * [:backend:`4416`] The ``ontvangstdatum`` attribute is now set for uploaded
          documents.

    - ZGW API's

        * [:backend:`4337`] The form name is now used as ``omschrijving`` of the created
          zaak.
        * [:backend:`4414`] Simplified ZGW API options configuration - there is no
          default config anymore, you must explicitly select one.
        * [:backend:`4416`] The ``ontvangstdatum`` attribute is now set for uploaded
          documents.

    - [:backend:`4267`] Improve UX of Objects API and ZGW API's configuration. More will
      come in Open Forms 2.8.

* Authentication plugins:

    - [:backend:`4246`] Reworked the OpenID Connect integration:

        * Claims with a ``.`` character are now supported.
        * Added configuration options to extract more metadata about the authentication.
        * Defined a formal schema for authentication context data
        * Updated DigiD/eHerkenning plugin flavours to store additional information,
          such as level of assurance, representee/authorizee, mandate context...
        * Added static variables to access/register the authentication context in
          submissions.
        * [:backend:`3967`] Company branch number is now recorded for eHerkenning via
          OpenID.

* DMN plugins:

    - [:backend:`4269`, :backend:`4278`] Improved Camunda DMN engine integration:

        * The UI now shows the input variables, even from complex expressions.
        * DMN tables that depend on other tables now don't show intermediate input
          variables that are already automatically provided.
        * Added overview table for all the expected input expressions.
        * Added automatic problem detection.
        * Selecting another decision definition now resets the input and output mapping.
        * You can now map static form variables to DMN input variables.

* [:backend:`72`] All supported components are now covered in the backend validation.
  Support is added for: time, selectboxes, textarea, postcode, bsn, select, checkbox,
  currency, signature, map, cosign, password, iban, file, datetime, addressNL and
  licenseplate components.
* [:backend:`4009`] Improved the representation of submission data in the admin interface.
* [:backend:`4005`] Added the ability to search submission reports by public registration
  reference and submission in the admin.
* [:backend:`4005`] The title of the submission PDF now includes the public registration
  reference.
* [:backend:`3725`] The admin email digest now detects and reports more problems.
* [:backend:`3889`] You can now export the audit trails and GDPR log entries.
* [:backend:`3889`] Viewing an outgoing request log entry in the admin will now create a
  GDPR log entry.
* [:backend:`4101`] The "Show form" button in the admin is now only displayed for active forms.
* [:backend:`4080`] Added generation timestamp to PDF submission report.
* [:backend:`4215`] Email logs older than 90 days are now periodically deleted.
* [:backend:`4229`] Improved performance of KVK number validation.
* Optimized performance of the appointment information admin page and added search support.
* Removed the feature flag to disable backend validation.
* [:backend:`4277`] You can now upload a (separate) logo image file to be used in emails.
* [:backend:`3807`] You can now configure the template for the co-sign request email.
* [:backend:`4347`] When Organization login is enabled, the username/password fields are
  initially collapsed.
* [:backend:`4356`] Added support for the Expoints feedback tool.
* [:backend:`4377`] Added support for token-exchange extension to BRK client.
* [:backend:`3993`] The ``addressNL`` component now supports autofill of street and city
  for entered postcode and house number.
* [:backend:`4423`] You can now specify a layout (single or double column) for the
  ``addressNL`` component.

**Bugfixes**

* [:backend:`3969`] Removed the level of assurance override for eHerkenning/eIDAS
  authentication. In its existing form it was not supported by brokers, but it will be
  re-introduced in another form in the future.
* Fixed more backend validation issues:

    - [:backend:`4065`] Hidden fields/components are not longer taken into account
      during backend validation.
    - [:backend:`4068`] Fixed various backend validation issues:

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

    - [:backend:`4126`] Fixed incorrect validation of components inside repeating groups
      that are conditionally visible (with frontend logic).
    - [:backend:`4143`] Added additional backend validation: now when form step data is
      being saved (including pausing a form), the values are validated against the
      component configuration too.
    - [:backend:`4151`] Fixed backend validation error being triggered for
      radio/select/selectboxes components that get their values/options from another
      variable.
    - [:backend:`4172`] Fixed a crash while running input validation on date fields
      when min/max date validations are specified.
    - [DH#671] Fixed conditionally making components required/optional via backend logic.
    - Fixed validation of empty/optional select components.
    - [:backend:`4096`] Fixed validation of hidden (with ``clearOnHide: false``) radio
      components.
    - [DH#667] Fixed components inside a repeating group causing validation issues when
      they are nested inside a fieldset or columns.
    - [:backend:`4241`] Fixed some backend validation being skipped when there is
      component key overlap with layout components (like fieldsets and columns).

* [:backend:`4069`] Fixed a crash in the form designer when navigating to the variables
  tab if you use any of the following registration backends: email, MS Graph
  (OneDrive/Sharepoint) or StUF-ZDS.
* [:backend:`4061`] Fixed not all form components being visible in the form builder when
  other components can be selected.
* [:backend:`4079`] Fixed metadata retrieval for DigiD failure when certificates signed
  by the G1 root are used.
* [:backend:`4099`] Fixed a crash in the form designer when editing (user defined)
  variables and the template-based Objects API registration backend is configured.
* [:backend:`4103`] Fixed incorrect appointment details being included in the submission
  PDF.
* [:backend:`4073`] Removed unused StUF-ZDS 'gemeentecode'.
* [:backend:`4015`] Fixed possible traversal attack in service fetch service.
* [:backend:`4084`] Fixed default values of select components set to multiple.
* [:backend:`4134`] Fixed form designer admin crashes when component/variable keys are
  edited.
* [:backend:`4131`] Fixed bug where component validators all had to be valid rather
  than at least one.
* [:backend:`4072`] Fixed recovery token flow redirecting back to login screen, making
  it impossible to use recovery tokens.
* [:backend:`4145`] Fixed the payment status not being registered correctly for StUF-ZDS.
* [:backend:`4124`] Fixed forms being shown multiple times in the admin list overview.
* [:backend:`4052`] Fixed payment (reminder) emails being sent more often than intended.
* [:backend:`4156`] Fixed the format of order references sent to payment providers. You
  can now provide your own template.
* [:backend:`4141`] Fixed a crash in the Objects API registration when using periods
  in component keys.
* [:backend:`4165`] A cookie consent group for analytics is now required.
* [:backend:`4187`] Selectboxes/radio with dynamic options are considered invalid when
  submitting the form.
* [:backend:`4202`] Fixed Objects API registration v2 crash with hidden fields.
* [:backend:`4115`] Support different kinds of GovMetric feedback (aborting the form
  vs. completing the form).
* [:backend:`4197`] Ensured all uploaded images are being resized if necessary.
* [:backend:`4191`] Added missing required ``aoaIdentificatie`` field to ZGW registration.
* [:backend:`4173`] Fixed registration backends not being included when copying a form.
* [:backend:`4146`] Fixed SOAP timeout not being used for Stuf-ZDS client.
* [:backend:`3964`] Toggling visibility with frontend logic and number/currency
  components leads to fields being emptied.
* [:backend:`4247`] Fixed migration crash because of particular key-structure with
  repeating groups.
* [:backend:`4174`] Fixed submission pre-registration being stuck in a loop when failing
  to do so.
* [:backend:`4184`] Fixed broken references to form steps when copying a form.
* [:backend:`4205`] The CSP ``form-action`` directive now allows any ``https:`` target,
  to avoid errors on eHerkenning login redirects.
* [:backend:`4158`] Added missing English translation for ``invalid_time`` custom error
  message.
* [:backend:`4302`] Made co-sign data (date and co-sign attribute) available in the
  Objects API registration.
* [:backend:`1906`] Fixed a cause of form imports sometimes creating new form definitions
  instead of linking the already existing one.
* [:backend:`4291`] Fixed logic triggers with boolean user defined variables.
* [:backend:`4199`] Fixed submissions remembering authentication context from a previous
  submission, even though the form was started without explicit login action.
* [:backend:`4255`] Fixed a performance issue in the confirmation PDF generation when large
  blocks of text are rendered.
* [:backend:`4403`] Fixed broken submission PDF layout when empty values are present.
* [:backend:`4450`] Fixed submission PDF rows overlapping.
* [:backend:`4012`] Fixed WYSIWYG editor link popup not always clearing.
* [:backend:`4368`] Fixed URLs to the same domain being broken in the WYSIWYG editors.
* [:backend:`4362`] Fixed a crash in the form designer when a textfield/textarea allows
  multiple values in forms with translations enabled.
* [:backend:`4363`] Fixed option descriptions not being translated for radio and
  selectboxes components.
* [:backend:`4338`] Fixed prefill for StUF-BG with SOAP 1.2 not properly extracting
  attributes.
* [:backend:`4379`] Fixed logout requests for OpenID Connect triggering a server error
  because of bad redirect responses.
* [:backend:`4350`] Disabled link protocol warning in WYSIWYG editors.
* [:backend:`4409`] Updated language for payment amount in submission PDF.
* [:backend:`4051`] The JSON view/editor in the form builder now has syntax highlighting.
* [:backend:`4425`] Fixed the wrong price being sent to the Objects API when multiple
  payment attempts are made.
* [:backend:`4425`] Fixed incorrectly marking failed/non-completed payment attempts as
  registered in the registration backend.
* [:backend:`4425`] Added missing (audit) logging for payments started from the
  confirmation email link.
* [:backend:`4313`] Fixed theme styling for organisation OIDC login.
* Fixed temporary file uloads not being associated with the active form submission.

**Project maintenance**

* [:backend:`4035`] Added an E2E test for the file component.
* Cleaned up logging config: removed unused performance logging config, added tools to
  mute logging.
* Cleaned up structure of local setting overrides.
* [:backend:`4057`] Upgraded to ``zgw-consumers`` 0.32.0. This drops the dependency on
  ``gemma-zds-client``.
* Vendored ``decorator-include``, as it is not maintained anymore.
* Updated dependencies to drop ``setuptools``.
* [:backend:`3878`] Updated some dependencies after the Django 4.2 upgrade.
* Switched to Docker Compose V2 in CI, as V1 was removed from Github Ubuntu images.
* Moved EOL changelog to archive.
* Ordered changelog entries by version instead of date in archive.
* Added feature to log flaky tests in CI.
* Documented versioning policy change.
* ``uv`` is now used to install dependencies in Docker build.
* Improved release process documentation.
* [:backend:`3878`] Updated docs dependencies.
* Added PR checklist template.
* [:backend:`4009`, :backend:`979`] Removed the ``get_merged_data`` of the submission model.
* [:backend:`4044`] Improved developer documentation of submission state and component configuration.
* [:backend:`3878`] Updated to the latest version of ``django-yubin``, removed the temporary patch.
* [:backend:`3878`] Updated to the latest version of ``celery``, including related dependencies.
* [:backend:`4247`] Improved robustness of the ``FormioConfigurationWrapper`` with editgrids.
* [:backend:`4236`] Removed form copy API endpoint, as it is not used anymore.
* [:backend:`4246`] Rewrote the OIDC-flow tests to be much more representative, added
  docker-compose configuration and docs to easily replicate this in a local dev environment.
* Changelog now links to the relevant (Github) issues.
* Upgraded to the latest django-cookie-consent: updated the fixtures to use natural
  keys and bundle the package Javascript instead of inlining it.
* [:backend:`4285`] Upgraded schwifty to v2024.5.3
* [:backend:`4262`] Added script for reporting invalid default values in radio component.
* Various type-annotation improvements.
* [:backend:`4341`] Upgraded to Storybook 8, added automatic visual regression tests.
* Upgraded dependencies to their latest (security) releases.
* [:backend:`4346`] Refactored feature flag management to use django-flags.
* [:backend:`598`] Added unit tests for appointments failure flows.
* Upgraded lxml and xmlsec so that binary wheels can be installed, speeding up CI and
  docker image build.
* Re-generated expired self-signed certificates for test suite.
* Squased migrations again for the release, removed earlier squashed migrations.
* Removed some sources of test flakiness in CI.
* Updated release issue template to mention all VCR tests to re-record.
* The docker-compose for Open Zaak and Objects/Objecttypes API's now load the fixtures
  automatically, and use the latest available versions.

2.6.11 (2024-06-20)
===================

Hotfix for payment integration in Objects API

* [:backend:`4425`] Fixed the wrong price being sent to the Objects API when multiple payment
  attempts are made.
* [:backend:`4425`] Fixed incorrectly marking failed/non-completed payment attempts as registered
  in the registration backend.
* [:backend:`4425`] Added missing (audit) logging for payments started from the confirmation
  email link.

2.5.11 (2024-06-20)
===================

Hotfix for payment integration in Objects API

* [:backend:`4425`] Fixed the wrong price being sent to the Objects API when multiple payment
  attempts are made.
* [:backend:`4425`] Fixed incorrectly marking failed/non-completed payment attempts as registered
  in the registration backend.
* [:backend:`4425`] Added missing (audit) logging for payments started from the confirmation
  email link.

2.6.10 (2024-06-19)
===================

Hotfix fixing a regression in the PDF generation.

* [:backend:`4403`] Fixed broken submission PDF layout when empty values are present.
* [:backend:`4409`] Updated language used for payment amount in submission PDF.

2.5.10 (2024-06-19)
===================

Hotfix fixing a regression in the PDF generation.

* [:backend:`4403`] Fixed broken submission PDF layout when empty values are present.
* [:backend:`4409`] Updated language used for payment amount in submission PDF.

2.6.9 (2024-06-14)
==================

Bugfix release fixing some issues (still) in 2.6.8

* [:backend:`4338`] Fixed prefill for StUF-BG with SOAP 1.2 not properly extracting attributes.
* [:backend:`4390`] Fixed regression introduced by #4368 that would break template variables in
  hyperlinks inside WYSIWYG content.

2.6.8 (2024-06-14)
==================

Bugfix release

* [:backend:`4255`] Fixed a performance issue in the confirmation PDF generation when large
  blocks of text are rendered.
* [:backend:`4241`] Fixed some backend validation being skipped when there is component key
  overlap with layout components (like fieldsets and columns).
* [:backend:`4368`] Fixed URLs to the same domain being broken in the WYSIWYG editors.
* [:backend:`4377`] Added support for pre-request context/extensions in BRK client
  implementation.
* [:backend:`4363`] Fixed option descriptions not being translated for radio and selectboxes
  components.
* [:backend:`4362`] Fixed a crash in the form designer when a textfield/textarea allows multiple
  values in forms with translations enabled.

2.5.9 (2024-06-14)
==================

Bugfix release fixing some issues (still) in 2.5.8

Note that 2.5.8 was never published to Docker Hub.

* [:backend:`4338`] Fixed prefill for StUF-BG with SOAP 1.2 not properly extracting attributes.
* [:backend:`4390`] Fixed regression introduced by #4368 that would break template variables in
  hyperlinks inside WYSIWYG content.

2.5.8 (2024-06-14)
==================

Bugfix release

* [:backend:`4255`] Fixed a performance issue in the confirmation PDF generation when large
  blocks of text are rendered.
* [:backend:`4368`] Fixed URLs to the same domain being broken in the WYSIWYG editors.
* [:backend:`4362`] Fixed a crash in the form designer when a textfield/textarea allows multiple
  values in forms with translations enabled.

2.6.7 (2024-05-22)
==================

Bugfix release

* [:backend:`3807`] Made the co-sign request email template configurable.
* [:backend:`4302`] Made co-sign data (date and co-sign attribute) available in the Objects API registration.

2.6.6 (2024-05-13)
==================

Bugfix release

* [:backend:`4146`] Fixed SOAP timeout not being used for Stuf-ZDS client.
* [:backend:`4205`] The CSP ``form-action`` directive now allows any ``https:`` target,
  to avoid errors on eHerkenning login redirects.
* [:backend:`4269`] Fixed DMN integration for real-world decision definitions.

2.5.7 (2024-05-13)
==================

Bugfix release

* [:backend:`4052`] Fixed payment (reminder) emails being sent more often than intended.
* [:backend:`4124`] Fixed forms being shown multiple times in the admin list overview.
* [:backend:`3964`] Toggling visibility with frontend logic and number/currency components leads to fields being emptied.
* [:backend:`4205`] The CSP ``form-action`` directive now allows any ``https:`` target,
  to avoid errors on eHerkenning login redirects.

2.7.0-alpha.0 (2024-05-06)
==========================

This is an alpha release, meaning it is not finished yet or suitable for production use.

Detailed changes
----------------

**New features**

* Improved backend validation robustness, mainly by validating new components:

   - [:backend:`72`] Improved validation for the following components: time, selectboxes, textarea, postcode, bsn, select, checkbox,
     currency, signature, map, cosign, password, iban and licenseplate.


* Submission registration:

   - [:backend:`4031`] Added a warning for the Objects API registration configuration when switching back to the legacy configuration.
   - [:backend:`4041`] Improved robustness of document registration in the Documents API.

Other features:

* [:backend:`3969`] For eHerkenning/eIDAS authentication, the level of assurance can no longer be overridden (as brokers do not support this).
* [:backend:`4009`] Improved the representation of submission data in the admin interface.
* [:backend:`4005`] Added the ability to search submission reports by public registration reference and submission in the admin.
* [:backend:`4005`] Updated title of the PDF submission report to include the public registration reference.
* [:backend:`3725`] Expanded email digest by detecting more problems in features actively used, such as:

   - Submissions with failed registration status.
   - Prefill plugins failures.
   - Missing or wrong BRK client configuration.
   - Address autofill (based on postal code and house numer) misconfiguration.
   - Form logic rules referring to non-existent fields.
   - Invalid registration backends configuration.
   - ZGW services: Mutual TLS certificates/certificate pairs and (nearly) expired certificates.

* [:backend:`3889`] You can now export the audit trails and GDPR log entries.
* [:backend:`3889`] Viewing an outgoing request log entry in the admin will now create a GDPR log entry.
* [:backend:`4101`] The "Show form" button in the admin is now only displayed for active forms.
* [:backend:`4080`] Added generation timestamp to PDF submission report.
* [:backend:`4215`] Email logs older than 90 days are now periodically deleted.
* [:backend:`4229`] Improved performance of KVK number validation.

**Bugfixes**

* Fixed more backend validation issues:

   - [:backend:`4065`] Hidden fields/components are not longer taken into account during backend validation.
   - [:backend:`4068`] Fixed various backend validation issues:

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

   - [:backend:`4126`] Fixed incorrect validation of components inside repeating groups that are
     conditionally visible (with frontend logic).
   - [:backend:`4143`] Added additional backend validation: now when form step data is being saved
     (including pausing a form), the values are validated against the component
     configuration too.
   - [:backend:`4151`] Fixed backend validation error being triggered for radio/select/selectboxes
     components that get their values/options from another variable.
   - [:backend:`4172`] Fixed a crash while running input validation on date fields when min/max date
     validations are specified.
   - [DH#671] Fixed conditionally making components required/optional via backend logic.
   - Fixed validation of empty/optional select components.
   - [:backend:`4096`] Fixed validation of hidden (with ``clearOnHide: false``) radio components.
   - [DH#667] Fixed components inside a repeating group causing validation issues when
     they are nested inside a fieldset or columns.



* [:backend:`4069`] Fixed a crash in the form designer when navigating to the variables tab if you
  use any of the following registration backends: email, MS Graph (OneDrive/Sharepoint)
  or StUF-ZDS.
* [:backend:`4061`] Fixed not all form components being visible in the form builder when other
  components can be selected.
* [:backend:`4079`] Fixed metadata retrieval for DigiD failing when certificates signed by the G1
  root are used.
* [:backend:`4099`] Fixed a crash in the form designer when editing (user defined) variables and
  the template-based Objects API registration backend is configured.
* [:backend:`4103`] Fixed incorrect appointment details being included in the submission PDF.
* [:backend:`4073`] Removed unused StUF-ZDS 'gemeentecode'.
* [:backend:`4015`] Fixed possible traversal attack in service fetch service.
* [:backend:`4084`] Fixed default values of select components set to multiple.
* [:backend:`4134`] Fixed form designer admin crashes when component/variable keys are edited.
* [:backend:`4131`] Fixed bug where component validators all had to be valid rather than at least
  one.
* [:backend:`4072`] Fixed recovery token flow redirecting back to login screen, making it impossible to use recovery tokens.
* [:backend:`4145`] Fixed the payment status not being registered correctly for StUF-ZDS.
* [:backend:`4124`] Fixed forms being shown multiple times in the admin list overview.
* [:backend:`4052`] Fixed payment (reminder) emails being sent more often than intended.
* [:backend:`4156`] Fixed the format of order references sent to payment providers. You can now
  provide your own template.
* [:backend:`4141`] Fixed a crash in the Objects API registration when using periods in component
  keys.
* [:backend:`4165`] A cookie consent group for analytics is now required.
* [:backend:`4187`] Selectboxes/radio with dynamic options are considered invalid when submitting the form.
* [:backend:`4202`] Fixed Objects API registration v2 crash with hidden fields.
* [:backend:`4115`] Support different kinds of GovMetric feedback (aborting the form vs. completing the form).
* [:backend:`4197`] Ensured all uploaded images are being resized if necessary.
* [:backend:`4191`] Added missing required ``aoaIdentificatie`` field to ZGW registration.
* [:backend:`4173`] Fixed registration backends not being included when copying a form.
* [:backend:`4146`] Fixed SOAP timeout not being used for Stuf-ZDS client.
* [:backend:`3964`] Toggling visibility with frontend logic and number/currency components leads to fields being emptied.
* [:backend:`4247`] Fixed migration crash because of particular key-structure with repeating groups.
* [:backend:`4174`] Fixed submission pre-registration being stuck in a loop when failing to do so.

**Project maintenance**

* [:backend:`4035`] Added an E2E test for the file component.
* Cleaned up logging config: removed unused performance logging config, added tools to mute logging.
* Cleaned up structure of local setting overrides.
* [:backend:`4057`] Upgraded to ``zgw-consumers`` 0.32.0. This drops the dependency on ``gemma-zds-client``.
* Vendored ``decorator-include``, as it is not maintained anymore.
* Updated dependencies to drop ``setuptools``.
* [:backend:`3878`] Updated some dependencies after the Django 4.2 upgrade.
* Switched to Docker Compose V2 in CI, as V1 was removed from Github Ubuntu images.
* Moved EOL changelog to archive.
* Ordered changelog entries by version instead of date in archive.
* Added feature to log flaky tests in CI.
* Documented versioning policy change.
* Used ``uv`` to install dependencies in Docker build.
* Improved release process documentation.
* [:backend:`3878`] Updated docs dependencies.
* Added PR checklist template.
* [:backend:`4009`, :backend:`979`] Removed the ``get_merged_data`` of the submission model.
* [:backend:`4044`] Improved developer documentation of submission state and component configuration.
* [:backend:`3878`] Updated to the latest version of ``django-yubin``, removed the temporary patch.
* [:backend:`3878`] Updated to the latest version of ``celery``, including related dependencies.
* [:backend:`4247`] Improved robustness of the ``FormioConfigurationWrapper`` with editgrids.
* [:backend:`4236`] Removed form copy API endpoint, as it is not used anymore.

2.6.5 (2024-04-24)
==================

Bugfix release

* [:backend:`4165`] A cookie consent group for analytics is now required.
* [:backend:`4115`] Added new source ID and secure GUID.
* [:backend:`4202`] Fixed Objects API registration v2 crash with hidden fields.

2.6.5-beta.0 (2024-04-17)
=========================

Bugfix beta release

* [:backend:`4186`] Fix for "client-side logic" in the formio-builder cleared existing values.
* [:backend:`4187`] Selectboxes/radio with dynamic options are considered invalid when submitting the form.
* [:backend:`3964`] Toggling visibility with frontend logic and number/currency components leads to fields being emptied.

2.6.4 (2024-04-16)
==================

Bugfix release

* [:backend:`4151`] Fixed backend validation error being triggered for radio/select/selectboxes
  components that get their values/options from another variable.
* [:backend:`4052`] Fixed payment (reminder) emails being sent more often than intended.
* [:backend:`4124`] Fixed forms being shown multiple times in the admin list overview.
* [:backend:`4156`] Fixed the format of order references sent to payment providers. You can now
  provide your own template.
* Fixed some bugs in the form builder:

    - Added missing error message codes (for translations) for the selectboxes component.
    - Fixed the "client-side logic" to take the correct data type into account.
    - Fixed the validation tab not being marked as invalid in some validation error
      situations.

* Upgraded some dependencies with their latest (security) patches.
* [:backend:`4172`] Fixed a crash while running input validation on date fields when min/max date
  validations are specified.
* [:backend:`4141`] Fixed a crash in the Objects API registration when using periods in component
  keys.

2.6.3 (2024-04-10)
==================

Bugfix release following feedback on 2.6.2

* [:backend:`4126`] Fixed incorrect validation of components inside repeating groups that are
  conditionally visible (with frontend logic).
* [:backend:`4134`] Fixed form designer admin crashes when component/variable keys are edited.
* [:backend:`4131`] Fixed bug where component validators all had to be valid rather than at least
  one.
* [:backend:`4140`] Added deploy configuration parameter to not send hidden field values to the
  Objects API during registration, restoring the old behaviour. Note that this is a
  workaround and the correct behaviour (see ticket #3890) will be enforced from Open
  Forms 2.7.0 and newer.
* [:backend:`4072`] Fixed not being able to enter an MFA recovery token.
* [:backend:`4143`] Added additional backend validation: now when form step data is being saved (
  including pausing a form), the values are validated against the component
  configuration too.
* [:backend:`4145`] Fixed the payment status not being registered correctly for StUF-ZDS.

2.5.6 (2024-04-10)
==================

Hotfix release for StUF-ZDS users.

* [:backend:`4145`] Fixed the payment status not being registered correctly for StUF-ZDS.

2.6.2 (2024-04-05)
==================

Bugfix release - not all issues were fixed in 2.6.1.

* Fixed various more mismatches between frontend and backend input validation:

    - [DH#671] Fixed conditionally making components required/optional via backend logic.
    - Fixed validation of empty/optional select components.
    - [:backend:`4096`] Fixed validation of hidden (with ``clearOnHide: false``) radio components.
    - [DH#667] Fixed components inside a repeating group causing validation issues when
      they are nested inside a fieldset or columns.

* [:backend:`4061`] Fixed not all form components being visible in the form builder when other
  components can be selected.
* [:backend:`4079`] Fixed metadata retrieval for DigiD failing when certificates signed by the G1
  root are used.
* [:backend:`4103`] Fixed incorrect appointment details being included in the submission PDF.
* [:backend:`4099`] Fixed a crash in the form designer when editing (user defined) variables and
  the template-based Objects API registration backend is configured.
* Update image processing library with latest security fixes.
* [DH#673] Fixed wrong datatype for field empty value being sent in the Objects API
  registration backend when the field is not visible.
* [DH#673] Fixed fields hidden because the parent fieldset or column is hidden not being
  sent to the Objects API. This is a follow up of :backend:`3980`.

2.5.5 (2023-04-03)
==================

Hotfix release for appointments bug

* [:backend:`4103`] Fixed incorrect appointment details being included in the submission PDF.
* [:backend:`4079`] Fixed metadata retrieval for DigiD failing when certificates signed by the G1
  root are used.
* [:backend:`4061`] Fixed not all form components being visible in the form builder when other
  components can be selected.
* Updated dependencies to their latest security releases.

2.6.1 (2024-03-28)
==================

Hotfix release

A number of issues were discovered in 2.6.0, in particular related to the additional
validation performed on the backend.

* [:backend:`4065`] Fixed validation being run for fields/components that are (conditionally)
  hidden. The behaviour is now consistent with the frontend.
* [:backend:`4068`] Fixed more backend validation issues:

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

* [:backend:`4069`] Fixed a crash in the form designer when navigating to the variables tab if you
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

* [:backend:`3688`] Objects API registration rework

    - Added support for selecting an available object type/version in a dropdown instead
      of copy-pasting a URL.
    - The objecttype definition (JSON-schema) is processed and will be used for validation.
    - Registration configuration is specified on the "variables" tab for each available
      (built-in or user-defined) variable, where you can select the appropriate object
      type property in a dropdown.
    - Added the ability to explicitly map a file upload variable into a specific object
      property for better data quality.
    - Ensured that the legacy format is still available (100% backwards compatible).

* [:backend:`3855`] Improved user experience of DMN integration

    - The available input/output parameters can now be selected in a dropdown instead of
      entering them manually.
    - Added robustness in case the DMN engine is not available.
    - Added caching of DMN evaluation results.
    - Automatically select the only option if there's only one.

* Added documentation on how to configure Camunda for DMN.
* Tweaked the dark-mode styling of WYSIWYG editors to better fit in the page.
* [:backend:`3164`] Added explicit timeout fields to services so they can be different from the
  global default.
* [:backend:`3695`] Improved login screen and flow

    - Allow opt-in to automatically redirect to OIDC provider.
    - Support WebAuthn (like YubiKey) hardware tokens.

* [:backend:`3885`] The admin form list now keeps track of open/collapsed form categories.
* [:backend:`3957`] Updated the eIDAS logo.
* [:backend:`3825`] Added a well-performing public API endpoint to list available forms, returning
  only minimal information.
* [:backend:`3825`] Added public API endpoint to list available form categories.
* [:backend:`3879`] Added documentation on how to add services for the service fetch feature.
* [:backend:`3823`] Added more extensive documentation for template filters, field regex validation
  and integrated this documentation more into the form builder.
* [:backend:`3950`] Added additional values to the eHerkenning CSP-header configuration.
* [:backend:`3977`] Added additional validation checks on submission completion of the configured
  formio components in form steps.
* [:backend:`4000`] Deleted the 'save and add another' button in the form designer to maintain safe
  blood pressure levels for users who accidentally clicked it.

**Bugfixes**

* [:backend:`3672`] Fixed the handling of object/array variable types in service fetch configuration.
* [:backend:`3890`] Fixed visually hidden fields not being sent to Objects API registration backend.
* [:backend:`1052`] Upgraded DigiD/eHerkenning library.
* [:backend:`3924`] Fixed updating of payment status when the "registration after payment is
  received" option is enabled.
* [:backend:`3909`] Fixed a crash in the form designer when you use the ZGW registration plugin
  and remove a variable that is mapped to a case property ("Zaakeigenschap").
* [:backend:`3921`] Fixed not all (parent/sibling) components being available for selection in the
  form builder.
* [:backend:`3922`] Fixed a crash because of invalid prefill configuration in the form builder.
* [:backend:`3958`] Fixed the preview appearance of read-only components.
* [:backend:`3961`] Reverted the merged KVK API services (basisprofiel, zoeken) back into separate
  configuration fields. API gateways can expose these services on different endpoints.
* [:backend:`3705`] Fixed the representation of timestamps (again).
* [:backend:`3975`, :backend:`3052`] Fixed legacy service fetch configuration being picked over the intended
  format.
* [:backend:`3881`] Fixed updating a re-usable form definition in one form causing issues in other
  forms that also use this same form definition.
* [:backend:`4022`] Fix crash on registration handling of post-payment registration. The patch for
  :backend:`3924` was bugged.
* [:backend:`2827`] Worked around an infinite loop when assigning the variable ``now`` to a field
  via logic.
* [:backend:`2828`] Fixed a crash when assigning the variable ``today`` to a variable via logic.

**Project maintenance**

* Removed the legacy translation handling which became obsolete with the new form builder.
* [:backend:`3049`] Upgraded the Django framework to version 4.2 (LTS) to guarantee future
  security and stability updates.
* Bumped dependencies to pull in their latest security/patch updates.
* Removed stale data migrations, squashed migrations and cleaned up old squashed migrations.
* [:backend:`851`] Cleaned up ``DocumentenClient`` language handling.
* [:backend:`3359`] Cleaned up the registration flow and plugin requirements.
* [:backend:`3735`] Updated developer documentation about pre-request clients.
* [:backend:`3838`] Divided the API into public and private API and their implied versioning
  policies.
* [:backend:`3718`] Removed obsolete translation data store.
* [:backend:`4006`] Added utility to detect KVK integration via API gateway.
* [:backend:`3931`] Remove dependencies on PyOpenSSL.

2.5.4 (2024-03-19)
==================

Hotfix release to address a regression in 2.5.3

* [:backend:`4022`] Fix crash on registration handling of post-payment registration. The patch for
  :backend:`3924` was bugged.

2.5.3 (2024-03-14)
==================

Bugfix release

* [:backend:`3863`] Fixed the generated XML for StUF-BG requests when retrieving partners/children.
* [:backend:`3920`] Fixed not being able to clear some dropdows in the new form builder (advanced
  logic, WYSIWYG content styling).
* [:backend:`3858`] Fixed a race condition that would manifest during parallel file uploads,
  leading to permission errors.
* [:backend:`3864`] Fixed handling of StUF-BG responses where one partner is returned.
* [:backend:`1052`] Upgraded DigiD/eHerkenning library.
* [:backend:`3924`] Fixed updating of payment status when the "registration after payment is
  received" option is enabled.
* [:backend:`3921`] Fixed not all (parent/sibling) components being available for selection in the
  form builder.
* [:backend:`3922`] Fixed a crash because of invalid prefill configuration in the form builder.
* [:backend:`3975`, :backend:`3052`] Fixed legacy service fetch configuration being picked over the intended
  format.
* [:backend:`3881`] Fixed updating a re-usable form definition in one form causing issues in other
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

* [:backend:`713`] Added JSON-template support for payment status update in the Objects API.
* [:backend:`3783`] Added minimal statistics for form submissions in the admin.
* [:backend:`3793`] Reworked the payment reference number generation to include the submission
  reference.
* [:backend:`3680`] Removed extraneous authentication plugin configuration on cosign V2 component.
* [:backend:`3688`] Added plumbing for improved objects API configuration to enforce data-constracts
  through json-schema validation. This is very work-in-progress.
* [:backend:`3730`] Added DMN-capabilities to our logic engine. You can now evaluate a Camunda
  decision definition and use the outputs for further form logic control.
* [:backend:`3600`] Added support for mapping form variables to case properties in the ZGW API's
  registration backend.
* [:backend:`3049`] Reworked the two-factor solution. You can now enforce 2FA for username/password
  accounts while not requiring this when authenticating through OpenID Connect.
* Added support for WebAuthn-compatible 2FA hardware tokens.
* [:backend:`2617`] Reworked the payment flow to only enter payment mode if the price is not zero.
* [:backend:`3727`] Added validation for minimum/maximum number of checked options in the selectboxes
  component.
* [:backend:`3853`] Added support for the KVK-Zoeken API v2.0. V1 is deprecated and will be shut
  down this year.

**Bugfixes**

* [:backend:`3809`] Fixed a crash when viewing a non-existing submission via the admin.
* [:backend:`3616`] Fixed broken PDF template for appointment data.
* [:backend:`3774`] Fixed dark-mode support in new form builder.
* [:backend:`3382`] Fixed translation warnings for date and datetime placeholders in the form
  builder.
* [:cve:`CVE-2024-24771`] Fixed (non-exploitable) multi-factor authentication weakness.
* [:backend:`3623`] Fixed some OpenID Connect compatibility issues with certain providers.
* [:backend:`3863`] Fixed the generated XML for StUF-BG requests when retrieving partners/children.
* [:backend:`3864`] Fixed handling of StUF-BG responses where one partner is returned.
* [:backend:`3858`] Fixed a race condition that would manifest during parallel file uploads,
  leading to permission errors.
* [:backend:`3822`] Fixed searching in form versions admin.

**Project maintenance**

* Updated to Python 3.10+ typing syntax.
* Update contributing documentation regarding type annotations.
* [:backend:`3806`] Added email field to customer detail fields for demo appointments plugin.
* Updated CI action versions to use the latest NodeJS version.
* [:backend:`3798`] Removed unused ``get_absolute_url`` in the form definition model.
* Updated to black version 2024.
* [:backend:`3049`] More preparations to upgrade to Django 4.2 LTS.
* [:backend:`3616`] Added docker-compose setup for testing SDK embedding.
* [:backend:`3709`] Improved documentation for embedding forms.
* [:backend:`3239`] Removed logic rule evaluation logging as it was incomplete and not very usable.
* Cleaned up some test helpers after moving them into libraries.
* Upgraded external librariesto their newest (security) releases.

2.5.2 (2024-02-06)
==================

Bugfix release

This release addresses a security weakness. We believe there was no way to actually
exploit it.

* [:cve:`CVE-2024-24771`] Fixed (non-exploitable) multi-factor authentication weakness.
* [:sdk:`642`] Fixed DigiD error message via SDK patch release.
* [:backend:`3774`] Fixed dark-mode support in new form builder.
* Upgraded dependencies to their latest available security releases.

2.5.1 (2024-01-30)
==================

Hotfix release to address an upgrade problem.

* Included missing UI code for GovMetric analytics.
* Fixed a broken migration preventing upgrading to 2.4.x and newer.
* [:backend:`3616`] Fixed broken PDF template for appointment data.

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

    * [:backend:`3712`] Replaced the form builder with our own implementation. The feature flag is
      now on by default for new instances. Existing instances need to toggle this.
    * [:backend:`2958`] Converted component translations to the new format used by the new form
      builder.
    * [:backend:`3607`] Added a new component type ``addressNL`` to integrate with the BRK.
    * [:backend:`2710`] Added "initials" to StufBG prefill options.

* Registration plugins

    * [:backend:`3601`], ZGW plugin: you can now register (part of) the submission data in the
      Objects API, and it will be related to the created Zaak.

      ⚠️ This requires a compatible version of the Objects API, see the
      `upstream issue <https://github.com/maykinmedia/objects-api/issues/355>`_.

* [:backend:`3726`] Reworked the payment flow to make it more obvious that payment is required.
* [:backend:`3707`] group synchronization/mapping can now be disabled with OIDC SSO.
* [:backend:`3201`] Updated more language to be B1-level.
* [:backend:`3702`] Simplified language in co-sign emails.
* [:backend:`180`] Added support for GovMetric analytics.
* [:backend:`3779`] Updated the menu structure following user feedback about the form building
  experience.
* [:backend:`3731`] Added support for "protocollering" headers when using the BRP Personen
  Bevragen API.

**Bugfixes**

* [:backend:`3656`] Fixed incorrect DigiD error messages being shown when using OIDC-based plugins.
* [:backend:`3705`] Fixed the ``__str__`` datetime representation of submissions to take the timezone
  into account.
* [:backend:`3692`] Fixed crash when using OIDC DigiD login while logged into the admin interface.
* [:backend:`3704`] Fixed the family members component not retrieving the partners when using
  StUF-BG as data source.
* Fixed 'none' value in CSP configugration.
* [:backend:`3744`] Fixed conditionally marking a postcode component as required/optional.
* [:backend:`3743`] Fixed a crash in the admin with bad ZGW API configuration.
* [:backend:`3778`] Ensured that the ``content`` component label is consistently *not* displayed
  anywhere.
* [:backend:`3755`] Fixed date/datetime fields clearing invalid values rather than showing a
  validation error.

**Project maintenance**

* [:backend:`3626`] Added end-to-end tests for submission resume flows.
* [:backend:`3694`] Upgraded to React 18.
* Removed some development tooling which was superceded by Storybook.
* Added documentation for a DigiD/eHerkenning LoA error and its solution.
* Refactored the utilities for dealing with JSON templates.
* Removed (EOL) 2.1.x from CI configuration.
* [:backend:`2958`] Added formio component Hypothesis search strategies.
* Upgraded to the latest ``drf-spectacular`` version.
* [:backend:`3049`] Replaced the admin array widget with another library.
* Upgraded libraries to have their latest security fixes.
* Improved documentation for the release process.
* Documented typing philosophy in contributing guidelines.
* Modernized dev-tooling configuration (isort, flake8, coverage).
* Squashed forms and config app migrations.

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

* [:backend:`3178`] Replaced more custom components with NL Design System components for improved
  themeing. You can now use design tokens for:

  * ``utrecht-document``
  * ``utrecht-page``
  * ``utrecht-page-header``
  * ``utrecht-page-footer``
  * ``utrecht-page-content``

* [:backend:`3573`] Added support for sending geo (Point2D) coordinates as GeoJSON to the Objects API.
* Added CSP ``object-src`` directive to settings (preventing embedding by default).
* Upgraded the version of the new (experimental) form builder.
* [:backend:`3559`] Added support for Piwik PRO Tag Manager as an alternative for Piwik PRO Analytics.
* [:backend:`3403`] Added support for multiple themes. You can now configure a default theme and
  specify form-specific styles to apply.
* [:backend:`3649`] Improved support for different vendors of the Documenten API implementation.
* [:backend:`3651`] The suffix to a field label for optional fields now uses simpler language.
* [:backend:`3005`] Submission processing can now be deferred until payment is completed (when
  relevant).

**Bugfixes**

* [:backend:`3362`] We've reworked and fixed the flow to redirect from the backend back to the
  form in the frontend, fixing the issues with hash-based routing in the process.
  Resuming forms after pausing, cosign flows... should now all work properly when you
  use hash-based routing.
* [:backend:`3548`] Fixed not being able to remove the MS Graph service/registration configuration.
* [:backend:`3604`] Fixed a regression in the Objects API and ZGW API's registration backends. The
  required ``Content-Crs`` request header was no longer sent in outgoing requests after
  the API client refactoring.
* [:backend:`3625`] Fixed crashes during StUF response parsing when certain ``nil`` values are
  present.
* Updated the CSP ``frame-ancestors`` directive to match the ``X-Frame-Options``
  configuration.
* [:backend:`3605`] Fixed unintended number localization in StUF/SOAP messages.
* [:backend:`3613`] Fixed submission resume flow not sending the user through the authentication
  flow again when they authenticated for forms that have optional authentication. This
  unfortunately resulted in hashed BSNs being sent to registration backends, which we
  can not recover/translate back to the plain-text values.
* [:backend:`3641`] Fixed the DigiD/eHerkenning authentication flows aborting when the user
  changes connection/IP address.
* [:backend:`3647`] Fixed a backend (logic check) crash when non-parsable time, date or datetime
  values are passed. The values are now ignored as if nothing was submitted.

**Project maintenance**

* Deleted dead/unused CSS.
* Upgraded dependencies having new patch/security releases.
* [:backend:`3620`] Upgraded storybook to v7.
* Updated the Docker image workflow, OS packages are now upgraded during the build and
  image vulnerability scanning added to the CI pipeline.
* Fixed generic type hinting of registry.
* [:backend:`3558`] Refactored the CSP setting generation from analytics configuration mechanism
  to be more resilient.
* Ensured that we send tracebacks to Sentry on DigiD errors.
* Refactored card component usage to use the component from the SDK.
* Upgraded WeasyPrint for PDF generation.
* [:backend:`3049`] Replaced deprecated calls to ``ugettext*``.
* Fixed a deprecation warning when using new-style middlewares.
* [:backend:`3005`] Simplified/refactored the task orchestration for submission processing.
* Require OF to be minimum of 2.4 before upgrading to 2.5.
* Removed original source migrations that were squashed in Open Forms 2.4.
* Replaced some (vendored) code with their equivalent library versions.
* Upgraded the NodeJS version from v16 to v20.
