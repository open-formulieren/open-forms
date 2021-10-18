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
and the stylesheets. Because of incompatibilities with node-sass, we can't update yet
to Node 16+. node-sass is pulled in through github dependencies, even though we use
Dart sass ourselves.

On this older version of node, we also still support the v1 format of
``package-lock.json``. You should use nvm_ to manage your local Node and npm versions.
NPM v6.x still uses the v1 lock format.

SDK toolchain
=============

In the SDK we use yarn_ rather than NPM. There is no particular version pinned at the
moment (since the lockfile format did not recently change). For the node version, it's
probably safest to use the same Node version as the backend toolchain.

.. _nvm: https://github.com/nvm-sh/nvm
.. _yarn: https://yarnpkg.com/
