.. _configuration_registration_json_dump:

=========
JSON Dump
=========

The JSON Dump registration plugin can be used to send submitted form data as a
`JSON object`_ to a configured service.

What does the Open Forms administrator need?
============================================

Service options:

* API root URL
* API credentials (optional)
* Client certificate (optional)
* Server certificate (optional)

Plugin options:

* Which form variables to include in the data
* API endpoint (optional)


Configuration
=============

To configure the JSON Dump plugin, follow these steps:

#. In Open Forms, navigate to: **Configuration** > **Services**
#. Create a service to which the submitted form data should be sent

   a. Click **Add service**
   b. Fill out the form:

      * **Label**: *Fill in a human readable label*, for example: ``JSON Dump service``
      * **Type**: Select the type: ``ORC``
      * **API root url**: The root of this API, *for example* ``https://example.com/objecten/api/v2/``
      * **Authorization type**: Select the desired type of authorization
      * **Header key**: Header key of the API key (optional, only applicable for ``API key`` **Authorization type**)
      * **Header value**: The API key to connect to the service (optional, only applicable for ``API key`` **Authorization type**)

      * **Client certificate**: Select an existing or create a new certificate (optional)
      * **Server certificate**: Select an existing or create a new certificate (optional)

   c. Click **Save**

#. Navigate to: **Forms** > **Forms** and click on the desired form to configure the plugin for
#. In the form, navigate to the **Registration** tab, click **Add registration backend**, and fill out:

   a. **Name**: *Fill in a human readable label*, for example: ``JSON Dump plugin``
   b. **Select registration backend**: Select ``JSON dump registration``
   c. Click on **Configure options** and fill out the options:

      * **Service**: Select the service created in step 2
      * **Path**: Fill in the path relative to the service API root (optional)
      * **Variables**: Select the (form) variables which should be included in the data
      * **Metadata variables**: Consists of several fixed variables, and additional variables can be added here (optional)

   d. Click **Save**

#. Click **Save** or **Save and continue editing** to save the form


Technical
=========

The data that will be sent is a `JSON object`_ with four properties:

* values: JSON Object with the selected variables as properties
* values_schema: `JSON schema`_ describing the `values` property
* metadata: JSON object with the fixed and additional metadata variables as properties
* metadata_schema: JSON schema describing the `metadata` property

For file components that are included in the data to be sent (variable key was selected in the **Variables** option
of the plugin), the content of the attachment(s) uploaded to these components will be encoded using `base64`_.


.. _`JSON Object`: https://www.json.org/json-en.html
.. _`JSON Schema`: https://json-schema.org/
.. _`base64`: https://en.wikipedia.org/wiki/Base64
