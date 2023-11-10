.. _installation_upgrade_240:

===================================
Upgrade details to Open Forms 2.4.0
===================================

We do our best to avoid breaking changes, but at times we cannot guarantee that your
configuration will keep working flawlessly. Open Forms 2.4.0 is such a release - and
the manual interventions with context are documented here.

.. contents:: Jump to
   :depth: 1
   :local:


Check forms with duplicated steps
=================================

We now block duplicated form steps at the database level - if you have forms in your
environment with non-unique steps, the upgrade will refuse to execute (or crash if
you disable checks).

The check script is available since Open Forms 2.3.4, you can run it using:

.. code-block:: bash

    python /app/bin/check_non_unique_steps.py

and it will report any problematic forms. These forms need to be updated manually to
remove the duplicated steps.

DigiD/eHerkenning configuration
===============================

DigiD and/or eHerkenning configuration before Open Forms 2.4.0 required manually
uploading the XML metadata file.

This file is now automatically retrieved, provided you configure the "(XML) metadata
URL". We cannot populate this URL on existing instances, so you need to configure this
manually by navigating to:

* **Admin** > **Configuratie** > **DigiD-configuratie** and
* **Admin** > **Configuratie** > **EHerkenning/eIDAS-configuratie**

The field can be found under the "Identity provider" section.

Once these URLs are configured, the metadata file field and the identity provider ID
will be automatically populated.

Our upgrade mechanism automatically generates the relevant CSP directives from your
existing DigiD/eHerkenning configuration.

.. note:: Any previously uploaded metadata files continue to work as expected.

KVK Configuration
=================

We've done some extensive code and configuration cleanups, and the KVK configuration may
be affected by this. The service configuration for the "zoeken" and "basisprofiel" API's
has been merged into a single service. Normally this configuration update should have
been performed correctly automatically, but we can't rule out possible mistakes with
more exotic configurations (e.g. when using API gateways).

⚠️ Please check and update your configuration if necessary - you can check this via:
**Admin** > **Configuratie** > **Configuratie overzicht** and look for the KVK entries.

If you run into any errors, then please check your certificate configuration, API key
and validate that the API root does *not* include the ``v1/`` suffix. An example of a
correct API root: ``https://api.kvk.nl/api/`` or ``https://api.kvk.nl/test/api/``.

Button styling
==============

We are committed to NL Design System and have overhauled our custom button
implementation and styles.

Our buttons used custom design tokens since they were implemented before the `NL Design
System buttons`_ were much of a thing. *Most* of the tokens map cleanly, and if you
have configured any overrides in the admin environment they should have been
automatically migrated. However, we urge you to verify the configuration on a
test/acceptance environment and prepare the necessary changes.

However, if you have made custom CSS changes, we cannot incorporate those and you will
have to check your customizations. You will have to manually check if those changes
are still relevant or not. Our advice is to also take a critical look - the transition
to community components should make it much easier to change the appearance and behaviour
using design tokens rather than CSS overrides.

.. note:: We recommend setting up your own theme rather than trying to override the
   ``.openforms-theme``, but with the CSS precedence order it should still be possible
   to override token values via the admin interface.

.. warning:: The automatic migration we ship cannot be reversed - we recommend creating
   a database backup before upgrading in case you need to do a rollback.

.. _NL Design System buttons: https://nl-design-system.github.io/utrecht/storybook/?path=/docs/css-button-tokens--docs

Reference
---------

The CSS mapping below is the one we have taken into account for our automatic migration,
using the following logic:

* if the Open Forms token (right hand side) exists, extract the value and assign it to
  the matching NL DS token (left hand side)
* if the NL DS token is already specified, abort and keep the explicitly defined value

The mapping below shows the NL Design System tokens populated from our custom tokens:

