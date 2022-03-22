.. _developers_npm:

=========
NPM usage
=========

NPM is the Node package manager, where Node is used in the frontend toolchain.

Note that we have "two frontends":

1. The frontend toolchain for Open Forms (= the backend)
2. The toolchain for the Open Forms SDK (= the frontend)

Backend toolchain
=================

In the backend project, we use Node and NPM for the admin interface UI (React-based)
and the stylesheets. You should use nvm_ to manage your local Node and npm versions.

From the root of the project:

.. code-block:: bash

    nvm install  # one time only
    nvm use  # to use the configured node version in .nvmrc

SDK toolchain
=============

In the SDK we use yarn_ rather than NPM. There is no particular version pinned at the
moment (since the lockfile format did not recently change). For the node version, it's
probably safest to use the same Node version as the backend toolchain.

.. _nvm: https://github.com/nvm-sh/nvm
.. _yarn: https://yarnpkg.com/
