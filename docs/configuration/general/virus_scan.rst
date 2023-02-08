.. _configuration_general_virus_scan:

Virus scan with ClamAV
=======================

In Open-Forms, it is possible to scan files uploaded by a user for possible viruses. The scan is done with `ClamAV`_.
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

Save the changes. You can navigate to **Configuratie** > **Configuratie overzicht** to see if Open-Forms can connect to
the ClamAV server.

Running ClamAV
--------------

For information on how to run a ClamAV server, look at the ClamAV `documentation`_.

It is possible to run ClamAV as a `Docker container`_. For an example, see our ``docker-compose.yml`` file.
When testing with our ``docker-compose.yml`` file, the admin should be configured as follows:

* Check the box **Enable virus scan**.
* Fill ClamAV server hostname: **clamav**
* Fill ClamAV port: **3310**.

.. _documentation: https://docs.clamav.net/
.. _Docker container: https://hub.docker.com/r/clamav/clamav

RAM requirements
^^^^^^^^^^^^^^^^

The ClamAV recommendation for the container RAM is:

* Minimum: 3 GB
* Preferred: 4 GB

As explained in the `ClamAV documentation`_, once a day ClamAV loads new signature definitions.
When reloading the engine to include the new definitions, it will use more than 2.4 GB of RAM.
So, if your container is killed / becomes unresponsive once a day, it might not have enough RAM for this process.

.. _ClamAV documentation: https://docs.clamav.net/manual/Installing/Docker.html#why-is-this-much-ram-required
