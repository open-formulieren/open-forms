.. _developers_frontend_index:

======================
Frontend documentation
======================

The 'frontend' is an ambiguous concept in the context of Open Forms as a combination
of software projects and associated code repositories. So, first, let's clear this up.

* The :ref:`developers_sdk_index` is responsible for the form rendering and interacting
  with the backend API.

* The `design tokens`_ package contains the design token definitions/values for the
  (default) theme. It is used by both the SDK and :ref:`Django backend <developers_backend_index>`
  for consistency in the UI/theme.

* The `formio builder`_ package is used by the Django backend, as part of the
  form designer user interface.

* The `formio renderer`_ package will replace formiojs/react-formio as the library used
  by the SDK.


So, this means we can identify the following **first party repositories**:

* ``open-formulieren/open-forms`` (backend)
* ``open-formulieren/open-forms-sdk`` (SDK)

Which are supported by the following **second party repositories**:

* ``open-formulieren/design-tokens``
* ``open-formulieren/formio-builder``
* ``open-formulieren/formio-renderer``

.. _design tokens: https://www.npmjs.com/package/@open-formulieren/design-tokens
.. _formio builder: https://www.npmjs.com/package/@open-formulieren/formio-builder
.. _formio renderer: https://github.com/open-formulieren/formio-renderer

.. _developers_frontend_index_i18n:

Managing translations
=====================

We standardize using FormatJS_ to manage frontend translations across all projects and
repositories. For React projects, this manifests as using the `react-intl`_ library.
See :ref:`developers_i18n` for day-to-day programming usage.

This section dives deeper in the entire toolchain and conventions to make it all work
together without too much friction.

Responsibilities
----------------

All user-facing literals should support localization in a translator-friendly format.
This means that you should not break up literals in individually translatable blocks,
but instead treat them as an atomic unit. The reasoning for this is that different
locales often have different sentence structures.

**Libraries** *also* need to declare their messages using ``FormattedMessage``,
``intl.formatMessage`` or equivalent constructs. Additionally, each library is
responsible for extracting its messages so that downstream libraries and projects can
incorporate them. They must distribute these message catalogs as part of the NPM package.

**Projects** are responsible for including the translations of libraries they use in the
final message catalog. Using the above library convention, this means that the FormatJS
CLI ``compile`` command should include the
``node_modules/@open-formulieren/*/i18n/message/{locale}.json`` glob path.

Message extraction and distribution
-----------------------------------

.. note:: The https://github.com/open-formulieren/formio-builder repository acts as the
   reference for the best practices here.

Libraries must provide the necessary shell scripts to correctly extract messages:

* ``bin/makemessages.sh``: script to extract messages from code for all supported locales
* ``npm run compilemessages``: optional but recommended - script to compile the messages for react-intl

The convention for libraries is to distribute the (uncompiled) messages in the NPM
package. The location must be ``i18n/messages/{locale}.json``. At the minimum, the ``en``
and ``nl`` locales must be supported.

Additionally, it's highly recommended to set up message compilation and use the
`react-intl storybook addon`_ to test and verify translations in isolation.

Example package layout:

.. code-block:: none

    .
    ├─┬ i18n
    │ ├─┬ compiled
    │ │ ├── en.json
    │ │ └── nl.json
    │ └─┬ messages
    │   ├── en.json
    │   └── nl.json
    └─┬ lib
      ├── cjs
      └── esm

It's **recommended** that projects follow the same structure as libraries, but it's not
required to change existing i18n structures.

Compiling the message catalogs
------------------------------

Projects (backend, SDK) are able to compile in the messages from libraries when:

* the messages are distributed in the package
* the messages are in a predictable location (see convention above)

This is easiest achieved through a helper shell script, ``bin/compilemessages_js.sh``.

For reference, the backend script:

.. code-block:: bash

    #!/bin/bash
    #
    # Usage, from the root of the repository:
    #
    #   ./bin/compilemessages_js.sh
    #

    SUPPORTED_LOCALES=(
      en
      nl
    )

    for locale in "${SUPPORTED_LOCALES[@]}"; do
      echo "Compiling messages for locale '$locale'"
      npm run compilemessages -- \
        --ast \
        --out-file "src/openforms/js/compiled-lang/$locale.json" \
        "src/openforms/js/lang/$locale.json" \
        "node_modules/@open-formulieren/*/i18n/messages/$locale.json"
    done

This script can handle current and future NPM packages published in the
@open-formulieren namespace that comply with the package layout conventions.

.. _FormatJS: https://formatjs.github.io/
.. _react-intl: https://formatjs.github.io/docs/getting-started/installation
.. _react-intl storybook addon: https://storybook.js.org/addons/storybook-react-intl


Topics
======

.. toctree::
   :maxdepth: 1

   admin-styling
