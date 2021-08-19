.. _configuration_email:

=====
Email
=====

Open Forms supports sending emails using customizable email templates.
In addition to static text it's possible to add customized content based
on data the email has access to.

Email Template
==============

There are two ways to customize the sending of emails.
The first is **conditional rendering** and the second is **dynamic variables**.

Conditional Rendering
---------------------

Using conditional rendering you can show or hide certain content from the emails based on certain conditions.

To do this you will use one of ``{% if %}{% endif %}``, ``{% if %}{% else %}{% endif %}``,
``{% if %}{% elif %}{% endif %}``, or
``{% if %}{% elif %}{% else %}{% endif %}`` where you will put conditions within the ``{% if %}`` or ``{% elif %}``
that will evalate to either be true or false and the text you want to display is between two of the ``{% %}`` statements.

It is possible to nest conditions for even more customization.

See below for examples.

Dynamic Variables
-----------------

Using dynamic variables you can have content added to the email that will be equal to the value of the variable.

To do this you will use ``{{ variable }}`` where ``variable`` is the name of the value you want to display in the email.

See below for examples.

Confirmation Email Examples
===========================

The Confirmation Email is an optional email that will be sent when a user fills out a form.
It has access to the submission data done by the user by accessing the `Property Name` of the component
in the form so this is what will be used in the examples but it's important to remember that other emails
will have access to different data and so it's important to be sure your specific email has access to the
data you want to use.

For the examples below we will assume the form has a `firstName` and `lastName` property and both are optional.

Conditional Rendering
---------------------

If you wanted to add an additional message only when the user enters their first name you can do

.. code:: text

   This is the confirmation email.

   {% if firstName %}
   The user has entered their first name.
   {% endif %}


and if the user entered their first name the email will be

.. code:: text

   This is the confirmation email.

   The user has entered their first name.


but if the user did not enter their first name the email will be

.. code:: text

   This is the confirmation email.


You can also use the ``{% else %}`` option to add content in the opposite case.  Consider the email

.. code:: text

   This is the confirmation email.

   {% if firstName %}
   The user has entered their first name.
   {% else %}
   The user did not enter their first name.
   {% endif %}


If the user enters their first name the email will be

.. code:: text

   This is the confirmation email.

   The user has entered their first name.


however if the user does not enter their first name the email will be

.. code:: text

   This is the confirmation email.


   The user did not enter their first name.


You can also use the ``{% elif %}`` option to further customize the content.  Given the email


.. code:: text

   This is the confirmation email.

   {% if firstName %}
   The user has entered their first name.
   {% elif lastName %}
   The user did not enter their first name but entered their last name.
   {% endif %}

If the user enters their first name the email will be

.. code:: text

   This is the confirmation email.

   The user has entered their first name.

but if the user does not enter their first name but does enter their last name the email will be

.. code:: text

   This is the confirmation email.

   The user did not enter their first name but entered their last name.

It's important to note that when using ``{% elif %}`` it will only add the content when the ``{% if %}`` is not
true.  This means in the case that the user enters both their first name and last name then the resulting email
will be

.. code:: text

   This is the confirmation email.

   The user has entered their first name.

because the ``{% if %}`` statement turned out to be true.

It's possible to add as many ``{% elif %}`` statements as you want however remember that only the first
``{% if %}`` or ``{% elif %}`` will be shown.  Given the email

.. code:: text

   This is the confirmation email.

   {% if firstName  %}
   The user has entered their first name.
   {% elif middleName %}
   The user did not enter their first name but entered their middle name.
   {% elif lastName %}
   The user did not enter their first name or middle name but entered their last name.
   {% endif %}

if the user entered their first name the result will be

.. code:: text

   This is the confirmation email.

   The user has entered their first name.

if the user did not enter their first name but entered a middle name the result will be

.. code:: text

   This is the confirmation email.

   The user did not enter their first name but entered their middle name.

if the user did not enter their first name or middle name but entered a last name the result will be

.. code:: text

   This is the confirmation email.

   The user did not enter their first name or middle name but entered their last name.

and finally if the user did not enter any of these the email will simply be

.. code:: text

   This is the confirmation email.

Note that in the case the user enters all their names the resulting email will be

.. code:: text

   This is the confirmation email.

   The user has entered their first name.

or if the user enters their middle name and last name the result will be

.. code:: text

   This is the confirmation email.

   The user did not enter their first name but entered their middle name.

since the first statement to be true is the only one that will be shown.

You can also use the ``{% elif %}`` and ``{% else %}`` together.  Take the example

