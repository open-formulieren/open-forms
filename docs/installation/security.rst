.. _installation_security:

===================================
Securing an Open Forms installation
===================================

.. note:: The intended audience for this documentation is DevOps engineers

The default configuration options of Open Forms aim to provide a secure setup which
enables all functionalities. We provide sufficient room to tighten this security if
desired, which may come at the cost of disabling certain features, or to loosen the
security for quick-and-dirty exploration installations.

We recommend reading and understanding this document before performing penetration
tests. The contents have been composed based on pentest reports we have received.

.. warning:: Do not blindly take the configuration from the ``docker-compose.yml`` file
   - it is not suitable for real deployments, only for exploration.

Throughout this document, certain configuration options will be referenced. The full
list of configuration options and how to apply them is documented in the
:ref:`installation_environment_config`.

Cross-Origin Resource Sharing (CORS)
====================================

If you want to :ref:`embed forms<developers_embedding>` on trusted third-party
domains (for example on "products and services" pages), then you need to configure
`CORS`_ appropriately. The embedded form makes calls to the API endpoints on the domain
where Open Forms is deployed.

It is important to understand that CORS is not a security mechanism by itself, but
rather a feature to allow exceptions through in an existing security feature of
browsers (such as embedding forms).

If you don't plan to use this embedding feature, you don't need CORS. By default, Open
Forms is configured to block CORS.

Definitions
-----------

Third-party domain
    Domains different from the one where Open Forms is hosted which are under your
    organization's control or have permission to serve content for your organization.

Trusted domain
    A domain that is allowed to interact with your Open Forms instance by your
    organization - the counterpart of a malicious domain.

I want to embed forms
---------------------

If you want to embed forms on third-party domains, these domains need to be explicitly
added to the allow-list for CORS-requests, otherwise the browser will prevent these
requests from working and the embedded forms will be broken.

We recommend using the explicit allowlist ``CORS_ALLOWED_ORIGINS`` - specified as a
comma-separated list of trusted domains, e.g.:

.. code-block:: bash

    CORS_ALLOWED_ORIGINS=https://external.example.com,https://external2.example.com

Alternatively, you can use regular expression patterns if you need to allow many
domains:

.. code-block:: bash

    CORS_ALLOWED_ORIGIN_REGEXES=^https://\w+\.example\.com$

In that case, you also need to specify ``CSRF_TRUSTED_ORIGINS`` with an explicit list
of all domains (this setting does not accept regular expressions). If you use the
``CORS_ALLOWED_ORIGINS`` setting, ``CSRF_TRUSTED_ORIGINS`` will be automatically
populated from that setting.

We advise **against** setting ``CORS_ALLOW_ALL_ORIGINS=True``, as this allows malicious
domains to make CORS requests - this could then be exploited if there are
`XSS`_ vulnerabilities.

.. note:: A misconfigured ``CORS_ALLOW_ALL_ORIGINS`` setting is by far the most common
   and serious "vulnerability" reported in pentests.

I don't want to embed forms
---------------------------

If you don't intend on embedding forms on third party domains, you can enhance the
security by configuring the ``SameSite`` (see `SameSite on MDN`_) property of cookies:

.. code-block:: bash

    SESSION_COOKIE_SAMESITE=Strict
    CSRF_COOKIE_SAMESITE=Strict
    LANGUAGE_COOKIE_SAMESITE=Strict

Alternatively, a value of ``Lax`` instead of ``Strict`` is also possibly - this is
the current browser default.

Open Forms defaults to ``None`` in HTTPS contexts to allow embedding/CORS.

.. note:: These settings do not apply to non-HTTPS contexts.

File uploads
============

.. note:: This section is informational - you can not configure this behaviour.

Open Forms processes file-uploads in two stages:

1. A temporary upload - the file extension and mimetype are validated against each
   other. At this stage, "unexpected" file types can be uploaded, such as ``.exe``
   files.

2. Relating temporary uploads to a form submission step. At this stage, the file type
   is validated against the configured allowed filetypes on the form field. A ``.exe``
   file will typically be rejected at this stage and the end-user receives a validation
   error.

