.. _install_development:

=======================
Development environment
=======================

Quick start
===========

#. Navigate to the location where you want to place your project.

#. Get the code::

    $ git clone git@bitbucket.org:maykinmedia/openforms.git
    $ cd openforms

#. Bootstrap the virtual environment and install all required libraries. The
   ``bootstrap.py`` script basically sets the proper Django settings file to be
   used::

    $ python bootstrap.py <production|staging|test|dev>

#. Activate your virtual environment and create the statics and database::

    $ source env/bin/activate  # or, workon <env> if you use virtualenvwrapper
    $ npm install
    $ gulp sass
    $ python src/manage.py collectstatic --link
    $ python src/manage.py migrate


Next steps
----------

Optionally, you can load demo data and extract demo media files::

    $ python src/manage.py loaddata demo
    $ cd media
    $ tar -xzf demo.tgz

You can now run your installation and point your browser to the address given
by this command::

    $ python src/manage.py runserver
