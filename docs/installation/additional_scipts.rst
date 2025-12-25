.. _installation_additional_scripts:

=========================================
Update Open Forms with additional scripts
=========================================

Sometimes, upgrading from a specific version of Open Forms to another one requires an extra
script which is necessary for additional operations. In case this script is missing in your
container you can follow the instructions to copy it from the project source.

1.  Visit the source code of Open Forms in github and download the raw file:

.. code-block:: bash

    $ wget https://github.com/open-formulieren/open-forms/blob/main/<name_of_the_file>

2.  Copy the downloaded file to the `/app/bin` folder in the container

.. code-block:: bash

    $ docker cp <file_name> <container_id_or_name>:/app/bin

3.  Run the script
