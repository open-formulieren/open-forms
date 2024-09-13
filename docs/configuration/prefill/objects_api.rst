.. todo:: This feature is still in development and not ready for production yet.

.. _configuration_prefill_objects_api:

===========
Objects API
===========

The `Objects API`_ stores data records of which the structure and shape are defined by a particular object type
definition in the `Objecttypes API`_. These records can be used to pre-fill form fields if an object reference is
passed when the form is started.

.. note::

   The service may contain sensitive data. It is advised to require DigiD/eHerkenning authentication on the form. You
   should be careful with how you pass the object references to the customers and set up the object type in a way that
   makes authentication checks possible (e.g. by storing the expected BSN or KVK number).

.. _`Objects API`: https://objects-and-objecttypes-api.readthedocs.io/en/latest/
.. _`Objecttypes API`: https://objects-and-objecttypes-api.readthedocs.io/en/latest/


Configuration
=============

1. In Open Forms, navigate to: **Forms**
2. Click **Add form**
3. Define the necessary form details and add the desired components
4. Navigate to: **Variables** tab
5. Navigate to: **User defined** subtab
6. Click **Add variable** and fill in the data from the available options:
   * **Plugin**: Choose the *Objects API* plugin
   * **API Group**: Select the appropriate API group. These API groups should be set up by an administrator, 
   via **Admin** > **Configuration** > **Prefill plugins** > **Objects API** > **Manage API groups**
   * **Objecttype**: Select the expected object type from the dropdown.
   * **Mappings**: Configure which property from the Objects API record needs to be assigned to which form variable. 
   For each form variable you want to pre-fill, add a new mapping. Then, on the left select the desired form variable, 
   and on the right you can specify which property from the object type contains the value.

7. Click **Save**
8. Save the form

The Objects API configuration is now complete.
