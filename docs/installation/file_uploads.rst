.. _installation_file_uploads:

File uploads
============

Open Forms supports file upload fields in forms, which needs some special care at the
webserver level.

Typically Open Forms is deployed behind a load balancer - on Kubernetes
this would be your ingress solution, while on a single-server setup you'd typically
run a reverse proxy like nginx on your host.

Misconfiguration or bad tuning will typically result in
:ref:`installation_issues_http_413` errors.

Endpoints
---------

The following endpoint(s) process file-uploads:

- ``/api/v1/submissions/files/upload``

We recommend specifying upload limits specifically for these endpoints, as allowing
large requests bodies poses a Denial-of-Service (DOS) risk.

For example:

.. code-block:: nginx

    location = /api/v1/submissions/files/upload {
        client_max_body_size 50M;

        // usual proxy directives...
        proxy_pass http://backend;
    }

Environment variable
--------------------

Additionally, Open Forms supports the ``MAX_FILE_UPLOAD_SIZE`` environment variable.
File uploads larger than that will be rejected, and the value will be dynamically
presented in the form designer and relevant API documentation.
