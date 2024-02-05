.. _configuration_dmn_camunda:


Camunda 7
---------

Plugin configuration
^^^^^^^^^^^^^^^^^^^^

In the admin, navigate to **Configuratie** > **Camunda configuration**.

See :ref:`configuration_registration_camunda` for a description of the settings that need to be configured.

This configuration is used both when Camunda is used as a registration backend AND when Camunda is used as the engine to
evaluate decision tables in form logic rules.

However, these permissions are needed in Camunda for evaluating decision definitions:

==============================  =======================================================================================
Permissions within Camunda      Description
==============================  =======================================================================================
List decision definitions       Open Forms must be able to read the available decision definitions to connect a form to a process.
Execute decision definitions    Open Forms must be able to execute decision definitions.
==============================  =======================================================================================


Form configuration
^^^^^^^^^^^^^^^^^^

In the form designer page in the admin, navigate to the **Logic tab**. Then:

#. Add a new logic rule (can be simple or advanced) with a trigger that should determine when the decision table should
   be evaluated.
#. Add a new action and select the value **Evaluate DMN** in the drop down.
#. Click on the 'Configure' button next to the drop down. This opens a modal with more settings to configure.

Action configuration:

#. Select the plugin that should be used to evlauate the decision table, in this case **Camunda 7**.
#. After selecting the plugin, the drop down **Decision Definition ID** will be populated with the decision tables
   available in the configured Camunda instance. Select the desired decision definition to evaluate.
#. If the selected definition has multiple versions, you can select a specific version in the drop down **Decision definition version**.
#. The **Input mapping** table maps Open Forms variables to DMN input variables. Only the data of the variables
   specified in the mapping will be sent to the decision table for evaluation.
#. The **Output mapping** table maps DMN output variables to Open Forms variables. After evaluation of the decision table,
   the logic action will update the specified Open Forms output variable(s) with the values returned by Camunda.
#. Save the settings.

For an example form, see :ref:`examples_camunda`.
