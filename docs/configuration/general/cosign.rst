.. _configuration_general_cosign:

=========
Cosigning
=========

Open Forms supports form submission flows where a second person needs to cosign the
submission before it gets processed.

Roughly summarized there are two variations for the cosigner:

* the cosign request email contains a link taking the cosigner directly to the right
  page
* the cosign request does not contain a link, but instead it instructs the user how
  to start the cosign process

The global configuration influences which variation is used.

.. tip::

    Read :ref:`the manual (Dutch) <manual_cosign_flow>` to learn more about the flow
    and how to enable this in a form.


Confirmation page configuration
===============================

When the form submitter completes the submission, they get a confirmation page of the
submitted data. The content of this page is configurable. Navigate to **Admin** >
**Configuratie** > **Algemene configuratie**, section
**Formulieren met mede-ondertekenen**:

**Titel mede-ondertekenenbevestigingspagina**
    The main page title displayed for the confirmation page. You can use the template
    variable ``{{ public_reference }}`` here.

**Mede-ondertekenenbevestigingspagina tekst**
    The body text of the confirmation page. This WYSIWYG content supports some template
    expressions too:

    * ``{{ public_reference }}``: the reference number in case the user needs to contact
      your organization. Strongly recommended to include this somewhere.
    * ``{{ cosigner_email }}``: the email address that will receive the cosign request
      email.
    * ``{% cosign_button text="Nu ondertekenen" %}``: a button to start the cosign
      process immediately from the confirmation page. You can provide the button text
      as an argument.

Both Dutch and English variants can be configured to support multi-language forms.

Cosign request email configuration
==================================

The person that needs to cosign the submission will receive an email requesting them to
do this. The content of this email is configurable. Navigate to **Admin** >
**Configuratie** > **Algemene configuratie**, section
**Mede-ondertekenen e-mails**:

**Mede-ondertekenenverzoeksjabloon**
    The content of the cosign request email. This is a template that supports a number
    of expressions:

    * ``{{ form_name }}``: the name/title of the form that requires cosigning
    * ``{{ form_url }}``: a deep link to start the cosign process. If this variable is
      present, the cosign login options are not displayed on the regular form start
      page and the cosigner does not have to enter the code, otherwise both regular and
      cosign login options are displayed. If you omit this link (e.g. for security
      reasons), you should provide clear instructions how the cosigner can find the
      form on your website(s).
    * ``{{ code }}``: the cosign submission code. This code needs to be provided to
      retrieve the submission that needs to be cosigned. If you use deep links, you can
      omit this, as the code is already included in the link.
