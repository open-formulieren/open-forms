.. _security_policy:

Security policy
===============

The development team is strongly committed to responsible reporting and 
disclosure of security-related issues. As such, we’ve adopted and follow a set 
of policies which conform to that ideal and are geared toward allowing us to 
deliver timely security updates to the official distribution of Open Forms.

Reporting security issues
-------------------------

**Short version: please report security issues by emailing 
security@maykinmedia.nl.**

If you discover security issues in Open Forms or related projects under the 
same organization, we request you to disclose these in a *responsible* way by 
mailing to security@maykinmedia.nl.

It is extremely useful if you have a reproducible test case and/or clear steps 
on how to reproduce the vulnerability.

Please do not report security issues on the public Github issue tracker, as 
this makes it visible which exploits exist before a fix is available, 
potentially comprising a lot of unprotected instances.

Once you’ve submitted an issue via email, you should receive an acknowledgment 
from a member of the security team as soon as possible, and depending on the 
action to be taken, you may receive further followup emails.

Timeline of the process
-----------------------

Open Forms community support is provided by `Maykin`_. The community
support team is responsible for the handling of security issues.

1. The recipients of the report first validate if there is indeed a (possible) 
   issue.

2. After validation, we confirm that we received the report and if it is indeed
   a valid issue.

3. We have a private Github repository accessible only to the community support 
   team. In this repository, an issue is created for the vulnerability where 
   the impact and possible solutions are discussed.

4. The next step is to create a (draft) Github security advisory, which is only 
   visible to the repository administrators and community support team. 
   Severity and impact will be established here.

5. If appropriate, we request a `CVE identifier`_ from Github.

6. A patch is implemented, reviewed and tested in a private fork.

7. When the fix is tested and release coordination is done, the fix is merged 
   into the primary repository. The security advisory and release are 
   published. All managed instances should be updated.

8. The release and security vulnerability are communicated to the community. 
   This includes an announcement on `commonground.nl`_.


.. _`CVE identifier`: https://cve.mitre.org/cve/identifiers/
.. _`commonground.nl`: https://commonground.nl
.. _`Maykin`: https://www.maykin.nl

Pentest considerations / security scope
---------------------------------------

We encourage independent pentests and security audits on the Open Forms codebase and
treat all with due care and seriousness. However, we do want to delineate the scope for
potential security findings to make clear which role has particular responsibilities.
Below you will also find a list of commonly reported issues that are often
misunderstood.

Open Forms maintainers
^^^^^^^^^^^^^^^^^^^^^^

The maintainers are responsible for keeping the backend and frontend code secure, which
covers the source code that ends up in the Docker images. This consists of (but is not
necessarily limited to):

* the Python/Django code of the backend.
* the Typescript/Javascript code in the SDK and helper libraries
* the code in third party packages, either by direct ownership, contributing fixes
  upstream or forks/workarounds to defuse security issues.
* ensuring there's documentation detailing the security considerations.

This explicitly excludes any infrastructure tooling or code, such as webserver
configurations, Kubernetes examples and Docker compose setups. While the maintainers do
their best to provide secure reference setups or examples, we cannot commit to bringing
these within the scope of our security policy. The primary security responsibility for
such artifacts lies with the Service Provider (see below). However, suggestions for
improvements are welcome - these can be submitted as regular feature requests/Github
issues.

See the `project governance <https://github.com/open-formulieren/open-forms/blob/main/PROJECT_GOVERNANCE.md>`_
details for more details about the maintainers role.

Service providers
^^^^^^^^^^^^^^^^^

Open Forms is open source and under the terms of source code's license, any party is
free to offer Open Forms to their customers as a (managed) service.  Anyone operating
any part of the software contained in the ``open-formulieren`` Github organization is a
"service provider".

The maintainers expect service providers to have deep knowledge of the software and how
to deploy it securely, among other things by keeping up to date with the latest security
considerations listed in the documentation, for example in the
:ref:`securing an installation <installation_security>` docs. Furthermore, they should
have a thorough understanding of web-application security risks and threat-mitigation
mechanisms.

The service providers are responsible for all components that sit between the end-user's
browser and the container images published by the maintainers. Amongst others, this
covers:

* TLS protection with strong configuration.
* (Web application) firewall configuration and maintenance/tuning.
* (D)DoS protections.
* CORS policies.
* Reverse proxy / load balancer configuration, with emphasis on HTTP headers that improve
  security.
* Run-time configuration of the containers through environment variables.
* Deploying and configuring anti-virus.
* Server/Kubernetes cluster security.
* Configuring single sign-on for staff users / user account management.

