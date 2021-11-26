.. _developers_architecture:

Architecture
============

Open Forms is API-first and embraces the separation of concerns lined out by the
5-layers principle of `Common Ground`_.

There, Open Forms as a product consists of two separate codebases:

* Open Forms ("the backend")
* Open Forms SDK ("the frontend")

These codebases complement each other to bring the full functionality of dynamic forms
to the end user.


Open Forms
----------

Repository: https://github.com/open-formulieren/open-forms/

The backend is essentially what runs on a server. It stores the form-related data in a
backing database and performs the majority of the processing. The following features are
implemented in the backend:

* Administrative interface for content editors, system configuration and submission state
  introspection.
* RESTful API for the SDK and other clients to call to consume or mutate (submission)
  data
* A number of modules implementing specific functionality, often with various plugins to
  connect with third-party systems centered around a certain functionality
* Asynchronous background processing queue, jobs and workers with automatic
  retry-functionality
* A basic but customizable UI wrapper around the SDK to present forms to end-users

.. todo:: add image that Joeri used for pitch

Logically, Open Forms is made up of a core and various modules which are to a lesser or
higher degree coupled with each other.

Core
~~~~

Core functionality is considered functionality that does not or very loosely tie in to
particular modules. It is functionality that has meaning on its own without dependencies,
but is enriched by modules, such as:

* Accounts: administrative user accounts, roles and permissions
* Forms: form definitions, forms and form steps
* Submissions: filled out forms by end-users, uploaded attachments and processing information
* Products: product information offered via forms
* General purpose utilities

**Modules**

Modules focus on specific useful functionalities, often offering choices in which plugin
to use to implement said functionality. Usually you can even use a different plugin per
form, offering a wide range of flexibility.

* Authentication: before a form can be started, often the end-user must authenticate
  with a particular identity provider
* Registrations: once the form is submitted, the data can be sent to a registration
  backend for further processing
* Payments: product-related forms often require payment - this module integrates with
  payment providers
* Appointments: appointments created by end-user can be registered and managed in third
  party appointment systems
* Prefill: once authenticated, form fields can be pre-filled from various third party
  systems

The core and modules are documented in-depth in
the :ref:`the backend section <developers_backend_index>`.


SDK
---

Repository: https://github.com/open-formulieren/open-forms-sdk/

The frontend is responsible for presenting forms to end-users and take them through the
process of successfully filling out a form designed by a content editor.

The SDK consumes the API served by the backend and has no knowledge of specific plugins
implemented in the backend.

The technical documentation can be found in :ref:`another section <developers_sdk_index>`.

.. _Common Ground: https://commonground.nl
