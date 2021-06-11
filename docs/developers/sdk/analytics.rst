.. _developers_sdk_analytics:

==============================
Analytics/tracking integration
==============================

The SDK supports a couple of analytics providers out of the box:

- SiteImprove
- Matomo (formerly known as Piwik)
- Google Analytics

These integrations rely on the typical integrations of each provider which require
Javascript snippets to be embedded.

To be able to use these correctly, the snippets **must** be embedded before the
Open Forms SDK is invoked.

Provider specific documentation
===============================

**SiteImprove**

SiteImprove uses ``window._sz`` to store their tracker.

**Matomo**

Matomo was formerly known as Piwik. The tracker code appears to be identical.

Matomo integration relies on ``window._paq`` being available.

**Google Analytics**

Google Analytics uses the ``window.ga`` global variable.

Adding other providers
======================

We expose the object ``OpenForms.ANALYTICS_PROVIDERS`` in the SDK.

You can add your custom provider to this or even delete integrations, for example:

.. code-block:: js

    OpenForms.ANALYTICS_PROVIDERS.custom = async (location, previousLocation) => {
        const navigatedFrom = previousLocation ?  ` from ${previousLocation.pathname}` : '';
        console.log(`Navigated to ${location.pathname}${from}`);
    };

    ...

    const form = new OpenForms.OpenForm(targetNode, targetNode.dataset);
    form.init();

.. note::

   Ensure you register your provider BEFORE starting/rendering a form to capture page
   changes.