.. code:: text

   This is the confirmation email.

   {% if firstName  %}
   The user has entered their first name.
   {% elif lastName %}
   The user did not enter their first name but entered their last name.
   {% else %}
   The user did not enter their first name or last name.
   {% endif %}

If the user entered their first name, or both their first name and last name, the result will be

.. code:: text

   This is the confirmation email.

   The user has entered their first name.


If the user did not enter their first name but did enter their last name the result will be

.. code:: text

   This is the confirmation email.

   The user did not enter their first name but entered their last name.

and if the user did not enter either the result will be

.. code:: text

   This is the confirmation email.

   The user did not enter their first name or last name.

It is also possible to compare a variable to a value and only show content if the variable matches a value or
does not match a value.  If you only want to show content when a variable matches a value then you use `==`
within the ``{% if %}`` or ``{% elif %}`` statements and if you only want to show content when a variable
does not match a value you would use `!=`.

Given the example using `==`

.. code:: text

   This is the confirmation email.

   {% if firstName == 'Sam' %}
   The user is named Sam.
   {% endif %}


The message seen if the user enters Sam as their first name will be

.. code:: text

   This is the confirmation email.


   The user is named Sam.


otherwise they will just see

.. code:: text

   This is the confirmation email.



Given the example using `!=`

.. code:: text

   This is the confirmation email.

   {% if firstName != 'Sam' %}
   The user is not named Sam.
   {% endif %}

The user will see

.. code:: text

   This is the confirmation email.

   The user is not named Sam.

if they enter anything other than Sam.  If they enter Sam they will see

.. code:: text

   This is the confirmation email.


Conditional Rendering with Multiple Variables
---------------------------------------------

It is possible to use multiple variables within the ``{% if %}`` or ``{% elif %}`` statement by using either
``or`` or ``and``. When using ``and`` the message will only be shown when all variables have a value.
When using ``or`` the message will be shown as long as one or more of the variables have a value.

Given the example using ``and``

.. code:: text

   This is the confirmation email.

   {% if firstName and lastName %}
   The user has entered their first name and last name.
   {% endif %}


The message will be

.. code:: text

   This is the confirmation email.

   The user has entered their first name and last name.

only when the user has entered both their first name and last name.  If the user enters only their first name,
only their last name, or neither then the message will be

.. code:: text

   This is the confirmation email.


Given the example using ``or``

.. code:: text

   This is the confirmation email.

   {% if firstName or lastName %}
   The user has entered at least one of their names.
   {% endif %}


If the user enters just their first name, just their last name, or both their first name and last name they will see

.. code:: text

   This is the confirmation email.

   The user has entered at least one of their names.


Only if the user does not enter their first name and last name will they see

.. code:: text

   This is the confirmation email.



Nested Conditional Rendering
----------------------------

It is possible to put ``{% if %}`` statements within other ``{% if %}`` or ``{% elif %}`` statements for
more control over the content of the email

Given the example

.. code:: text

   This is the confirmation email.

   {% if firstName %}
   The user is entered their first name.
   {% if firstName == 'Sam' %}
   The first name is Sam.
   {% endif %}
   {% endif %}


If the user enters their first name and their first name is Sam the email will be

.. code:: text

   This is the confirmation email.

   The user is entered their first name.

   The first name is Sam.

If the user enters their first name and but their first name is not Sam the email will be

.. code:: text

   This is the confirmation email.

   The user is entered their first name.


Finally if the user does not enter a first name the email will be

.. code:: text

   This is the confirmation email.


Dynamic Variables
-----------------

It is possible to add variables to the email which will be filled in with the value of the variable
when the email is sent. This can be done using ``{{ }}`` with the variable name between the two brackets.

Given the example

.. code:: text

   This is the confirmation email.

   The first name of the user is {{ firstName }}.


If the user enters Sam as their first name then the email will be

.. code:: text

   This is the confirmation email.

   The first name of the user is Sam.


Note that if the user does not enter a value (in this case a first name) then the variable will be left blank
so the resulting email would be

.. code:: text

   This is the confirmation email.

   The first name of the user is

To prevent this see the example below.


Conditional Rendering with Dynamic Variables
--------------------------------------------

If you want to only render dynamic variables when they exist you can use conditional rendering along with the
dynamic variables.

Given the example

.. code:: text

   This is the confirmation email.

   {% if firstName %}
   The first name of the user is {{ firstName }}.
   {% endif %}


If the user enters Sam as their first name then the resulting email will be

.. code:: text

   This is the confirmation email.

   The user is named Sam.

however if the user does not enter a first name then the email will be

.. code:: text

   This is the confirmation email.
