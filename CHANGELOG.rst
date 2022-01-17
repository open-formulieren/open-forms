=========
Changelog
=========


1.0.0-rc.0 (2022-01-17)
=======================

First release candidate of Open Forms.

Only critical bugs and security issues are considered release blockers. Other
improvements and bug fixes will go into a minor or patch release.

Features
--------

* User-friendly admin interface for staff users to design forms to be filled out by
  end users
* RESTful JSON API to manage/administer forms AND end-user sessions
* Javascript SDK to render forms
    - Built-in into the backend with pages to host forms
    - Embeddable in third party websites
* Authentication module for forms, with plugins:
    - DigiD
    - eHerkenning
    - eIDAS
    - mock/simulation equivalents to try out flows
* Optional Registrations module for forms - form data is sent to a plugin of choice:
    - ZGW APIs - REST/JSON binding with Dutch national standard for "Zaakgericht werken"
      (supports Open Zaak out of the box)
    - StUF-ZKN - StUF/SOAP binding with Dutch national standard for "Zaakgericht werken"
    - Camunda process engine, with detailed variable management options
    - Email - send the data and attachments to a backoffice via email.
    - Microsoft Sharepoint file store
    - Objects API - REST/JSON binding with the Dutch national standard
* Payments module
    - Connect products and pricing information
    - Ogone payment provider with support for multiple accounts
* Appointments module, with plugins for:
    - JCC Afspraken
    - QMatic Appointments
* Prefilling of data through plugins:
    - StUF-BG - StUF/SOAP Dutch national standard for retrieving person details
    - KvK - fetch company information from the Chamber of Commerce APIs
    - HaalCentraal - REST/JSON binding to Dutch national standard for retrieving person details
* GDPR/AVG support built-in
    - mark data fields as sensitive data
    - automatically scheduled and configurable removal of (privacy-sensitive) data
    - automatic logging of data access events
* NLX support
* Extensive dynamic and real-time logic options, based on the data the end-user is
  entering.
* User-administration suitable for your environment
    - Local user database
    - Integration with OpenID Connect (ADFS, Azure AD, KeyCloak...)
    - (Optional) Two-Factor authentication via OTP
    - RBAC with default roles
    - Multi-domain/tenant support
* Internationalization and localization support
    - Dutch
    - English

Meta features
-------------

Open Forms is a project aiming to set an example for the industry by also focusing
on aspects that are not directly visible in the product itself, but rather invest
in the future quality by following best practices.

* Open Source
* Strong focus on security
* Strong focus on codebase quality
* Automated (regression) testing to ensure codebase quality
* Publicly available documentation, both functional and technical
* Automated and public publishing of build artifacts
* TPM audited
* Scalable processing of data
* Containerized deployment, suitable for cloud and on-premise hosting and tuning
