.. _configuration_dmn_camunda:


Camunda 7
---------

Camunda Admin
^^^^^^^^^^^^^

In order to deploy a new decision definition and then evaluate it, users should be created with:

- The **CREATE** authorization for the **Deployment** resource.
- The **READ** and **CREATE_INSTANCE** authorization for the **Decision Definition**.

To configure this, log in into the Camunda Admin with a user with admin rights. Then, follow the following instructions:

#. **Creating groups**

   Click on **Groups** on the navigation bar and click on **Create new group +**. Fill in ``Deployers`` as the **Group ID**
   and then fill the other required fields. Then click on **Create new group**.

   Create then another group with **Group ID** ``DecisionTableEvaluators``.

#. **Creating users**

   Click on **Users** on the navigation bar and click on **Add user +**. Fill in ``deployer`` as the **UserID** and then
   fill the other required fields. Then click on **+ Create new user**.

   Create then another user with **UserID** ``openForms``.

   Now that the users are created, they need to be added to the right group. Click on the user ``deployer`` and then on
   the left hand side navigate to **Groups**. Click on **Add to a group** and add the user to the ``Deployers`` group.

   Then, go back to the Users page and click on the user ``openForms``. Add this user to the group ``DecisionTableEvaluators``.

#. **Updating authorizations**

   Click on **Authorizations** on the navigation bar.

   On the left hand side, navigate to **Deployment**. Click on **+ Create new authorization**. In the **User / Group**
   column, fill in ``Deployers``. Click on the check icon to save.

   On the left hand side, navigate to **Decision Definition**. Click on **+ Create new authorization**. In the **User / Group**
   column, fill in ``DecisionTableEvaluators``. Click on the pen icon to update the permissions. Uncheck everything, except
   **READ** and **CREATE_INSTANCE**. Click on the check icon to save.

Now, the credentials for the user ``deployer`` can be used in the Camunda modeller when deploying a decision definition.
The credentials for the user ``openForms`` can be used in the Open Forms admin under the
**Configuration > Camunda Configuration** page.

Plugin configuration
^^^^^^^^^^^^^^^^^^^^

In the admin, navigate to **Configuratie** > **Camunda configuration**.

See :ref:`configuration_registration_camunda` for a description of the settings that need to be configured.

This configuration is used both when Camunda is used as a registration backend AND when Camunda is used as the engine to
evaluate decision tables in form logic rules.


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
