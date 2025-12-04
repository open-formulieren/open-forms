.. _installation_self_signed:

Using self-signed certificates
==============================

Open Forms supports self-signed certificates in two ways:

* Hosting Open Forms using self-signed certificates - this is the classic route where
  your web server/ingress is configured appropriately
* Consuming services hosted with self-signed certificates - this is what this guide is
  about.

.. note::

   Some background!

   Open Forms communicates with external services such as ZGW API's, StUF-ZDS, StUF-BG
   and HaalCentraal providers. It does this using ``https`` - using http is insecure.

   When Open Forms makes these requests, the SSL certificates are verified for their
   validity - e.g. expired certificates or certificates signed by an unknown Certificate
   Authority (CA) will throw errors (as they should!).

   When you're using self-signed certificates, you are essentially using an unknown CA,
   and this breaks the functionality of Open Forms.


Adding your own certificates or CA (root) certificate
-----------------------------------------------------

Open Forms supports adding extra, custom certificates to the provided CA bundle. You do
this by setting an environment variable ``EXTRA_VERIFY_CERTS``, which must be a
comma-separated list of paths to certificate files in PEM format.

An example of such a certificate is:

.. code-block:: none

    -----BEGIN CERTIFICATE-----
    MIIByDCCAW8CFBRCXMlcdJAPb8XkG4cYMNL+Ku17MAoGCCqGSM49BAMCMGcxCzAJ
    BgNVBAYTAk5MMRYwFAYDVQQIDA1Ob29yZC1Ib2xsYW5kMRIwEAYDVQQHDAlBbXN0
    ZXJkYW0xEjAQBgNVBAoMCU9wZW4gWmFhazEYMBYGA1UEAwwPT3BlbiBaYWFrIFRl
    c3RzMB4XDTIxMDMxOTExMDYyM1oXDTI0MDMxODExMDYyM1owZzELMAkGA1UEBhMC
    TkwxFjAUBgNVBAgMDU5vb3JkLUhvbGxhbmQxEjAQBgNVBAcMCUFtc3RlcmRhbTES
    MBAGA1UECgwJT3BlbiBaYWFrMRgwFgYDVQQDDA9PcGVuIFphYWsgVGVzdHMwWTAT
    BgcqhkjOPQIBBggqhkjOPQMBBwNCAASzDq7C9atfN3uxoAGOCro8RfzWloVusDeO
    bwXztxUC/wBu4WgfRsYjg65eVzaJWQKvIKn5W9rGyuIAYbJZJtMZMAoGCCqGSM49
    BAMCA0cAMEQCIHKCp4qVEzF3WgaL6jY4tf60HBThnQTaXC99P7TaIFhxAiASMBVV
    tmukm/NP8zSMrNpEGLnGIFa8uU/d8VwNNPFhtA==
    -----END CERTIFICATE-----

Typically you would do this by (bind) mounting a volume in the Open Forms container
containing these certificates, and then specify their paths in the container, for
example:

.. code-block:: bash

    docker run \
        -it \
        -v /etc/ssl/certs:/certs:ro \
        -e EXTRA_VERIFY_CERTS=/certs/root1.crt,/certs/root2.crt
        open-zaak/open-zaak:latest

Of course, you will need to adapt this solution to your deployment method (Helm,
Kubernetes, single-server...).

PKIO
----

The Dutch government uses a CA-certificate which is not publicaly trusted. You
will need to add the so called PKIO G1 private root certificate.

1. Download the G1 certificate ("Stamcertificaat") from `cert.pkioverheid.nl/ <https://cert.pkioverheid.nl/>`__
2. Convert it from the binary X.509 encoding (DER) to the base64 encoding (CRT)

   .. code-block:: bash

      openssl x509 -inform DER -in PrivateRootCA-G1.crt -out PrivateRootCA-G1.crt

3. Make sure it's added as ``EXTRA_VERIFY_CERTS``. See above for instructions.
