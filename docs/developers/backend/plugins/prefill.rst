.. _developers_backend_plugins_prefill:

=======
Prefill
=======

The prefill module is invoked during the submission creation when an end-user starts
the form submission, after logging in. For forms without login, most prefill plugins
skip their execution. Typically the user identification (obtained through
:ref:`developers_backend_plugins_authentication`) is used to look up additional details
in an external API or service.

For each form field (or variable), the form builder can configure which plugin to use
to prefill it, and with which attribute. More complex configurations are possible,
depending on the selected plugin.

.. contents::
   :local:
   :depth: 2
   :backlinks: none

Python API
==========

There are currently two main modes of prefill configuration:

* simple plugin + attribute, typically stored in the Formio component definition
* advanced plugin + plugin options, for prefill behaviour that doesn't fit in a formio
  component

We're planning to rework the simple system into the more advanced system so that there's
only a single mode that covers all needs.

Module interface
----------------

.. automodule:: openforms.prefill.service
   :members:

Plugin interface
----------------

Prefill plugins must inherit from the base plugin.

**Plugin base API**

.. automodule:: openforms.prefill.base
   :members:

Available implementations
=========================

Customer interactions
---------------------

Fetch and update customer profile details from
`Open Klant <https://maykin.nl/nl/producten/open-klant/>`_.

Demo
----

Demo plugin that prefills form fields with random data.

eIDAS
-----

Extract user or company details from the European authentication means.

Family members
--------------

Look up partner and/or children details of the authenticated user, using their BSN
and "Haal Centraal BRP Personen bevragen" or StUF-BG.

Haal Centraal BRP Personen bevragen
-----------------------------------

Using the BSN of the authenticated user, fetch additional personal details, e.g. the
name(s), date of birth...

KvK (Chamber of Commerce)
-------------------------

Look up company details based on the Chamber of Commerce number of the authenticated
company.

Objects API
-----------

Given an Object reference at the start of a form, look up the object details and extract
the relevant information for further use in the form submission. Object ownership is
by default validated against the identification of the authenticated user.

StUF-BG
-------

Using the BSN of the authenticated user, fetch additional personal details, e.g. the
name(s), date of birth...

Suwinet
-------

.. todo:: add description

Yivi
----

`Yivi <https://yivi.app/>`_ can both authenticate a user and act as a digital wallet
to provide additional personal or company details during the login process.
