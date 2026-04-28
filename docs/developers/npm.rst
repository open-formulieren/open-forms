.. _developers_npm:

===================
Frontend toolchains
===================

NPM is the Node package manager, where Node is used in the frontend toolchains.

Note that we have "two frontends":

1. The frontend toolchain for Open Forms (= the backend), including helper libraries
   like the ``formio-builder``.
2. The toolchain for the Open Forms SDK (= the frontend), including helper libraries
   like the ``formio-renderer``.

Common tooling
==============

The common tooling applies to Open Forms, the SDK and the supporting libraries like
the formio-builder, formio-renderer and types repository.

**NVM**

You should use nvm_ (or similar tools) to manage your local Node and npm versions.

From the root of the project:

.. code-block:: bash

    nvm install  # one time only
    nvm use  # to use the configured node version in .nvmrc

**Prettier**

We don't like endless discussions about code formatting. For that, we leverage Prettier_
to perform the formatting for us. The CI pipelines run the ``checkformat`` scripts, and
locally you can format the code using the ``format`` script.

It is recommended to configure your editor or a pre-commit hook to run the prettier
formatting when a ``.prettierrc.json`` config file is available.

Currently, Prettier is configured to format ``.js``, ``.ts(x)`` and ``.scss`` files.

**Storybook**

All projects/libraries have a Storybook for the UI components. When you're working on
components that aren't in Storybook yet, please add them.

The `SDK Storybook`_ contains more technical documentation for the SDK. You can usually
run storybook with:

.. code-block:: bash

    npm run storybook [-- --no-open]

Writing `interaction tests <https://storybook.js.org/docs/writing-tests/interaction-testing>`_ is
recommended, but please limit those to actual interactions. For more low-level tests,
stick to writing unit tests in `Vitest browser mode <https://vitest.dev/guide/browser/>`_.
Stories are run in Chromatic, and each snapshot costs money.

Some older codebases that don't use ViteJS-based tooling yet, require tests to be
written in Jest using `Testing Library <https://www.npmjs.com/package/@testing-library/react>`_.

**Managing translations**

Translations are extracted from the code with helper scripts, and after the
translations have been edited in the JSON files, you can compile them via the
compilation helper scripts. We currently check both source and compiled messages into
version control. See :ref:`developers_frontend_index_i18n` for detailed instructions,
as we're currently re-organizing the tooling here.

Cheat sheet:

* SDK: ``npm run makemessages`` and ``npm run compilemessages``
* Backend: ``./bin/makemessages_js.sh`` and ``./bin/compilemessages_js.sh``
* Libraries: ``./bin/makemessages.sh`` and ``npm run compilemessages``

**Linting**

We lint the codebase with ESLint_. Usually you can run this locally through:

.. code-block:: bash

    npm run lint

For the ViteJS-based toolchains, the linting is usually run as part of the build process.

**.editorconfig**

Indent sizes and other code formatting rules are specified in the ``.editorconfig`` file,
which should be supported by most editors. Possibly you need to install a plugin for it
to be activated though.

.. _nvm: https://github.com/nvm-sh/nvm
.. _yarn: https://yarnpkg.com/
.. _Prettier: https://prettier.io/
.. _SDK Storybook: https://open-formulieren.github.io/open-forms-sdk/
.. _ESLint: https://eslint.org/
