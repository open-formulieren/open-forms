.. _configuration_prefill_family_members:

==============
Family members
==============

The **Family members** prefill plugin stores data records for partners and children based
on a person's BSN. These records can be used to pre-fill form variables if a set of specific 
variables is configured accordingly.

Currently, we support only `Haal Centraal BRP bevragen API`_ (v2) and `StUF-BG`_ (version 3.1).

.. note::

   The service contains sensitive/personally identifiable information. It is required to
   use authentication on the form, as this information is used to retrieve personal information
   about people.

Configuration
=============

#. First thing you need is to configure the desired service from which the data will be
   retrieved. This can be one of the following:

   * For `Haal Centraal BRP bevragen API`_ you should configure a relevant service 
     (see :doc:`configuration guide <haal_centraal>` for details) and it's important to 
     set the version to ``BRP Personen Bevragen 2.0``.

   * For `StUF-BG`_ you should configure a relevant service (see :doc:`configuration guide <stuf_bg>` for details).

#. Next step is to navigate to: **Configuration** > **General configuration** > **Plugin configuration**.
#. Select the source which will be used to retrieve the data.
#. Click **Save**.
#. The prefill configuration is ready.

How it works
============

As mentioned above, the Family members pre-fill plugin works in two ways according to the
source that has been selected. For both sources the user has to follow the same steps in
order to configure/enable the plugin.

In order to enable the plugin you need to complete the configuration above. Next step is
to add the relevant component and a **user defined** form variable:

  * The component you need to add to the form is either "partners" or "children" from
    the special fields. This will automatically create a form variable of data type ``array``.
    This form variable will hold the data each time something is updated (`mutable` variable).

  * Next step is to add a user defined variable that we call `immutable` since this is not 
    intended for modifications/updates. This is used for configuring the plugin and holding
    the original retrieved data. The data of this should not be modified because it's used
    as a prototype for the initial data we get from the selected service.

.. note::
   
   You can see the configuration of these two variables in detail in the :ref:`Family members form guide <examples_family_members_prefill>`

As a conclusion, you always need two variables (one from the component's creation and one
user defined) for storing data for the partners and two variables for the children. You 
can configure a form that handles both the partners and the children so in this case you
need four variables (two for each type of person).

Technical
=========

=================== ==================
API                 Supported versions
=================== ==================
BRP bevragen API    2.0
=================== ==================

================  ===================
Service           Supported versions
================  ===================
StUF-BG           3.10  (``npsLv01``)
================  ===================


.. _`Haal Centraal BRP bevragen API`: https://github.com/VNG-Realisatie/Haal-Centraal-BRP-bevragen
.. _`StUF-BG`: https://vng-realisatie.github.io/StUF-BG/
