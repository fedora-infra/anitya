Cnucnu Web
==========

Cnucnu is a release monitoring project.

Its goal is to regulary check if a project has made a new release. Originally
developed within Fedora, this project creates tickets on the `Fedora
bugzilla <https://bugzilla.redhat.com/>`_ when a new release is available.

Cnucnu Web provides a user-friendly interface to add or edit projects. New
releases are announced on `fedmsg <http://fedmsg.com>`_ and notifications
can then be sent via `FMN <http://github.com/fedora-infra/fmn>`_ (the FedMsg
Notifications service).

:Github page: https://github.com/fedora-infra/cnucnuweb


Hacking
-------

Here are some preliminary instructions about how to stand up your own instance
of cnucnuweb.  We'll use a virtualenv and a sqlite database and we'll install
our dependencies from the Python Package Index (PyPI).  None of these are best
practices for a production instance, but they will do for development.

First, set up a virtualenv::

    $ sudo yum install python-virtualenv
    $ virtualenv my-cnucnu-env
    $ source my-cnucnu-env/bin/activate

Issueing that last command should change your prompt to indicate that you are
operating in an active virtualenv.

Next, install your dependencies::

    (my-cnucnu-env)$ pip install -r requirements.txt

Create the database, by default it will be a sqlite database located at
``/var/tmp/cnucnu-web-dev.sqlite``::

    (my-cnucnu-env)$ python createdb.py

If all goes well, you can start a development instance of the server by
running::

    (my-cnucnu-env)$ python runserver.py

Open your browser and visit http://localhost:5000 to check it out.
