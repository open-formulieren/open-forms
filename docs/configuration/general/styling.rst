.. _configuration_general_styling:

Layout and styling
==================

Via **Admin** > **Configuratie** > **Algemene configuratie**, section
**Organization configuration**, you can configure the look and feel of the forms and html-email.

**Logo**

You can upload a logo to be used in the header here. If no logo is uploaded, a plain
link will be shown. Logo's can be the usual image formats, or an SVG image.

**Main website link**

The main website link is used so the end-user can return to you main website, e.g.
``https://www.gemeente.nl``. Clicking the logo (or link) in the header will return the
end-user to this URL.

**Theme CSS class name**

You can specify a CSS class name to apply to the root ``html`` element here. Typically
you need this if you use an NL Design System design token package which emits the design
tokens under this class name scope.

Example value: ``<gemeente>-theme``.

The `NL DS theme switcher`_ source code contains a list of built in themes and their
class names.

**Theme stylesheet URL**

If your organization publishes their design tokens as a package, you can use the
resulting CSS file here by specifying the URL to the hosted stylesheet.

The `NL DS theme switcher`_ source code contains a list of built in themes with
available hosted stylesheets under the ``href`` key.

.. note::

   If you are specifying an externally hosted stylesheet, then it will be
   blocked by default by the Content-Security-Policy (CSP).

   Navigate to **Admin** > **Configuratie** > **Csp settings** and add an entry to put
   this stylesheet on the allowlist. For the *directive* field, select ``style-src``,
   while the *Waarde* field should contain the (base) URL of the stylesheet, e.g.
   ``https://unpkg.com/@gemeente-denhaag/``.

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
            "color": {
                "value": "#000"
            },
            "background": {
                "value": "#2980b9"
            }
        },
        "footer": {
            "color": {
                "value": "#000"
            },
            "background": {
                "value": "#2980b9"
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
        "layout": {
            "background": {
                "value": "#e6e6e6"
            }
        },
        "color": {
            "link": {
                "value": "#000"
            },
            "link-hover": {
                "value": "fuchsia"
            }
        }
    }


.. _NL DS theme switcher: https://github.com/nl-design-system/themes/blob/main/packages/theme-switcher/src/index.js
.. _style dictionary: https://amzn.github.io/style-dictionary/


Additional design token values examples
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For 'inverted logos' it is possible to change the background colour of the header. The design token values have to be
set to:

.. code-block:: json

    {
      "page-header": {
        "background": {
          "value": "#35a7cc"
        }
      }
    }

This gives:

.. image:: _assets/background-colour.png

For wider logos, it is possible to increase the size with the following design token values:

.. code-block:: json

    {
      "logo-header": {
        "width": {
          "value": "400px"
        },
        "height": {
          "value": "75px"
        }
      }
    }

Which gives:

.. image:: _assets/logo-size.png


Color presets for rich text content component
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Via **Admin** > **Miscellaneous** > **Text editor color presets** you can manage the shared color presets palette used by the rich text editor of the content-component.

You can freely add, change or remove presets to create a collection of consistent colors for use in free text. These are then available here:

.. image:: _assets/color_presets.png

.. note:: Changing the presets doesn't change text with previously applied colors.
