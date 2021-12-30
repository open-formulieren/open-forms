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
   Forms SDK. Although Open Forms is bundled with the Open Forms SDK


Gettings started
================

We assume you have access to Open Forms, and have designed some forms in the 
*Admin UI*. To get these forms to show in your CMS you will need 3 things:

1. Have the webmaster of your website 
   :ref:`embed the Open Forms SDK <developers_sdk_embedding>`
2. Inform your Open Forms supplier of your main website domain so it can be
   whitelisted for `CORS (Cross-Origin Resource Sharing)`.
3. :ref:`Provide access to the Open Forms API` so your website can retrieve the
   forms from Open Forms.


.. _`CORS (Cross-Origin Resource Sharing)`: https://developer.mozilla.org/docs/Web/HTTP/CORS


.. _`Provide access to the Open Forms API`:

Access to the Open Forms API
----------------------------

To allow access to the Open Forms API, we need to create a user. This user will
be assigned an API token and a limited set of permissions on what this user
can do with the API token.

1. In the admin, navigate to **Accounts** > **Users**.

2. Click **Add user** and fill in:

   * **Username**: *For example: website-api*
   * **Password**: *Fill in some hard to guess password*

3. Click **Save and continue editing**.

4. Scroll down to the *Permissions* section and make the following changes:

   a. Check "Active".
   b. Make sure "Staff" and "Superuser" are unchecked.
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

10. Sent the *API token* to the webmaster of your website.

    .. image:: _assets/api_token.png


.. warning::

   Granting more permissions than **forms | form | Can view form** will cause
   security risks and can lead to submissions being exposed to the world. The
   API token is not secret but is only used to prevent regular users from 
   seeing all available forms easily.
