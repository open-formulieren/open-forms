.. _configuration_general_virus_scan:

Virus scan with ClamAV
=======================

In Open Forms, it is possible to scan files uploaded by a user for viruses (for more information on the file
upload flow, please see this :ref:`section<developers_backend_file_uploads>`). The scan is done with `ClamAV`_.
The scan happens as soon as the user uploads a file in the **File upload** component and if it is found to contain
malware, the upload is blocked and the file is not saved. The user is alerted that the virus scan found the file
to be infected.

Scanning files for malware is disabled by default. The configuration can be updated in the Admin.

.. _ClamAV: https://www.clamav.net/

Configuration
-------------

In the admin, navigate to **Configuratie** > **Algemene configuratie**. Scroll to **Virus scan**. Then:

* Check the box **Enable virus scan**.
* Fill **ClamAV server hostname**
* Fill **ClamAV port**. By default ClamAV listens on port 3310.
* Optionally, fill **ClamAV socket timeout**.

Save the changes. You can navigate to **Configuratie** > **Configuratie overzicht** to see if Open Forms can connect to
the ClamAV server.

Running ClamAV
--------------

For information on how to run a ClamAV server, look at the ClamAV `documentation`_.

It is possible to run ClamAV as a `Docker container`_. Deploying ClamAV is out of scope for this documentation.
Please refer to the official ClamAV documentation if you would like to run it.

.. _documentation: https://docs.clamav.net/
.. _Docker container: https://hub.docker.com/r/clamav/clamav
