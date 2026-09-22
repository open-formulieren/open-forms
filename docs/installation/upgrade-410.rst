.. _installation_upgrade_410:

===================================
Upgrade details to Open Forms 4.1.0
===================================

Open Forms 4.1 is a backwards compatible feature release, though there are some things
to be aware of.

We've collected the details on this page - topics are sorted with the highest impact
items first.

.. contents:: Jump to
   :depth: 1
   :local:
   :backlinks: none

Data type of date, datetime and time components and variables
=============================================================

.. note:: Relevant for: form designers, registration data processors

Before Open Forms 4.1, the 'empty' value of a ``date``, ``datetime`` and ``time``
component or variable was the empty string (``""``). The reason for this was simply
because it was the behaviour of the Formio.js Javascript library. In Open Forms 4.0,
we no longer depend on this library anywhere, which gives us the freedom to use a better
approach.

Now, the empty value for these components is ``null`` (in JSON/Javascript, ``None`` in
Python). This would affect forms in three possible ways:

* If you use the :ref:`configuration_registration_generic_json` plugin, the values of
  those components/variables would be emitted as ``null`` now, instead of the empty
  string.
* If you use the :ref:`manual_registration_objects_api` registration plugin, the values
  of those components/variables would be emitted as ``null`` now, or, for the legacy
  template-based variant, could mess up your output.
* If you have template logic in content components (for example) based on those values,
  you may see different results.

**We've taken care to avoid breaking changes to existing forms!**

All existing forms with the Generic JSON or Objects API registration plugins are
automatically updated to enable the legacy behaviour - the plugin options have a new
option for this.

New plugins that you add, have this option *disabled* by default. This option will be
removed in Open Forms 5.0. There is no planned release date for 5.0, but it will
definitely not be before September 2027.

For the templates we recommend you verify them - if you have expressions like below,
the behaviour is unchanged:

.. code-block:: django

    {% if someDate %}someDate is not empty{% endif %}
    {% if not someTime %}someTime is empty{% endif %}

for expressions that explicitly compare against the empty value, we recommend you update
them to the above form:

.. code-block:: django

    {% if someDate != '' %}someDate is not empty{% endif %}
    {% if someTime == '' %}someTime is empty{% endif %}

Partners/children component edge case
-------------------------------------

We have identified an edge case where partners or children with partial dates for their
date of birth would lead to problems, as the input validation requires the date of birth
field to be provided. Partial dates are currently not handled and instead changed to the
empty value. Here too, the empty string becomes ``null``, but there's a bigger issue that
needs to be solved as we don't currently believe these forms are usable for people with
partial birthdates.