The Content-Security-Policy (CSP) configuration deserves an explicit mention here as the
scope is covered by both maintainers and service providers. It requires fine-grained
management which necessitates that the application itself provides controls and manages
it to a certain extent. Additional relaxation options are exposed to service providers
through environment variables.

Finally, service providers are also responsible for training/assisting
functional/technical administrators who manage technical configuration in the admin
interface, such as connections to external API's.

Form designers
^^^^^^^^^^^^^^

A Form designer is any person from within an organization that creates and maintains
forms in Open Forms through the visual interface in the admin UI.

Form designers should be mindful of the features offered by the application to restrict
and validate user input and use these unless there is a compelling reason not to, so
that untrusted user input is validated and sanitized for the context in which it will
be processed by downstream systems. Some examples:

* use the correct form component type, e.g. postcode, BSN, date... that already performs
  a lot of input validation.
* configure an appropriate maximum file size for file uploads.
* restrict the file upload extensions/file types to only the relevant types.
* limit the maximum length of text fields if the size of expected data is known.
* configure regular expression patterns in text fields where appropriate.
* take care to not leak sensitive information in user-facing templates.
* configure appropriate submission retention policies.
* only enable outgoing request logging when actively troubleshooting an issue.

Not security issues
^^^^^^^^^^^^^^^^^^^

It's possible to upload viruses (EICAR test file)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open Forms has virus scanning with ClamAV as opt-in feature. Service providers must
provide the ClamAV service and ensure it's configured and enabled in Open Forms.

Partial validation when submitting a form step
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Security researchers often discover that you can bypass client-side validation of
required fields and proceed to the next step in the form.

This finding is accurate, but is intended behavior rather than a bug - it is necessary
to support the "pause-and-resume-later" feature of a form where partial answers of a
(long) step can be saved without having to start over for the whole step.

Before the submission is finalized, every step is validated again by the backend. This
includes validation of all fields, including the ``validate.required`` configuration of
components. This prevents an incomplete or invalid (according to the validation rules)
form submission being passed to downstream systems for further processing.

Additionally, Open Forms API endpoints are intended to be called/read by untrusted users,
and we take care to not expose any internal details that are not absolutely necessary
for the functioning of the form.

Use of session cookies
~~~~~~~~~~~~~~~~~~~~~~

The use of session cookies is deliberate, as it is a battle tested and simple setup.
Session cookies however open up a CSRF attack vector, which can be particular risky in
Django applications that use django-restframework.

Open Forms uses custom authentication/authorization mechanisms that enforce the
validation of the CSRF token and cookie even in these "anonymous" contexts to protect
against CSRF attacks.

Use of ``SameSite=None`` in cookies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default Open Forms configuration is a compromise between security and features. The
application is built with embedding of forms on third party websites in mind, which
requires the cookie to be sent in cross-site requests.

If the service provider knows that embedding will never be used, they should follow the
documentation at :ref:`installation_security` to harden the installation - the
``SameSite`` attribute can be configured through environment variables.

Submission pausing/resuming can potentially be hijacked
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open Forms supports suspending a form submission so that the submission data up until that
point is saved to the database, and the user can enter their email address where they
receive a magic link to resume the submission where they left of. There are often
concerns about someone else being able to access the submission through this mechanism.

The maintainers are aware that this is a part of the application that carries higher
risk. That is mitigated in depth with a number of protections:

* the magic link contains an unguessable cryptographically secure token.
* the magic link has an expiration encoded in it - it's only valid for a limited number
  of days (configurable with environment variables). Tampering with the encoded duration
  invalidates the token.
* the token generation takes properties of the submission into account. Suspending the
  submission again or completing it, invalidates any previously issued magic links.

Additionally, there are concerns that if you can guess the UUID of a submission, you can
get the resume link sent to the email address of an attacker. This is protected by two
main mechanisms:

* you can only suspend a submission that belongs to your session - even if an attacker
  can guess your submission UUID, they need your session cookie/ID and CSRF token/cookie.
  Idle sessions automatically expire after 15 minutes (hard limit).
* upon resuming the submission, you must re-authenticate the same way that the
  submission was authenticated to start.

Submission status URL / PDF download URL requires no authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the user completes the submission, background processing starts and they see a
loader while that's happening. The frontend uses a magic endpoint to retrieve the
processing status periodically. Once processing is complete, the confirmation page is
shown with a link to download the confirmation PDF, which again uses a magic link.

These magic links can (by design) accessed by anyone that has the link. The link is
never transmitted via other channels (like email) - it's only exchanged between the
frontend code and the backend API.

The magic links automatically expire - the duration of validity can be configured with
environment variables. The links contain a cryptographically secure token to make them
unguessable.

Being able to copy and paste the PDF link is a feature, e.g. to let the partner of the
user also download the document. This requires an active effort from the user to share
the link with others.
