.. _developers_versioning:

Versioning policy
=================

Because Open Forms ("as a suite") is a collection of components developed individually
from each other, it's important to be aware of the compatible versions to guarantee
that the application(s) keep working as expected.

We identify three major components having their own version numbers:

* Open Forms API, the API implemented by the Open Forms backend
* Open Forms SDK, the client application consuming the API
* Open Forms backend, implements the API, administrative interface and various
  modules/plugins (see :ref:`developers_architecture`).

The Open Forms SDK and Open Forms API versions must be aligned with each other for
correct functioning of the forms.

All versions adhere to `semantic versioning <https://semver.org/>`_, meaning major
versions may introduce breaking changes and minor versions are backwards compatible.

Open Forms SDK
--------------

The SDK follows its own semantic versioning scheme. Major versions typically mean that
users of the Javascript interfaces are impacted (npm package users or users modifying
the window global directly in their own code).

Whenever new features are added to the SDK that depend on certain API functionality
being available, then *at least* the minor version of the SDK will be bumped.

Newer minor API versions should be compatible with a given minor SDK version, per the
semantic versioning principles.

The table below documents the required API version ranges for a given SDK version. The
maximum API version should usually not be applicable, unless the SDK relies on
experimental feature changes (see :ref:`developers_versioning_api`).

.. table:: Required API version ranges
   :widths: auto

   ================ =================== ===================
   SDK version      minimum API version maximum API version
   ================ =================== ===================
   3.2.0            3.1.0               n/a
   3.1.0            3.1.0               n/a
   3.0.0            3.0.0               n/a
   2.4.0            2.8.0               2.8.x
   ================ =================== ===================

End-of-life versions are not listed in this table.

.. _developers_versioning_api:

Open Forms API
--------------

Open Forms exposes a public and a private API. Semantic versioning is applied for the
public API. However, breaking changes to the private API can happen in minor and patch versions.

We also use the `specification extension`_ pattern in the API spec to mark functionality
as experimental, using the ``x-experimental: true`` flag.

We use this to mark parts of the API that we are not yet convinced about that they
are the right implementation. Release notes of Open Forms backend will include which
experimental functionality was changed.

.. _specification extension: https://swagger.io/specification/#specification-extensions


==============  ==============  =============================
Version         Release date    API specification
==============  ==============  =============================
latest          n/a             `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/master/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/master/src/openapi.yaml>`__
3.2.0           2025-07-11      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/3.2.0/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/3.2.0/src/openapi.yaml>`__
3.1.0           2025-03-31      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/3.1.0/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/3.1.0/src/openapi.yaml>`__
3.0.0           2025-01-09      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/3.0.0/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/3.0.0/src/openapi.yaml>`__
==============  ==============  =============================

See: `All versions and changes <https://github.com/open-formulieren/open-forms/blob/master/CHANGELOG.rst>`_

**Unsupported versions**

==============  ==============  =============================
Version         Release date    API specification
==============  ==============  =============================
2.8.0           2024-09-27      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.8.0/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.8.0/src/openapi.yaml>`__
2.7.0           2024-07-09      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.7.0/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.7.0/src/openapi.yaml>`__
2.6.0           2024-03-25      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.6.0/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.6.0/src/openapi.yaml>`__
2.5.0           2024-01-25      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.5.0/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.5.0/src/openapi.yaml>`__
2.4.0           2023-11-09      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.4.0/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.4.0/src/openapi.yaml>`__
2.3.1           2023-09-25      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.3.1/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.3.1/src/openapi.yaml>`__
2.3.0           2023-08-24      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.3.0/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.3.0/src/openapi.yaml>`__
2.2.3           2023-09-25      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.2.3/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.2.3/src/openapi.yaml>`__
2.2.0           2023-06-23      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.2.0/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.2.0/src/openapi.yaml>`__
2.1.1           2023-09-25      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.1.7/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.1.7/src/openapi.yaml>`__
2.1.0           2023-03-03      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.1.0/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.1.0/src/openapi.yaml>`__
2.0.1           2023-09-25      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.0.11/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.0.11/src/openapi.yaml>`__
2.0.0           2022-10-26      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.0.0/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/2.0.0/src/openapi.yaml>`__
1.1.1           2022-06-21      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/1.1.11/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/1.1.11/src/openapi.yaml>`__
1.0.1           2022-05-16      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/1.0.14/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/1.0.14/src/openapi.yaml>`__
1.0.0           2022-03-10      `ReDoc <https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/1.0.0/src/openapi.yaml>`__,
                                `Swagger <https://petstore.swagger.io/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/1.0.0/src/openapi.yaml>`__
==============  ==============  =============================


Open Forms backend
------------------

The Open Forms backend implements the Open Forms API, form submission processing and
various features related to forms happening at runtime.

Changes in the backend may result in changes to the API schema, but this is not a
guarantee. Many things happen "under the hood" that change or improve the API behaviour
in a backwards-compatible way without affecting the API schema.

This means that:

* the Open Forms backend version may be greater than the Open Forms API version (=
  changes did not affect the API schema)
* the backend version is always *at least* the API version - changes affecting the
  schema result in an API version bump.
* Breaking changes result in an major version increase for both backend and API

The matrix below documents which API version ranges are implemented by which Open Forms
backend version.

.. table:: API version offered by backend version
   :widths: auto

   =============== =============
   Backend version API version
   =============== =============
   3.2.x           3.2.y
   3.1.x           3.1.y
   3.0.x           3.0.y
   2.8.x           2.8.y
   =============== =============

End-of-life versions are not listed in this table.
