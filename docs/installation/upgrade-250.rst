.. _installation_upgrade_250:

===================================
Upgrade details to Open Forms 2.5.0
===================================

We do our best to avoid breaking changes, but at times we cannot guarantee that your
configuration will keep working flawlessly. Open Forms 2.5.0 is such a release - and
the manual interventions with context are documented here.

.. contents:: Jump to
   :depth: 1
   :local:

Form styling - SDK
==================

We continue our adoption of NL Design System, for which the SDK has received some
overhauls. Please read and apply the `SDK 2.1 upgrade notes`_.

.. _SDK 2.1 upgrade notes: https://open-formulieren.github.io/open-forms-sdk/?path=/docs/developers-upgrade-notes-2-1-0--docs

Form styling - backend
======================

Additionally, we've reworked more components in our "backend" which renders the forms,
most notably the page header, footer and general scaffolding. This refactor is backwards
compatible and covered by an automatic migration, however some tokens cannot be reliably
converted.

.. note:: We have broken some legacy shorthand values into their individual parts. E.g.
   a padding value of ``10px 20px`` translates to:

   * block-start padding: 10px
   * block-end padding: 10px
   * inline-start padding: 20px
   * inline-end padding: 20px

Page footer
-----------

The old token ``of.page-footer.mobile.padding`` should be used for:

* ``--of-utrecht-page-footer-mobile-padding-block-end``
* ``--of-utrecht-page-footer-mobile-padding-block-start``
* ``--of-utrecht-page-footer-mobile-padding-inline-end``
* ``--of-utrecht-page-footer-mobile-padding-inline-start``

The old token ``of.page-footer.tablet.padding`` should be used for:

* ``--of-utrecht-page-footer-tablet-padding-block-end``
* ``--of-utrecht-page-footer-tablet-padding-block-start``
* ``--of-utrecht-page-footer-tablet-padding-inline-end``
* ``--of-utrecht-page-footer-tablet-padding-inline-start``

The old token ``of.page-footer.laptop.padding`` should be used for:

* ``--of-utrecht-page-footer-laptop-padding-block-end``
* ``--of-utrecht-page-footer-laptop-padding-block-start``
* ``--of-utrecht-page-footer-laptop-padding-inline-end``
* ``--of-utrecht-page-footer-laptop-padding-inline-start``

The old token ``of.page-footer.desktop.padding`` should be used for:

* ``--of-utrecht-page-footer-desktop-padding-block-end``
* ``--of-utrecht-page-footer-desktop-padding-block-start``
* ``--of-utrecht-page-footer-desktop-padding-inline-end``
* ``--of-utrecht-page-footer-desktop-padding-inline-start``

Page header
-----------

The old token ``of.page-header.mobile.padding`` should be used for:

* ``--of-utrecht-page-header-mobile-padding-block-end``
* ``--of-utrecht-page-header-mobile-padding-block-start``
* ``--of-utrecht-page-header-mobile-padding-inline-end``
* ``--of-utrecht-page-header-mobile-padding-inline-start``

The old token ``of.page-header.tablet.padding`` should be used for:

* ``--of-utrecht-page-header-tablet-padding-block-end``
* ``--of-utrecht-page-header-tablet-padding-block-start``
* ``--of-utrecht-page-header-tablet-padding-inline-end``
* ``--of-utrecht-page-header-tablet-padding-inline-start``

The old token ``of.page-header.laptop.padding`` should be used for:

* ``--of-utrecht-page-header-laptop-padding-block-end``
* ``--of-utrecht-page-header-laptop-padding-block-start``
* ``--of-utrecht-page-header-laptop-padding-inline-end``
* ``--of-utrecht-page-header-laptop-padding-inline-start``

The old token ``of.page-header.desktop.padding`` should be used for:

* ``--of-utrecht-page-header-desktop-padding-block-end``
* ``--of-utrecht-page-header-desktop-padding-block-start``
* ``--of-utrecht-page-header-desktop-padding-inline-end``
* ``--of-utrecht-page-header-desktop-padding-inline-start``

Page
----

You may want to specify a background color for the ``.utrecht-page`` selector. Open
Forms currently falls back to ``--of-layout-background-color``, but if you have a custom
theme this will not be picked up.

Other
-----

These are direct mappings and are handled automatically, but if you have custom
stylesheets/themes, you should update these:

* ``--of-page-footer-bg`` becomes ``--utrecht-page-footer-background-color``
* ``--of-page-footer-fg`` becomes ``--utrecht-page-footer-color``
* ``--of-page-header-bg`` becomes ``--utrecht-page-header-background-color``
* ``--of-page-header-fg`` becomes ``--utrecht-page-header-color``
* ``--of-page-header-logo-return-url-min-height`` becomes
  ``--of-page-header-logo-return-url-min-block-size``
* ``--of-page-header-logo-return-url-min-width`` becomes
  ``--of-page-header-logo-return-url-min-inline-size``
* ``--of-page-header-logo-return-url-mobile-min-height`` becomes
  ``--of-page-header-logo-return-url-mobile-min-block-size``
* ``--of-page-header-logo-return-url-mobile-min-width`` becomes
  ``--of-page-header-logo-return-url-mobile-min-inline-size``
