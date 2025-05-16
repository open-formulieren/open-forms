.. _examples_family_members_prefill:

=========================================================
Form with Family members prefill plugin (Family members)
=========================================================

In this example we create a form which is going to be used to retrieve and prefill
personal data from several sources. For now, we support `Haal Centraal BRP bevragen API`_ 
(Version 2) `StUF-BG`_ (version 3.1).

.. _`Haal Centraal BRP bevragen API`: https://github.com/VNG-Realisatie/Haal-Centraal-BRP-bevragen
.. _`StUF-BG`: https://vng-realisatie.github.io/StUF-BG/


Create the form
================

The steps below describe one form which will retrieve data for both the "partners" and the
"children" of a person. You can adapt this according to your needs and you can configure it
to work for either the "partners" or the "children" for example (configuring only 2 
variables each time).

**Partners**

#. Create a form and select **Demo BSN** login options for the form authentication methods.
    
    .. image:: _assets/family_members_form_authentication.png
       :alt: Screenshot of form authentication.

#. Create a user defined variable with the name **partners** and data type ``array`` (the
   data type should always be an ``array`` otherwise it will not work). This variable will
   be used to hold the retrieved data and can be modified/updated during the submission.
#. Create a user defined variable with the name **partners-initial** and data type ``string``.
   This variable will hold all the necessary configuration for the plugin and the retrieved
   data, but it **should not be modified**, it's meant to be immutable.
#. Click the pencil icon in the "Prefill" column of the **partners-initial** variable. You can 
   now set the options.

    * In the **Plugin** select "Family members". There are now extra options in the modal.
    * For **Type** select partners.
    * For **Data destination form variable**, select the variable we created (**partners**)
    * Click "Save" to save the settings.

      *The above configuration should resemble the screenshot below*:

        .. image:: _assets/family_members_partners_configuration.png
          :alt: Screenshot of mutable variable for partners.

#. Make sure you have the following variables summary:

    .. image:: _assets/family_members_partners_summary.png
      :alt: Screenshot of variables summary.

#. Save the form.

**Children**

#. Repeat steps 2 and 3 from above to add the necessary variables, but this time change
   the variable names to **children** and **children-initial**.
#. Click the pencil icon in the "Prefill" column of the **children-initial** variable. You can 
   now set the options.

    * In the **Plugin** select "Family members". There are now extra options in the modal.
    * For **Type** select children.
    * For **Data destination form variable**, select the variable we created (**children**)
    * Apply any filters that you desire. By default all the children will be retrieved if
      you do not specify/modify any of the available filters.
    * Click "Save" to save the settings.

      *The above configuration should resemble the screenshot below*:

        .. image:: _assets/family_members_children_configuration.png
          :alt: Screenshot of mutable variable for children.

#. Make sure you have the following variables summary:

    .. image:: _assets/family_members_partners_children_summary.png
      :alt: Screenshot of variables summary.

#. Save the form.

