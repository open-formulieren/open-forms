.. _manual_templates:

=========
Templates
=========

Open Forms supports templating for various aspects. Templates are basically
text areas that can have customized content using **variables**.

Currently, templates are used for:

* Confirmation emails
* Confirmation pages

There are two ways to customize : **dynamic variables** and
**conditional rendering**. The variables that are available depends on the type
of template and is explained below.

Let's assume these variables are available for a template:

==========  =============
Variable    Value
==========  =============
age         19
gender      M
firstName   John
lastName    Doe
==========  =============

How it works
============

Dynamic variables
-----------------

Using dynamic variables you can have content added to the email that will be
equal to the value of the variable.

To do this you will use ``{{ variable }}`` where ``variable`` is the name of
the value you want to display in the email.

**Example**

.. tabs::

   .. tab:: Template

      .. code:: django

         Hello {{ firstName }} {{ lastName }}!

   .. tab:: Rendered

      .. code:: text

         Hello John Doe!


Conditional rendering
---------------------

Using conditional rendering you can show or hide certain content from the emails
based on certain conditions.

To do this you can use ``{% if variable %}``, ``{% elif variable %}``,
``{% else %}`` and ``{% endif %}`` statements in the email template.
The condition (``variable``) will evalate to either true or false and the text
you want to display is between two of the ``{% %}`` statements. An
``if``-statement needs to closed with an ``endif``-statement.

You can use ``and``, ``or`` to evaluate multiple ``variables`` and you can
compare variables to some value by using various operators: ``==`` (equal),
``!=`` (not equal), ``>`` (greater than) or ``<`` (smaller than). The last two
can only be done with numeric values.

If you don't make a comparison, it will simply check if the ``variable`` is not
empty. Finally, you can check if a variable is empty by adding ``not`` before
the ``variable``: ``{% if not variable %}...``

It is possible to nest conditions for even more customization.

**Example**

.. tabs::

   .. tab:: Template

      .. code:: django

         Hello {% if gender == 'M' %} Mr. {% elif gender == 'F' %} Mrs. {% else %} Mr/Mrs. {% endif %} {{ lastName }}!

      .. code:: django

         {% if age < 21 and firstName %} Hi {{ firstName }} {% else %} Hello {{ lastName }} {% endif %}


   .. tab:: Rendered

      .. code:: text

         Hello Mr. Doe!

      .. code:: text

         Hi Joe!


Confirmation email
==================

The Confirmation email is an optional email that will be sent when a user fills
out a form. It has access to the submission data, filled in by the user, by
accessing the `Property Name` of each element in the form.

The `Property Names` are therefore equal to the ``variables`` that are available
in the template. Typically, these vary per form!

**Special variables or statements**

These are additional variables and statements available to the template.

===================================  ===========================================================================
Element                              Description
===================================  ===========================================================================
``{% summary %}``                    A full summary of all elements marked to show in the email.
``{{ public_reference }}``           The public reference of the submission, e.g. the "zaaknummer".
``{% appointment_information %}``    The information about the appointment to show in the email.
``{% get_appointment_links %}``      Retrieves relevant links about the appointment.
``{% payment_status %}``             If the submission required payment this will either confirm the amount and status, or displays a link where payment can be completed. Displays nothing if submission is free.
===================================  ===========================================================================

**get_appointment_links example**

.. tabs::

   .. tab:: Template

      .. code:: django

         {% get_appointment_links as links %}
         Cancel Appointment: {{ links.cancel_url|urlize }}


   .. tab:: Rendered

      .. code:: text

         Cancel Appointment: http://fake.nl/api/v1/submission-uuid/token/verify/


Confirmation page
=================

The Confirmation page is the page that shows after the submission is completed.
It has access to the submission data, filled in by the user, by accessing the
`Property Name` of each element in the form.

The `Property Names` are therefore equal to the ``variables`` that are available
in the template. Typically, these vary per form!

**Special variables or statements**

These are additional variables and statements available to the template.

========================== ===========================================================================
Element                    Description
========================== ===========================================================================
``{{ public_reference }}`` The public reference of the submission, e.g. the "zaaknummer".
========================== ===========================================================================
