.. _developers_releases:

Release flow
============

Open Forms periodically releases new versions - feature releases and/or bugfix releases.

This document is intended for release managers preparing and pushing out a new release.

.. _developers_releases_versioning:

Versioning policy
-----------------

Open Forms follows `semantic versioning <https://semver.org/>`_. This means that we
have versions ``MAJOR.minor.patch``, optionally suffixed with a pre-release identifier
such as ``-beta.0`` or ``-rc.1``.

Note that Open Forms itself has a version, and the API provided by Open Forms has its
own version. API changes must also be judged based on semver and result in a matching
version number change. This is tracked in the ``API_VERSION`` setting.

See also the :ref:`developers_versioning`.

Preparing a release
-------------------

For new releases, a release branch is created, named: ``release/<new-version>``.
For minor and major releases, checkout from ``master``. For patch releases, checkout
from ``stable/<major>.<minor>.x``. All release-related actions are concentrated in this branch.

**Updating translation strings**

Messages are localized/translated as part of the release process. There exists a wrapper
script that automates this as much as possible:

.. code-block:: bash

    ./bin/makemessages.sh

This extracts the backend translations in the appropriate ``.po`` files and the
JavaScript translations into the ``src/openforms/js/lang/[locale].json`` files.

You can use the script ``python ./bin/find_untranslated_js.py`` to scan for (likely)
missing JS translations.

Note that the translations in ``src/openforms/js/lang/formio/[locale].json`` cannot be
automatically extracted and requires tedious manual checking and adding translations.

**Re-recording the VCR cassettes**

(Stable) minor and major releases must re-record the VCR cassettes to ensure that any
feature that interacts with external APIs still works properly. Re-recording the
cassettes forces the tests to talk to the real services again instead of replaying the
recorded mock data, which can give a false sense of security.

You may have to run subsets of the test suite separately, due to different integrations
all configured on the same obfuscated URL (e.g. ``http://localhost:8080``), for example:

.. code-block:: bash

    python src/manage.py test openforms.authentication.contrib.digid

.. note::

    One example of this is in appointments - ``mitmproxy`` is used and exposes the
    external service on ``http://localhost:8080``, but the Camunda tests also expect
    this URL to be available. The Camunda tests would fail here because the returned
    data is not compatible with the Camunda API at all.

    Camunda tests are skipped by default if the test code cannot connect to
    ``localhost:8080``, so you don't run into this issue usually.

Instructions and (pointers to) credentials are documented in our internal Taiga.

Delete the existing/recorded cassettes and then commit the results/changes.

.. note::

    Setting ``VCR_RECORD_MODE=all`` in your environment appends new episodes instead of
    overwriting them, which is not the desired result.

**Updating the changelog**

``CHANGELOG.rst`` contains a summary of changes compared to the previous release. Use
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

    git log <previous-release-tag>...HEAD \
        --date=format:"%Y-%m-%d" \
        --cherry \
        --decorate=auto \
        --pretty=format:"* %s %d" \
        --reverse

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

Once the PR has been reviewed and approved, merge it to:

* the ``master`` branch for minor and major releases
* the ``stable/<major>.<minor>.x`` branch for patch releases.

Then proceed to tagging the release.

**Maintenance + Docker Hub preparation (new minor versions)**

When a new minor version is released, the matching ``stable/<major>.<minor>.x`` needs
to be created and pushed to Github. Any bugfixes that require backporting are done to
these stable branches.

Additionally, you need to register the stable branch in ``docker/ci/config.json`` under
the ``supportedTags`` key, which is used as input for the Docker Hub README generation.

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

**Forward port changelog for patch releases**

For patch releases only, update the ``CHANGELOG.rst`` on the master branch with the new summary of changes.
Order the entries by date (most recent first). If multiple patch versions are done on the same day, order them by
version (most recent first).

Stable releases and on-going development
----------------------------------------

Open Forms follows the one-flow branching model: the ``master`` branch is the main
branch. Features and bugfixes are developed in separate branches (e.g. ``feature/foo``
and ``issue/bar``) with a pull request to ``master``.

Supported stable (and upcoming) releases have their own branch following the pattern
``stable/<major>.<minor>.x``. Conforming to the :ref:`developers_releases_versioning`,
bugfixes merged into ``master`` must be backported to the respective release branch(es).
Pull requests with bugfixes must be tagged with the **needs-backport** label. The
release branches are tested in CI as well.

The person merging the pull request is responsible for making sure the fix ends up in
the appropriate release branch as well. This can be done via:

* cherry-picking the relevant commit(s) on the release branch and pushing to the release
  branch
* creating a branch to cherry-pick the commit(s) on and make a pull request to the
  release branch

The person merging the pull request is responsible for making sure the build on the
release branch (still) passes.

When backporting commits, please add tags to the resulting (cherry-picked) commits to
cross reference everything. This should look something like:

.. code-block:: none

    :bug: [#123] -- Fixed a Very Nasty bug

    <elaborate description>

    Backport-Of: open-formulieren/open-forms#987

...so that it points to the original bugfix PR. In the original bugfix PR, add a comment
with the resulting backport commit hashes.

You can decide to rebase multiple backport commits into a single one - as long as
everything is linked together this is okay.

Bundling of SDK inside Open Forms backend image
-----------------------------------------------

The Open Forms backend image includes a version of the SDK for ease of deployment under
the ``/static/sdk/`` prefix. The particular SDK version should be aligned with the
backend version, which can be controlled through docker build args.

To produce a backend image build of Open Forms version ``x.y.z`` with SDK version
``a.b.c``, the following steps must be performed in the right order:

1. Build the SDK version ``a.b.c.`` and ensure it is pushed to Docker Hub or otherwise
   available to the backend build environment.
2. Update the file ``.sdk-release`` in the backend repository with the version ``a.b.c``
3. Specify ``--build-arg RELEASE=x.y.z`` and ``--build-arg SDK_RELEASE=a.b.c.`` for the
   backend image build. On CI, this happens automatically.
4. Build, tag and push the backend image.

By default ``RELEASE`` and ``SDK_RELEASE`` are set to ``latest``, and if the SDK image
is not available on the local filesystem, it will be pulled from Docker Hub.

On CI, if the backend release is ``latest``, SDK release ``latest`` will be included.
Otherwise, the release in the file ``.sdk-release`` is used.

.. todo:: Set up the SDK and backend version compatibility matrix
