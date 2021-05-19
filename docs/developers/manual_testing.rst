.. _developers_manual_testing:

==============
Manual testing
==============

Certain (UI) functionalities are not easily tested automatically. To prevent regressions,
the following test scenario's should be checked for a new build.

Form builder tests
==================

The form builder is the core tool used by content editors to design the forms to be
rendered by the SDK. It uses formio.js under the hood, with custom field types added.
These custom field types should be verified to be functional.

1. Navigate to the admin. Then go to **Formulieren > Form definitions**. Next, click
   **form definition toevoegen**.

2. Verify that the following components are present under the label **Configuration**,
   and can be added to the form builder by dragging it to the right:

    * Section *Formuliervelden*:

        * Text Field
        * IBAN Field
        * Text Area
        * Number
        * Checkbox
        * Select boxes
        * Select
        * Currency
        * Radio

    * Section *Opmaak*

        * Content
        * Field Set

    * Section *Basisregistratie Personen*

        * Gezinsleden
