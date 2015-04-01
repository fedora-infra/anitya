# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

anitya internal library.
"""


__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import logging
import sys

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

import anitya.lib
import anitya.lib.model
import anitya.lib.exceptions

log = logging.getLogger('anitya.lib')
STDERR_LOG = logging.StreamHandler(sys.stderr)
STDERR_LOG.setLevel(logging.INFO)
log.addHandler(STDERR_LOG)


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
        anitya.lib.model.BASE.metadata.create_all(engine)

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

    if create:
        anitya.lib.plugins.load_plugins(scopedsession)

    return scopedsession


def create_project(
        session, name, homepage, user_mail, backend='custom',
        version_url=None, regex=None):
    """ Create the project in the database.

    """
    project = anitya.lib.model.Project(
        name=name,
        homepage=homepage,
        backend=backend,
        version_url=version_url,
        regex=regex
    )

    session.add(project)

    try:
        session.flush()
    except SQLAlchemyError as err:
        log.exception(err)
        session.rollback()
        raise anitya.lib.exceptions.AnityaException(
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
        insecure, user_mail):
    """ Edit a project in the database.

    """
    changes = {}
    if name != project.name:
        old = project.name
        project.name = name.strip() if name else None
        changes['name'] = {'old': old, 'new': project.name}
    if homepage != project.homepage:
        old = project.homepage
        project.homepage = homepage.strip() if homepage else None
        changes['homepage'] = {'old': old, 'new': project.homepage}
    if backend != project.backend:
        old = project.backend
        project.backend = backend
        changes['backend'] = {'old': old, 'new': project.backend}
    if  version_url != project.version_url:
        old = project.version_url
        project.version_url = version_url.strip() if version_url else None
        if old != project.version_url:
            changes['version_url'] = {'old': old, 'new': project.version_url}
    if regex != project.regex:
        old = project.regex
        project.regex = regex.strip() if regex else None
        if old != project.regex:
            changes['regex'] = {'old': old, 'new': project.regex}
    if insecure != project.insecure:
        old = project.insecure
        project.insecure = insecure
        changes['insecure'] = {'old': old, 'new': project.insecure}

    try:
        if changes:
            anitya.log(
                session,
                project=project,
                topic='project.edit',
                message=dict(
                    agent=user_mail,
                    project=project.name,
                    fields=changes.keys(),  # be backward compat
                    changes=changes,
                )
            )
            session.add(project)
            session.commit()
    except SQLAlchemyError as err:
        log.exception(err)
        session.rollback()
        raise anitya.lib.exceptions.AnityaException(
            'Could not edit this project. Is there already a project '
            'with these name and homepage?')


def map_project(
        session, project, package_name, distribution, user_mail,
        old_package_name=None, old_distro_name=None):
    """ Map a project to a distribution.

    """

    distribution = distribution.strip()

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
        except SQLAlchemyError, err:  # pragma: no cover
            # We cannot test this situation
            session.rollback()
            raise anitya.lib.exceptions.AnityaException(
                'Could not add the distribution %s to the database, '
                'please inform an admin.' % distribution, 'errors')

    pkgname = old_package_name or package_name
    distro = old_distro_name or distribution
    pkg = anitya.lib.model.Packages.get(
        session, project.id, distro, pkgname)

    # Check that we can update the mapping to the new info provided
    other_pkg = anitya.lib.model.Packages.by_package_name_distro(
        session, package_name, distro)
    if other_pkg:
        raise anitya.lib.exceptions.AnityaInvalidMappingException(
                pkgname, distro, package_name, distribution,
                other_pkg.project.id, other_pkg.project.name)

    edited = None
    if not pkg:
        topic = 'project.map.new'
        pkg = anitya.lib.model.Packages(
            distro=distro_obj.name,
            project_id=project.id,
            package_name=package_name
        )
    else:
        topic = 'project.map.update'
        edited = []
        if pkg.distro != distro_obj.name:
            pkg.distro = distro_obj.name
            edited.append('distribution')
        if pkg.package_name != package_name:
            pkg.package_name = package_name
            edited.append('package_name')

    session.add(pkg)
    try:
        session.flush()
    except SQLAlchemyError as err:  # pragma: no cover
        log.exception(err)
        # We cannot test this situation
        session.rollback()
        raise anitya.lib.exceptions.AnityaException(
            'Could not add the mapping of %s to %s, please inform an '
            'admin.' % (package_name, distribution))

    message = dict(
        agent=user_mail,
        project=project.name,
        distro=distro_obj.name,
        new=package_name,
    )
    if edited:
        message['prev'] = old_package_name or package_name
        message['edited'] = edited

    anitya.log(
        session,
        project=project,
        distro=distro_obj,
        topic=topic,
        message=message,
    )

    return pkg


def flag_project(session, project, reason, user_mail):
    """ Flag a project in the database.

    """

    flag = anitya.lib.model.ProjectFlag(
        project=project,
        reason=reason,
        user=user_mail)

    session.add(flag)

    try:
        session.flush()
    except SQLAlchemyError as err:
        log.exception(err)
        session.rollback()
        raise anitya.lib.exceptions.AnityaException(
            'Could not flag this project.')

    anitya.log(
        session,
        project=project,
        topic='project.flag',
        message=dict(
            agent=user_mail,
            project=project.name,
            reason=reason,
        )
    )
    session.commit()
    return project
