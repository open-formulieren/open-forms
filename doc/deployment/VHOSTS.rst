Apache + mod-wsgi configuration
===============================

An example Apache2 vhost configuration follows::

    WSGIDaemonProcess openforms-<target> threads=5 maximum-requests=1000 user=<user> group=staff
    WSGIRestrictStdout Off

    <VirtualHost *:80>
        ServerName my.domain.name

        ErrorLog "/srv/sites/openforms/log/apache2/error.log"
        CustomLog "/srv/sites/openforms/log/apache2/access.log" common

        WSGIProcessGroup openforms-<target>

        Alias /media "/srv/sites/openforms/media/"
        Alias /static "/srv/sites/openforms/static/"

        WSGIScriptAlias / "/srv/sites/openforms/src/openforms/wsgi/wsgi_<target>.py"
    </VirtualHost>


Nginx + uwsgi + supervisor configuration
========================================

Supervisor/uwsgi:
-----------------

.. code::

    [program:uwsgi-openforms-<target>]
    user = <user>
    command = /srv/sites/openforms/env/bin/uwsgi --socket 127.0.0.1:8001 --wsgi-file /srv/sites/openforms/src/openforms/wsgi/wsgi_<target>.py
    home = /srv/sites/openforms/env
    master = true
    processes = 8
    harakiri = 600
    autostart = true
    autorestart = true
    stderr_logfile = /srv/sites/openforms/log/uwsgi_err.log
    stdout_logfile = /srv/sites/openforms/log/uwsgi_out.log
    stopsignal = QUIT

Nginx
-----

.. code::

    upstream django_openforms_<target> {
      ip_hash;
      server 127.0.0.1:8001;
    }

    server {
      listen :80;
      server_name  my.domain.name;

      access_log /srv/sites/openforms/log/nginx-access.log;
      error_log /srv/sites/openforms/log/nginx-error.log;

      location /500.html {
        root /srv/sites/openforms/src/openforms/templates/;
      }
      error_page 500 502 503 504 /500.html;

      location /static/ {
        alias /srv/sites/openforms/static/;
        expires 30d;
      }

      location /media/ {
        alias /srv/sites/openforms/media/;
        expires 30d;
      }

      location / {
        uwsgi_pass django_openforms_<target>;
      }
    }
