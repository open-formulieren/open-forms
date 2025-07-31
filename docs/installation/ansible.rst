.. _installation_ansible:

=====================
Install using Ansible
=====================

Deployment is done via `Ansible`_. Currently, only single server deployments
are described but you can just as easily deploy the application in a Kubernetes
environment.

.. warning:: The deployment configuration (called a "playbook") is very
   simplistic and also contains sensitive values. This makes the playbook more
   readable but is not following best practices!

Prerequisites
=============

You will only need Ansible tooling and nothing more on your own machine:

* `Ansible`_


Server preparation
==================

You can configure the Ansible playbook to install relevant services, do it
manually, or have these pre-installed. You will need:

* PostgreSQL 12 or above
* Nginx
* Docker
* Python 3.6+ (needed for Ansible, not Open Forms)
* Python PIP

Apart from Docker, you can install all these with something like:

.. code:: shell

   $ sudo apt-get install git postgresql nginx python3 python3-pip python3-venv

For Docker, follow the instructions here: https://docs.docker.com/engine/install/

You will also need access to, or create, a database. You can create a database
with something like:

.. code:: shell

   $  sudo su postgres --command="createuser <db-username> -P"
   Enter password for new role:
   Enter it again:
   $ sudo su postgres --command="createdb <db-name> --owner=<db-username>"


Installation
============

1. Download the project from Github or just the `deployment files`_.

   .. code:: shell

      $ git clone https://github.com/open-formulieren/open-forms.git

2. Setup virtual environment:

   .. code:: shell

      $ python3 -m venv env/
      $ source env/bin/activate
      $ pip install "ansible~=2.10"

   .. note:: Sometimes, additional or updates packages are needed if they
      are not installed by the Ansible setup installation. You can do so like
      this:

      .. code:: shell

         $ python -m pip install -U pip
         $ pip install ordered_set packaging appdirs six wheel

3. Install Ansible collections:

   .. code:: shell

      $ ansible-galaxy collection install community.docker
      $ ansible-galaxy collection install maykinmedia.commonground

4. Edit the playbook ``app.yml`` to match your setup. Take special note of all
   **TODO** settings and **read through all the comments and variables**.

5. Rename ``hosts.example`` to ``hosts`` and make sure it contains your host.

6. Run the playbook:

   .. code:: shell

      $ ansible-playbook app.yml [--become --ask-become-pass --user=<myusername>]


.. _`Ansible`: https://www.ansible.com/
.. _`deployment files`: https://github.com/open-formulieren/open-forms/tree/stable/3.2.x/deployment
