.. developers_releases:

Release flow
============

Open Forms periodically releases new versions - feature releases and/or bugfix releases.

This document is intended for release managers preparing and pushing out a new release.

Versioning policy
-----------------

Open Forms follows `semantic versioning <https://semver.org/>`_. This means that we
have versions ``MAJOR.minor.patch``, optionally suffixed with a pre-release identifier
such as ``-beta.0`` or ``-rc.1``.

Preparing a release
-------------------

For new releases, a release branch is created, named: ``release/<new-version>``. All
release-related actions are concentrated in this branch.

**Updating the changelog**

``Changelog.rst`` contains a summary of changes compared to the previous release. Use
the new version followed by the (planned) release data as section title.

You may group the changes in logical groups like "New features", "Bug fixes" etc. to
enhance readability.

Breaking changes should include a ``.. warning::`` section indicating any possibly
manual actions required. Breaking (API) changes MUST result in a major version bump.

Make sure to include references to the related Github issues. These *should* already
be in the commit messages.

Cheat sheet: get the commits since the previous version, which can be a starting
point for the changelog entry:

.. code-block:: bash

    git log <previous-release-tag>..HEAD --reverse

**Bumping the version**

Use the ``bin/bumpversion.sh`` script, which is a wrapper around ``bump2version``. It
ensures that the ``package-lock.json`` file is also updated.

Examples:

.. code-block:: bash
    :caption: Bugfix release

    ./bin/bumpversion.sh patch

.. code-block:: bash
    :caption: Backwards compatible feature release

    ./bin/bumpversion.sh minor

.. code-block:: bash
    :caption: Backwards incompatible release

    ./bin/bumpversion.sh major

.. code-block:: bash
    :caption: Bump alpha -> beta -> release candidate

    ./bin/bumpversion.sh pre

.. code-block:: bash
    :caption: Bump build (alpha/beta/rc only)

    ./bin/bumpversion.sh build

After bumping the version, verify and commit the changes:

.. code-block:: bash

    git commit -am ":bookmark: Bumped version to <new-version>"


**Create a pull request**

Push the release branch to Github, create a pull request and assign a peer for review.

Publishing a release
--------------------

Once the PR has been reviewed and approved, merge it to the ``master`` branch, then
proceed to tagging the release.

**Tag the release**

Git tags are crucial to the release and build process - any pushed git tag results in
a build artifact with the same tag. Treat tags as immutable snapshots!

Release managers should configure their environment to sign tags using GPG, see the
`github documentation <https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-tags>`_.

Example:

.. code-block:: bash

    git tag -s <new-version>

Make sure to add a meaningful annotation - the safest bet is to copy the changelog
entry. This ensures the changes are also visible from the Github releases page.

The CI workflow will ensure that a Docker image with the same release tag is published.

**Announce the release in communication channels**

This is to be fleshed out more, but some existing channels are:

* Common Ground slack
* commonground.nl
* possible email subscribers
