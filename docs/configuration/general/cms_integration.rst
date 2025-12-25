.. _configuration_general_cms_integration:

===============
CMS integration
===============

Open Forms forms can be used with any CMS, to show forms on the domain of your 
main website.

**Open Forms** includes the *Open Forms Admin UI*, where forms can be 
designed, and the *Open Forms API* through which the designed forms can be 
retrieved and filled in forms can be submitted.

The **Open Forms SDK** is a separate library that can render forms retrieved
via the *Open Forms API*. This library can typically be used if you plan on
integrating Open Forms forms in your own CMS.

.. note::
   
   You will always need a hosted Open Forms instance somewhere to use the Open 
   Forms SDK. If you are using the generic form page bundled with Open Forms 
   instead of integrating forms in your CMS, you do not need the Open Forms 
   SDK.


Getting started
===============

We assume you have access to Open Forms, and have designed some forms in the 
*Admin UI*. To get these forms to show in your CMS you will need 3 things:

1. Have the webmaster of your website 
   :ref:`embed the Open Forms SDK <developers_embedding>`. For each form
   you want to integrate in the CMS, the webmaster will also need the UUID of
   the form as shown in the Open Forms *Admin UI*.
2. Inform your Open Forms supplier of your main website domain so it can be
   whitelisted for `CORS (Cross-Origin Resource Sharing)`.
3. Optionally, :ref:`provide access to the Open Forms API` so your CMS can 
   retrieve the list of forms from Open Forms. This way, you do not have to 
   pass individual form UUIDs to your webmaster.


.. _`CORS (Cross-Origin Resource Sharing)`: https://developer.mozilla.org/docs/Web/HTTP/CORS


.. _`provide access to the Open Forms API`:

Access to the Open Forms API
----------------------------

Providing access to the Open Forms API allows a CMS to integrate nicely with
with Open Forms. For example, the CMS can show a list of forms that are 
available and allows you to add an Open Forms form to a page in your CMS.

.. note:: This is an optional feature to ease the use of Open Forms for content 
   managers. It does however, require some development work on your end.

To allow access to the Open Forms API, we need to create a user. This user will
be assigned an API token and a limited set of permissions on what this user
can do with the API token.

1. In the admin, navigate to **Accounts** > **Users**.

2. Click **Add user** and fill in:

   * **Username**: *For example: website-api*
   * **Password**: *Fill in some hard to guess password*

3. Click **Save and continue editing**.

4. Scroll down to the *Permissions* section and make the following changes:

   a. Check **Active**.
   b. Make sure **Staff** and **Superuser** are unchecked.
   c. In **User permissions**, find and select 
      **forms | form | Can view form**. Make sure it's shown as only entry on 
      the right side.

   .. image:: _assets/api_user.png

5. Click **Save**.

6. Navigate to **Accounts** > **Tokens**.

7. Click **Add token** and fill in:

   * **User**: *Select the user you created above*

8. Click **Save**.

9. Copy the characters below the **Key** column. This is the *API token*.

10. Send the *API token* to the webmaster or supplier of your website.

    .. image:: _assets/api_token.png

    This *API token* needs to be provided when communicating with the Open 
    Forms API, as detailed in the `Open API Specification`_. For example, to 
    get a list of available forms:

    .. code:: http

       GET /api/v2/forms  HTTP/1.0
       Authorization: Token 3f084e81b3d68d52a5f9d1712e3d0eda27d2129f

    Additional endpoints of interest:

    * ``/api/v2/public/categories`` - list of form categories
    * ``/api/v2/public/categories/{uuid}`` - details of a single form category

    For the API documentation, see :ref:`developers_versioning_api`.

.. warning::

   Granting more permissions than **forms | form | Can view form** will cause
   security risks and can lead to submissions being exposed to the world.


.. _`Open API Specification`: https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-formulieren/open-forms/main/src/openapi.yaml
