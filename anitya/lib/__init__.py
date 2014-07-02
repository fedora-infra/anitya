#-*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

anitya internal library.
"""


__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import datetime
import logging
import time

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

import anitya.lib
import anitya.lib.model
import anitya.lib.exceptions

log = logging.getLogger(__name__)


def init(db_url, alembic_ini=None, debug=False, create=False):
    """ Create the tables in the database using the information from the
    url obtained.

    :arg db_url, URL used to connect to the database. The URL contains
        information with regards to the database engine, the host to
        connect to, the user and password and the database name.
          ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg alembic_ini, path to the alembic ini file. This is necessary
        to be able to use alembic correctly, but not for the unit-tests.
    :kwarg debug, a boolean specifying wether we should have the verbose
        output of sqlalchemy or not.
    :return a session that can be used to query the database.

    """
    engine = create_engine(db_url, echo=debug)

    if create:
        model.BASE.metadata.create_all(engine)

    # Source: http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html
    # see section 'sqlite-foreign-keys'
    if db_url.startswith('sqlite:'):
        def _fk_pragma_on_connect(dbapi_con, con_record):
            dbapi_con.execute("PRAGMA foreign_keys=ON")
        sa.event.listen(engine, 'connect', _fk_pragma_on_connect)

    if alembic_ini is not None:  # pragma: no cover
        # then, load the Alembic configuration and generate the
        # version table, "stamping" it with the most recent rev:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(alembic_ini)
        command.stamp(alembic_cfg, "head")

    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession


def create_project(
        session, name, homepage, backend, version_url, regex, user_mail):
    """ Create the project in the database.

    """
    project = model.Project(
        name=name,
        homepage=homepage,
        backend=backend,
        version_url=version_url,
        regex=regex
    )

    session.add(project)

    try:
        session.flush()
    except SQLAlchemyError:
        session.rollback()
        raise exceptions.AnityaException(
            'Could not add this project, already exists?')

    anitya.log(
        session,
        project=project,
        topic='project.add',
        message=dict(
            agent=user_mail,
            project=project.name,
        )
    )
    session.commit()
    return project


def edit_project(
        session, project, name, homepage, backend, version_url, regex,
        user_mail):
    """ Edit a project in the database.

    """
    edit = []
    if name != project.name:
        project.name = name
        edit.append('name')
    if homepage != project.homepage:
        project.homepage = homepage
        edit.append('homepage')
    if backend != project.backend:
        project.backend = backend
        edit.append('backend')
    if version_url != project.version_url:
        project.version_url = version_url
        edit.append('version_url')
    if regex != project.regex:
        project.regex = regex
        edit.append('regex')

    try:
        if edit:
            anitya.log(
                session,
                project=project,
                topic='project.edit',
                message=dict(
                    agent=user_mail,
                    project=project.name,
                    fields=edit,
                )
            )
            session.add(project)
            session.commit()
    except SQLAlchemyError, err:
        session.rollback()
        raise exceptions.AnityaException(
            'Could not edit this project. Is there already a project '
            'with this homepage?', 'errors')


def map_project(
        session, project, package_name, distribution, user_mail,
        old_package_name=None):
    """ Map a project to a distribution.

    """

    distribution = distribution.strip()
    cnt = 0
    msgs = []

    distro_obj = anitya.lib.model.Distro.get(session, distribution)

    if not distro_obj:
        distro_obj = anitya.lib.model.Distro(name=distribution)
        anitya.log(
            session,
            distro=distro_obj,
            topic='distro.add',
            message=dict(
                agent=user_mail,
                distro=distro_obj.name,
            )
        )
        session.add(distro_obj)
        try:
            session.flush()
        except SQLAlchemyError, err:
            session.rollback()
            raise exceptions.AnityaException(
                'Could not add the distribution %s to the database, '
                'please inform an admin.' % distribution, 'errors')

    pkgname = old_package_name or package_name
    pkg = anitya.lib.model.Packages.get(
        session, project.id, distribution, pkgname)

    edited = None
    if not pkg:
        topic = 'project.map.new'
        pkg = anitya.lib.model.Packages(
            distro=distribution,
            project_id=project.id,
            package_name=package_name
        )
    else:
        topic = 'project.map.update'
        edited = []
        if pkg.distro != distribution:
            pkg.distro = distribution
            edited.append('distribution')
        if pkg.package_name != package_name:
            pkg.package_name = package_name
            edited.append('package_name')

    session.add(pkg)
    try:
        session.flush()
    except SQLAlchemyError, err:
        session.rollback()
        raise exceptions.AnityaException(
            'Could not add the mapping of %s to %s, please inform an '
            'admin.' % (package_name, distribution), 'errors')

    message = dict(
        agent=user_mail,
        project=project.name,
        distro=distribution,
        new=package_name,
    )
    if edited:
        message['edited'] = edited

    anitya.log(
        session,
        project=project,
        distro=distro_obj,
        topic=topic,
        message=message,
    )

    return pkg
