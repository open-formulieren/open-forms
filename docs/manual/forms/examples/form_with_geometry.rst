.. _example_form_with_geometry:

==============================================
Form with geometry and registration attributes
==============================================

When adding a component to a form, it is possible to have the value filled in by
the user set as a specific field on the selected registration backend.

In this example, we will use the `Objects API`_ as a registration backend.

.. note::

    Depending on the selected backend, the supported registration attributes might differ.
    In the case of `Objects API`_, only the *Location > Coordinate* attribute is supported.


Creating the form
=================

1. Create an empty form and add a first step.
2. Add a new map component: *Speciale velden > Kaart*.
3. Under the **Registratie** tab, select the value *Location > Coordinate* in the **Registratie-attribuut** dropdown.
4. Save the component, and go under the **Registration** tab of the current form.
5. Add one of your configured Objects API backends (see :ref:`configuration_registration_objects` for more details on how to configure the backend).

Registration process
====================

When a new submission for this form is created, it will be registered in the selected backend (in our case, Objects API).

Internally, Open Forms will look into each component to see if a registration attribute is set. If this is the case,
the submitted value for this component will be set to a fixed JSON path (this path differs depending on the registration backend).

In the case of `Objects API`_, the service supports a geometry attribute set to ``record.geometry``. In our case,
the JSON data sent to the Objects API will look like the following:

.. code-block:: json

    {
        "type": "https://objecttype-example.nl/api/v2/objecttype/123",
        "record": {
            "typeVersion": "1",
            "data": {},
            "startAt": "2023-01-01",
            "geometry": {"type": "Point", "coordinates": [1.0, 2.0]}
        }
    }

Dealing with multiple geometry components
=========================================

When configuring registration attributes, having multiple components with the same attribute set will result in
the last one overridding the others. With the Objects API registration, you can circumvent this issue by tweaking
the JSON content template.

.. seealso::

    For more details on how to work with the JSON content template, see :ref:`objecten_api_registratie`.

If we have two map components with the following Eigenschapnaam: ``map1`` and ``map2``; and ``map1`` is using the location registration attribute,
we can use the following JSON content template to set ``map2`` to the custom data attribute ``map2_result``:

.. code-block:: django

    {
        "data": {% json_summary %},
        "type": "{{ productaanvraag_type }}",
        "bsn": "{{ variables.auth_bsn }}",
        "pdf_url": "{{ submission.pdf_url }}",
         attachments": {% uploaded_attachment_urls %},
        "submission_id": "{{ submission.kenmerk }}",
        "language_code": "{{ submission.language_code }}",
        "map2_result": : {% as_geo_json variables.map2 %}
    }

The resulting JSON data sent to the Objects API will look like:

.. code-block:: json

    {
        "type": "<configured_objecttype>",
        "record": {
            "typeVersion": "<configured_version>",
            "data": {
                "data": "...",
                "...": "...",
                "map2_result": {"type": "Point", "coordinates": [3.0, 4.0]}
            },
            "startAt": "2023-01-01",
            "geometry": {"type": "Point", "coordinates": [1.0, 2.0]}
        }
    }

.. _`Objects API`: https://objects-and-objecttypes-api.readthedocs.io/