Temporary file uploads cannot be downloaded by organization employees, so even though
potentially harmful files can be uploaded to Open Forms, there is no way for these files
to end up on employee systems.

Only validated uploads can be downloaded by employees.

Finally, temporary file uploads that have not been related to a form step submission are
automatically pruned after ``TEMPORARY_UPLOADS_REMOVED_AFTER_DAYS`` (currently the
default is 2 days).

.. seealso::

    * :ref:`Webserver configuration for file-uploads. <installation_file_uploads>`

    * :ref:`Reference documentation of the upload process. <developers_backend_file_uploads>`


Validating redirects
====================

Open redirects are a security vulnerability that could possibly send users from a
trusted domain (typically a form) to a malicious website. Because the user is
automatically redirected by the Open Forms backend, they should be able to trust the
domains they are redirected to.

Open Forms mechanisms to prevent open redirects are two-fold.

Internal redirects
------------------

Certain redirects are internal to URLs on our own application. These redirects typically
do not contain host information, but just the path - e.g. ``/admin/login/`` instead
of ``https://example.com/admin/login``.

Other redirects are validated against the current host and allowed hosts - as long as
the redirect is to the same domain you came from or a domain listed in ``ALLOWED_HOSTS``,
it is considered "safe".

External redirects
------------------

A number of redirects are external - they go to a domain that is outside of our own
control, such as (but not limited to):

* third-party domains embedding forms
* payment providers
* authentication/identity providers

Redirects that may be user-input are validated against the CORS-configuration - i.e.
if a domain is configured on the CORS allow-list, then redirects to that domain are
allowed, otherwise they are blocked.

.. warning:: ``CORS_ALLOW_ALL_ORIGINS=True`` is a common misconfiguration that
   essentially makes your installation vulnerable to open redirects.

Preventing access to internal URLs
==================================

A number of URLs are intended to be used by employees/staff and should not be publicly
accessible. Rather than complicating the application with these non-functionals, Open
Forms delegates this responsibility to the infrastructure.

You should configure your webserver/firewall to allow access to the internal URLs
only to trusted clients, e.g. by using IP-allowlists.

The internal URLs are:

* ``/admin/*`` - the admin interface where forms are designed and site-wide configuration
  is managed
* ``/api/v2/docs/`` and ``/api/docs/`` expose the technical API documentation. While no
  sensitive data is exposed in here, your organization may opt to not publicly expose
  this information (even though this documentation is publicly available on Github anyway).

Two-factor auth
===============

The admin interface requires two-factor authentication using OTP (using Microsoft or
Google's Authenticator app) or hardware tokens such as YubiKeys. If you use a single
sign on solution (e.g. Keycloak OIDC, Azure AD OIDC...), it is assumed that the second
factor is enforced on those products and staff users do not need to provide an
additional second factor in Open Forms.

.. _installation_config_webserver:

Webserver configuration
=======================

Permissions policy
------------------

The ``Permissions-Policy`` response header controls which browser feature may be used/
requested by Open Forms. For privacy and security reasons you may want to disable most
of the features, except the following:

* ``camera=(self)``: file upload components with images may use the camera feature to
  take pictures for upload.
* ``geolocation=(self)``: when using the map component, Open Forms will try to get the
  geolocation from the browser.

SSL/TLS
-------

TLS needs to be configured on the infrastructure (i.e. your webserver and/or ingress
solution if you use Kubernetes).

DigiD requires TLSv1.2 or higher - older versions are not allowed and will fail your
DigiD audit, so please ensure your infrastructure enforces these requirements.

We recommend you to apply the ``Strict-Transport-Security`` response header to instruct
browsers to only connect over HTTPS to Open Forms, preferably with the
``includeSubdomains`` directive.

Managing SSL certificates is outside of the scope of the application - Open Forms should
only be deployed behind a secured reverse proxy and/or load balancer.

.. _CORS: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
.. _XSS: https://developer.mozilla.org/en-US/docs/Glossary/Cross-site_scripting
.. _SameSite on MDN: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite
