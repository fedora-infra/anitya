.. image:: https://codecov.io/gh/release-monitoring/anitya/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/release-monitoring/anitya

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

Development
-------

Anitya deployment is currently only supported on Python 2.x, but local
development can use either Python 2.x or 3.x. The following steps should
all work regardless of which runtime you have your virtual environment
configured to use.

Vagrant
```````

To run Anitya in a Vagrant guest, simply run::

    $ sudo dnf install vagrant vagrant-libvirt vagrant-sshfs ansible
    $ cp Vagrantfile.example Vagrantfile
    $ vagrant up
    $ vagrant ssh
    $ systemctl --user start anitya.service

You may then access Anitya on your host at::

    http://127.0.0.1:5000

By default anitya imports the production database so you've got something
to work off of. If instead you prefer an empty database, add the following
to the ansible provisioner inside your `Vagrantfile`::

    ansible.extra_vars = { import_production_database: false }

virtualenv
``````````

Here are some preliminary instructions about how to stand up your own instance
of Anitya. We'll use a virtualenv and a sqlite database and we'll install
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

    (anitya-env)$ pip install -r requirements/requirements.txt


Running the test suite
``````````````````````
Regardless of which Python version you have configured in your local venv,
the tests can be run under both Python 2 & 3 via:

    (anitya-env)$ tox


Running a local instance
````````````````````````

Replace httplib2's own ca cert file (adjust as needed for Python version)::

    (anitya-env) $ ln -s /etc/pki/tls/certs/ca-bundle.crt \
                   ~/.virtualenvs/anitya-env/lib/python3.5/site-packages/httplib2/cacerts.txt

Configure the project to authenticate against iddev.fedorainfraclouid.org::

    (anitya-env) $ oidc-register \
                   --token-introspection-uri=https://iddev.fedorainfracloud.org/openidc/TokenInfo \
                   https://iddev.fedorainfracloud.org/ http://localhost:5000

Cache a local OIDC credentials file for automated integration testing::

    (anitya-env) $ python request_oidc_credentials.py

Create the database, by default it will be a sqlite database located at
``/var/tmp/anitya-dev.sqlite``::

    (anitya-env) $ python createdb.py

With that, try running the app with::

    (anitya-env) $ python runserver.py -c config

And then navigate to http://localhost:5000/


If all goes well, you can start a development instance of the server by
running::

    (anitya-env)$ python runserver.py

Open your browser and visit http://localhost:5000 to check it out.


Docker
``````
To build the Docker image::

    $ cd anitya/
    $ docker build -t anitya .

To run the container with a disposable SQLite database::

    $ docker run -e DB_URL='sqlite:////opt/anitya/anitya.db' -d -p 80:80 anitya


Listening for local event announcements
---------------------------------------

To listen for local event announcements over the Federated Message Bus,
first start a local relay in the background::

    $ fedmsg-relay --config-filename fedmsg.d/fedmsg-config.py &

And then display the received messages in the local console::

    $ fedmsg-tail --config fedmsg.d/fedmsg-config.py --no-validate --really-pretty

These commands will pick up the local config automatically if you're in
the Anitya checkout directory, but being explicit ensures they don't silently
default to using the global configuration.

To display the messages, we turn off signature validation (since the local
server will be emitting unsigned messages) and pretty-print the received JSON.

Refer to the `fedmsg consumer API <http://www.fedmsg.com/en/latest/consuming/>`_
for more details on receiving event messages programmatically.


Deployment
-------

Docker
``````
To build the Docker image::

    $ cd anitya/
    $ docker build -t anitya .

To run the container, execute the command below. Be sure to replace the value of DB_URL with the URL to connect to
your production database. Also ensure to replace SECRET_KEY with a random string (preferably hex values) that is the
same on every deployment of Anitya, as this is used for session management::

    $ docker run -e DB_URL='db_type://user:password@server.domain.local:3306/database_name' \
                 -e SECRET_KEY='123456789abcdef123456789' -d -p 80:80 anitya
