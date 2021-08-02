.. _installation_form_hosting:

============
Form hosting
============

Forms designed with Open Forms would typically be included on some CMS via the
:ref:`Javascript snippet <developers_sdk_embedding>`. However, if this is not possible,
forms can also be accessed through the UI portion of Open Forms.

This section of the documentation documents the various configuration aspects available
to tweak this to your organization needs. It is assumed that open forms is deployed on
a subdomain such as ``open-forms.gemeente.nl``, but other approaches are also possible.


Organization configuration
==========================

Published forms are available via the URL ``https://open-forms.gemeente.nl/<form-slug>``,
which renders the form in a minimal skeleton. The look and feel of this skeleton can be
modified by administrators, to some extent.

Deployment configuration
------------------------

The privacy policy URL in the footer is taken from the ``EHERKENNING_PRIVACY_POLICY``
environment variable, which is configured at deployment time. See
:ref:`installation_config_eherkenning` for more information.


Run-time configuration
----------------------

Via **Admin** > **Configuratie** > **Algemene configuratie**, section
**Organization configuration**, you can configure the look and feel.

**Logo**

You can upload a logo to be used in the header here. If no logo is uploaded, a plain
link will be shown. Logo's can be the usual image formats, or an SVG image.

**Main website link**

The main website link is used so the end-user can return to you main website, e.g.
``https://www.gemeente.nl``. Clicking the logo (or link) in the header will return the
end-user to this URL.

**Design token values**

With the design token values, you can control aspects such as back- and foreground
colors in the skeleton. This is considered advanced usage, as the structure from
`style dictionary`_ is used.

The following design tokens are currently available:

.. code-block:: text

    // anchors
    --of-color-link
    --of-color-link-hover

    // page header
    --of-page-header-background
    --of-page-header-padding-mobile
    --of-page-header-padding-tablet
    --of-page-header-padding-laptop
    --of-page-header-padding-desktop
    --of-logo-header-url  // automatically set if you upload a logo
    --of-logo-header-width
    --of-logo-header-height

    // footer
    --of-footer-background
    --of-footer-color

    // main body
    --of-layout-background

All design tokens are optional and have default values.

The configuration in the admin requires this to be provided as JSON, for example:

.. code-block:: json

    {
        "page-header": {
            "background": {
                "value": "#ffffff"
            }
        },
        "logo-header": {
            "width": {
                "value": "200px"
            },
            "height": {
                "value": "75px"
            }
        },
        "color": {
            "link": {
                "value": "#c00"
            },
            "link-hover": {
                "value": "fuchsia"
            }
        }
    }


.. _style dictionary: https://amzn.github.io/style-dictionary/#/

Configuration with CNAME DNS records
====================================

It's possible to deploy Open Forms as a "SaaS" service - the service provider manages
the installations of Open Forms on their own (internal) domain and organizations can
use this.

Organizations can use CNAME DNS records to point ``https://open-forms.gemeente.nl`` to
the internal host ``open-forms.gemeente.service-provider.nl``, for example. However,
some special care is needed for this.

* The CNAME record(s) MUST be included in the ``ALLOWED_HOSTS``
  :ref:`configuration parameter<installation_environment_config>`.

* The TLS certificate used must include the CNAME domain name.
