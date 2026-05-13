===
JCC
===

1. You will need to have a contract with `JCC`_ to use this plugin.
2. In Open Forms navigate to: **Configuration** > **Overview**
3. In the **Appointments plugin** group, click on **Configuration** for the **JCC-Rest** line.
4. Click the **Green Plus Button** to add a service and fill in the following details:

   * **Label**: JCC (REST)
   * **Api root url**: ORC (Overige)
   * **Api root url**: URL to the JCC-Afspraken WARP API, for example: ``https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api/warp/v1/``
   * **Authorization type**: OAuth2 client credentials flow
   * **Client id**: The client ID provided by the contract
   * **Secret**: The secret provided by the contract
   * **OAuth2 token url**: ``https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api/warp/v1/connect/token``
   * **OAuth2 scope**: warp-api

5. Click **Save**

.. _`JCC`: https://www.jccsoftware.nl/afspraken/
