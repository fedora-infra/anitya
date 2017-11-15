Generating new revisions
========================

For a branch based on `origin/master` that includes schema changes:

    $ rm /var/tmp/anitya-dev.sqlite
    $ git checkout origin/master
    $ python createdb.py
    $ git checkout <my working branch>
    $ alembic stamp head
    $ alembic revision --autogenerate -m "<Title for schema update>"`

Table creation is handled by `createdb.py`, so edit the generated migration
to remove the table creation commands.
