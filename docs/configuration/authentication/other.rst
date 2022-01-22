.. _configuration_authentication_other:

=====================
Other authentications
=====================

.. warning::
    
    These plugins are mostly for testing and development purposes and should
    not be used in production.

To test various aspects of authentication for a form, we include several 
plugins to simulate or test authentication. No configuration is required for
the plugins but the need to be enabled in the development settings.

* **Demo BSN**: Allows an admin to login using any BSN number. The form behaves
  as if an actual BSN was returned, as if the user logged in with DigiD.
* **Demo KvK-number**: Allows an admin to login using any KvK-number. The form
  behavves as if an actual KvK-number was returned, as if the user logged in 
  using eHerkenning.
* **Uitval simulatie (test)**: Simulates an generic authentication plugin that
  fails.
* **BSN Uitval (test)**: Simulates an authentication plugin that is expected
  to return a BSN but returns an invalid response instead.
* **KvK Uitval (test)**: Simulates an authentication plugin that is expected
  to return a KvK-number but returns an invalid response instead.
* **DigiD simulatie**: For demo purposes, a DigiD-like login experience but
  the username acts as the BSN-number. Any BSN-number that is used as username
  is passed to the form as if it was provided as BSN-number from DigiD.