.. code-block:: scss

    :root {
        /*  --utrecht-action-disabled-cursor: not-allowed;*/
        /*  --utrecht-action-submit-cursor: pointer;*/

        /* generic */
        --utrecht-button-background-color: var(--of-button-bg);
        --utrecht-button-border-color: var(--of-button-color-border);
        // --utrecht-button-border-width: 1px;
        --utrecht-button-color: var(--of-button-fg);
        --utrecht-button-font-family: var(--of-typography-sans-serif-font-family);
        // --utrecht-button-font-size: 1.125rem;
        // --utrecht-button-line-height: 1.333;
        // --utrecht-button-padding-block-end: 10px;
        // --utrecht-button-padding-block-start: 10px;
        // --utrecht-button-padding-inline-end: 12px;
        // --utrecht-button-padding-inline-start: 12px;

        --utrecht-button-hover-background-color: var(--of-button-hover-bg);
        --utrecht-button-hover-border-color: var(--of-button-hover-color-border);

        --utrecht-button-active-background-color: var(--of-button-active-bg);
        --utrecht-button-active-border-color: var(--of-button-active-color-border);
        --utrecht-button-active-color: var(--of-button-active-fg);

        --utrecht-button-focus-border-color: var(--of-button-focus-color-border);

        /* primary */
        // non-modified
        --utrecht-button-primary-action-background-color: var(--of-button-primary-bg);
        --utrecht-button-primary-action-border-color: var(--of-button-primary-color-border);
        /*  --utrecht-button-primary-action-border-width: 2px;*/
        --utrecht-button-primary-action-color: var(--of-button-primary-fg);

        // hover
        --utrecht-button-primary-action-hover-background-color: var(--of-button-primary-hover-bg);
        --utrecht-button-primary-action-hover-border-color: var(--of-button-primary-hover-color-border);

        // active
        --utrecht-button-primary-action-active-background-color: var(--of-button-primary-active-bg);
        --utrecht-button-primary-action-active-border-color: var(--of-button-primary-active-color-border);
        --utrecht-button-primary-action-active-color: var(--of-button-primary-active-fg);

        // focus, focus-visible
        --utrecht-button-primary-action-focus-border-color: var(--of-button-primary-focus-color-border);

        /* primary+danger */
        --utrecht-button-primary-action-danger-background-color: var(--of-button-danger-bg);
        --utrecht-button-primary-action-danger-border-color: var(--of-button-danger-color-border);
        --utrecht-button-primary-action-danger-color: var(--of-button-danger-fg);

        // hover
        --utrecht-button-primary-action-danger-hover-background-color: var(--of-button-danger-hover-bg);
        --utrecht-button-primary-action-danger-hover-border-color: var(
          --of-button-danger-hover-color-border
        );

        // active
        --utrecht-button-primary-action-danger-active-background-color: var(--of-button-danger-active-bg);
        --utrecht-button-primary-action-danger-active-border-color: var(
          --of-button-danger-active-color-border
        );
        --utrecht-button-primary-action-danger-active-color: var(--of-button-danger-active-fg);

        // focus, focus-visible
        --utrecht-button-primary-action-danger-focus-border-color: var(
          --of-button-danger-focus-color-border
        );

        /* secondary */
        --utrecht-button-secondary-action-background-color: var(--of-color-bg);
        --utrecht-button-secondary-action-border-color: var(--of-color-border);
        // --utrecht-button-secondary-action-border-width: 2px;
        --utrecht-button-secondary-action-color: var(--of-color-fg);

        // hover
        --utrecht-button-secondary-action-hover-background-color: var(--of-button-hover-bg);
        --utrecht-button-secondary-action-hover-border-color: var(--of-button-hover-color-border);

        // active
        --utrecht-button-secondary-action-active-background-color: var(--of-button-active-bg);
        --utrecht-button-secondary-action-active-border-color: var(--of-button-active-color-border);
        --utrecht-button-secondary-action-active-color: var(--of-button-active-fg);

        // focus, focus-visible
        --utrecht-button-secondary-action-focus-border-color: var(--of-color-focus-border);

        /* secondary+danger */
        --utrecht-button-secondary-action-danger-background-color: var(--of-button-danger-bg);
        --utrecht-button-secondary-action-danger-border-color: var(--of-button-danger-color-border);
        --utrecht-button-secondary-action-danger-color: var(--of-button-danger-fg);

        // hover
        --utrecht-button-secondary-action-danger-hover-background-color: var(--of-button-danger-hover-bg);
        --utrecht-button-secondary-action-danger-hover-border-color: var(
          --of-button-danger-hover-color-border
        );

        // active
        --utrecht-button-secondary-action-danger-active-background-color: var(
          --of-button-danger-active-bg
        );
        --utrecht-button-secondary-action-danger-active-border-color: var(
          --of-button-danger-active-color-border
        );
        --utrecht-button-secondary-action-danger-active-color: var(--of-button-danger-active-fg);

        // focus, focus-visible
        --utrecht-button-secondary-action-danger-focus-border-color: var(
          --of-button-danger-focus-color-border
        );

        /* subtle */
        --utrecht-button-subtle-danger-background-color: var(--of-button-danger-bg);
        --utrecht-button-subtle-danger-border-color: var(--of-button-danger-color-border);
        --utrecht-button-subtle-danger-color: var(--of-color-danger);

        --utrecht-button-subtle-danger-active-background-color: var(--of-color-danger);
        --utrecht-button-subtle-danger-active-color: var(--of-color-bg);
    }

The commented out tokens are values that used to be hardcoded in our CSS, but should now
be specified via design tokens and reflect the (default) values set in the Open Forms theme.

Alert styling
=============

We've refactored our alert styling to make use of the ``utrecht-alert`` component. This
effectively replaces the ``--of`` design tokens with the ``--utrecht`` ones. A backwards
compatibility layer is set up which will be dropped in Open Forms 3.0, so we recommend
updating your stylesheets.

There is no automatic data migration set up (yet).

Reference
---------

The mapping below shows the NL Design System tokens populated from our custom tokens:

.. code-block:: scss

    :root {
        --utrecht-alert-warning-background-color: var(--of-alert-warning-bg);
        --utrecht-alert-info-background-color: var(--of-alert-info-bg);
        --utrecht-alert-error-background-color: var(--of-alert-error-bg);
        --utrecht-alert-icon-error-color: var(--of-color-danger);
        --utrecht-alert-icon-info-color: var(--of-color-info);
        --utrecht-alert-icon-warning-color: var(--of-color-warning);
        --utrecht-alert-icon-ok-color: var(--of-color-success);
    }
