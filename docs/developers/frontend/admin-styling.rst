.. _developers_frontend_admin_styling:

Admin styling
=============
Custom styling of admin components can be realized by adding/updating .scss files,
which are located in ``src/openforms/scss``.

Adding a custom style
---------------------
The steps below describe how to add custom styling for a component in the admin, with the
help of an example ``div`` component:

.. code-block:: html

    <div className="json-dump-variables json-dump-variables--horizontal">
        ...
    </div>

1. Create a new file called ``_component-file-name.scss`` in ``src/openforms/scss/components/admin``,
   where ``component-file-name`` reflects the class name of the component. For example: ``_json-dump-variables.scss``

2. Add the custom styling. For example:

   .. code-block:: scss

       .json-dump-variables {
         display: flex;

         @include bem.modifier('horizontal') {
           align-items: center;
           gap: 0.5em;
         }
       }

3. To ensure it gets picked up, add an import of the file name (without underscore) to the ``_index.scss``
   file of the parent directory. For example, in ``src/openforms/scss/components/admin/_index.scss``):

   .. code-block:: scss

       ...
       @import './json-dump-variables';
       ...
