.. _configuration_registration_camunda:

=======
Camunda
=======

Camunda_ is a process engine using BPM models. Open Forms supports Camunda 7.x

.. note::

    This service requires a connection to an external Camunda instance, offered
    or maintained by a service provider.

What does the Open Forms administator need?
===========================================

The values for these parameters should be provided to the Open Forms
administrator by the service provider.

============================  =======================================================================================
Parameter                     Description
============================  =======================================================================================
**Camunda instance**
Version                       7.x. 7.16 is actively tested, 7.12 and up are expected to work. Other 7.x versions *should* work.
REST API root endpoint        The Camunda instance must expose its REST API on a URL reachable by Open Forms.
Username                      Username for the REST API user (Basic Auth)
Password                      Password for the REST API user (Basic Auth)
**Permissions**
List process definitions      Open Forms must be able to read the available process definitions to connect a form to a process.
Start process instances       Open Forms must be able to start process instances of the selected process definition(s).
============================  =======================================================================================

What does the service provider need?
====================================

The values for these parameters should be provided to the service provider by
the Open Forms administrator.

============================  =======================================================================================
Parameter                     Description
============================  =======================================================================================
**Security**
IP address                    The IP address of the Open Forms server (optional, for whitelisting).
============================  =======================================================================================

Configuration
=============

1. In Open Forms, navigate to: **Configuration** > **Camunda configuration**
2. In the **Camunda root** field, fill out the protocol and domein (and optional port)
   of the API root.
3. In the **REST api path** field, fill out the path of the REST API root, relative to
   the Camunda root URL.
4. Under **Auth**, fill out the username and password. Note that the password is never
   displayed, even if filled out correctly.

The configuration page tests the connection, if any mistakes are made, you will receive
validation errors.

Technical
=========

================  ===================
Camunda version   Test status
================  ===================
7.12              Manually verified
7.13              Untested
7.14              Untested
7.15              Untested
7.16              Tested in CI
================  ===================

.. _Camunda: https://camunda.com/
