.. _configuration_general_analytics:

Analytics
=========

By default, Open Forms does not enable any form of external data analytics 
tools. However, you can enable these tools within Open Forms. Below, we list
the integration possibilities within Open Forms.

.. warning::

    If you enable external data analytics tools, you **need** to setup a proper
    :ref:`cookie policy <configuration_general_cookies>` in accordance with
    the `GDPR`_ and your local privacy authority.

    Also, these data analytics tools will **only work** if the user allowed 
    these cookies. If you do not setup cookies, these tools will simply not 
    work because the user never allowed their cookies.

.. _`GDPR`: https://gdpr.eu/


Supported tools
---------------

The following tools are supported out of the box with Open Forms. You can 
configure them in the **General configuration**.

.. image:: _assets/admin_analytics_settings.png


* `Google Analytics <https://marketingplatform.google.com/about/analytics/>`__
* `Google Tag Manager <https://marketingplatform.google.com/about/tag-manager/>`__ 
* `Matomo (Piwik) <https://matomo.org/>`__ (cloud and on-premise support)
* `SiteImprove <https://siteimprove.com/en/analytics/>`__

.. note::

    Matomo was formerly known as Piwik. Do not confuse Piwik with Piwik PRO, 
    which is a different product from a different company. Currently, there is
    no support for Piwik PRO.
