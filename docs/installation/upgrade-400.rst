===================================
Upgrade details to Open Forms 4.0.0
===================================

Open Forms 4.0 is a major version release that contains breaking changes.

.. contents:: Jump to
   :depth: 1
   :local:

Removal of legacy OpenID Connect callback endpoints
====================================================

.. note:: Relevant for: devops, identity provider administrators.

The legacy plugin-specific OIDC callback endpoints have been removed. These were
introduced as a migration path in Open Forms 2.x and have been deprecated since then.

The following URL paths no longer exist:

* ``/digid-oidc/callback/``
* ``/digid-machtigen-oidc/callback/``
* ``/eherkenning-oidc/callback/``
* ``/eherkenning-bewindvoering-oidc/callback/``
* ``/org-oidc/callback/``

All OIDC identity providers must now redirect to ``https://<domain>/auth/oidc/callback/``.

The following environment variables are no longer read and can be removed from your
deployment configuration:

* ``USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS``
* ``USE_LEGACY_ORG_OIDC_ENDPOINTS``
* ``USE_LEGACY_OIDC_ENDPOINTS``

