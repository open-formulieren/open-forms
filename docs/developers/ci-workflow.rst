.. _developers_ci_workflow:

CI workflow
===========

Open Forms contains a CI workflow that performs many actions. For example:

    - Run the unit and end-to-end tests
    - Perform typechecking
    - Create Storybook builds with Chromatic snapshots
    - Build the documentation
    - Build and publish the Docker image

This document contains relevant information regarding this workflow.

GitHub actions
--------------

As part of hardening the CI workflow to improve our supply chain resiliency, we only allow a
specific set of `GitHub actions <https://docs.github.com/en/actions>`_ to be used in our workflow.
For these actions, we pin them to commit hashes instead of tags, to prevent modified tags
injecting malicious code into our container images. Changes to these commit hashes should be
thoroughly discussed and/or reviewed.

End-to-end tests
----------------

The end-to-end tests are executed in the backend repository of Open Forms, and use
the latest version of the SDK. Unfortunately, they are slow, and also not always
relevant for every pull request. They can be disabled by adding ``[skip: e2e]``
to the pull request description.

.. warning::

    With great power comes great responsibility!
