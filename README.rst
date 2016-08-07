Anitya
======

Anitya is a release monitoring project.

Its goal is to regularly check if a project has made a new release. Originally
developed within Fedora, the project created tickets on the `Fedora
bugzilla <https://bugzilla.redhat.com/>`_ when a new release is available.
Now this service has been split into two parts:

* `anitya <https://github.com/fedora-infra/anitya>`_: find and announce new
  releases
* `the new hotness <https://github.com/fedora-infra/the-new-hotness/>`_:
  listens to the fedmsg bus, opens a ticket on bugzilla for packages allowing
  for it and triggers a scratch-build of the new version

Anitya provides a user-friendly interface to add or edit projects. New
releases are announced on `fedmsg <http://fedmsg.com>`_ and notifications
can then be sent via `FMN <http://github.com/fedora-infra/fmn>`_ (the FedMsg
Notifications service).

:Github page: https://github.com/fedora-infra/anitya

Hacking
-------

Anitya deployment is currently only supported on Python 2.x, but local
development can use either Python 2.x or 3.x. The following steps should
all work regardless of which runtime you have your virtual environment
configured to use.

virtualenv
``````````

Here are some preliminary instructions about how to stand up your own instance
of anitya. We'll use a virtualenv and a sqlite database and we'll install
our dependencies from the Python Package Index (PyPI).  None of these are best
practices for a production instance, but they will do for development.

First, set up a virtualenv::

    $ sudo yum install python-virtualenv
    $ virtualenv anitya-env --system-site-packages
    $ source anitya-env/bin/activate

Issuing that last command should change your prompt to indicate that you are
operating in an active virtualenv.

Access to the system site packages is needed for access to the RPM bindings,
as those aren't available through PyPI, only as RPMs for the system Python
runtime.

Next, install your dependencies::

    (anitya-env)$ pip install -r requirements.txt


Running the test suite
``````````````````````

The tests can be run with a coverage data report via::

    (anitya-env)$ ./runtests.sh

If this is the first time you've run the tests, you'll also want to do::

    (anitya-env)$ pip install -r test_requirements.txt

Regardless of which Python version you have configured in your local venv,
the tests can be run under both Python 2 & 3 via:

    (anitya-env)$ tox


Running a local instance
````````````````````````

Create the database, by default it will be a sqlite database located at
``/var/tmp/anitya-dev.sqlite``::

    (anitya-env)$ python createdb.py

If all goes well, you can start a development instance of the server by
running::

    (anitya-env)$ python runserver.py

Open your browser and visit http://localhost:5000 to check it out.


Docker
``````

To build the Docker image::

    $ cd anitya/
    $ docker build --tag=anitya .

To run the container::

    $ docker run -d -p 5000:5000 anitya
