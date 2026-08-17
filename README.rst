==========
Open Forms
==========

.. image:: .github/assets/open-formulieren-logo.svg
    :height: 100px
    :alt: Open Forms

:Version: 4.0.0-alpha.2
:Source: https://github.com/open-formulieren/open-forms
:Keywords: e-Formulieren, Common Ground, FormIO, API

|docs| |docker|

Easily create and publish smart forms (`Nederlandse versie`_)

Developed by `Maykin B.V.`_, initiated by the `Stakeholders`_.


Introduction
============

Using Open Forms, administrators can quickly create powerful and smart forms
that are exposed via an API. With the Open Forms JavaScript `SDK`_, personalized
forms can be retrieved and shown to the user. The form blends in with an
existing website using various styling options. Form fields are pre-filled
whenever possible and personalized choices are shown depending on the user, if
authenticated.

Using a plugin-based architecture, Open Forms allows for flexible submission
backends (e.g. `Open Zaak`_), authentication schemes, payment providers, calendar
apps and pre-fill services.

Open Forms is developed in line with the `Common Ground`_ principles,
with many plugins for government usage and with a strong focus on usability for
both end users and administrators.

.. image:: docs/introduction/_assets/open-forms-from-designer-to-form.png
    :width: 100%

.. _`SDK`: https://github.com/open-formulieren/open-forms-sdk/
.. _`Common Ground`: https://commonground.nl/
.. _`Open Zaak`: https://open-zaak.readthedocs.io/


Sustainable Management
======================

This software is open source and free to use under the terms of the EUPL. However, safe and reliable use in a production environment requires structured management, including security updates, dependency and release management, quality assurance, and vulnerability handling. Maintaining public-facing functions associated with the open-source product also requires a sustained commitment.

**Public code calls for public responsibility.**

The `Stakeholders`_ expect public organizations, using this software in production, to make a financial contribution towards its collective maintenance.

Read more about the management organization, contributions, and responsibilities in `PROJECT_GOVERNANCE.md`_.


Component
=========

|build-status| |coverage| |code-quality| |ruff| |python-versions|

This component includes the **Open Forms Admin UI** and the **Open Forms API**.

API Specifications
------------------

These can be found in the `documentation <https://open-forms.readthedocs.io/en/latest/developers/versioning.html#open-forms-api>`_


References
==========

* `Documentation <https://open-forms.readthedocs.io/>`_
* `Community <https://commonground.nl/groups/view/0c79b387-4567-4522-bc35-7d3583978c9f/open-forms>`_
* `Docker image <https://hub.docker.com/r/openformulieren/open-forms>`_
* `Issues <https://github.com/open-formulieren/open-forms/issues>`_
* `Code <https://github.com/open-formulieren/open-forms>`_
* `Open Forms SDK <https://github.com/open-formulieren/open-forms-sdk>`_


Licence
=======

Copyright © the `Stakeholders`_, 2025

Licensed under the `EUPL`_.

.. _`Nederlandse versie`: README.NL.rst
.. _`Maykin B.V.`: https://www.maykin.nl
.. _`Stakeholders`: STAKEHOLDERS.md
.. _`PROJECT_GOVERNANCE.md`: PROJECT_GOVERNANCE.md
.. _`EUPL`: LICENSE.md

.. |build-status| image:: https://github.com/open-formulieren/open-forms/actions/workflows/ci.yml/badge.svg
    :alt: Build status
    :target: https://github.com/open-formulieren/open-forms/actions/workflows/ci.yml

.. |code-quality| image:: https://github.com/open-formulieren/open-forms/actions//workflows/code_quality.yml/badge.svg
    :alt: Code quality checks
    :target: https://github.com/open-formulieren/open-forms/actions//workflows/code_quality.yml

.. |docs| image:: https://readthedocs.org/projects/open-forms/badge/?version=latest
    :target: https://open-forms.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation status

.. |coverage| image:: https://codecov.io/github/open-formulieren/open-forms/branch/main/graphs/badge.svg?branch=main
    :alt: Coverage
    :target: https://codecov.io/gh/open-formulieren/open-forms

.. |ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Ruff

.. |docker| image:: https://img.shields.io/docker/v/openformulieren/open-forms?sort=semver
    :alt: Docker image
    :target: https://hub.docker.com/r/openformulieren/open-forms

.. |python-versions| image:: https://img.shields.io/badge/python-3.12-blue.svg
    :alt: Supported Python versions
