# -*- coding: utf-8 -*-
#
# This file is part of the Anitya project.
# Copyright (C) 2014 Red Hat, Inc.
# Copyright (C) 2014 Pierre-Yves Chibon <pingou@pingoured.fr>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""A collection of utilities for the Anitya library."""

import logging

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.exc import NoResultFound

from . import plugins, exceptions
from anitya.db import models, Base


_log = logging.getLogger(__name__)


def fedmsg_publish(*args, **kwargs):  # pragma: no cover
    ''' Try to publish a message on the fedmsg bus. '''
    # We catch Exception if we want :-p
    # pylint: disable=W0703
    # Ignore message about fedmsg import
    # pylint: disable=F0401
    kwargs['modname'] = 'anitya'
    kwargs['cert_prefix'] = 'anitya'
    kwargs['name'] = 'relay_inbound'
    kwargs['active'] = True
    try:
        import fedmsg
        fedmsg.publish(*args, **kwargs)
    except Exception as err:
        _log.error(str(err))


def check_project_release(project, session, test=False):
    ''' Check if the provided project has a new release available or not.

    :arg package: a Package object has defined in anitya.db.modelss.Project

    '''
    backend = plugins.get_plugin(project.backend)
    if not backend:
        raise exceptions.AnityaException(
            'No backend was found for "%s"' % project.backend)

    publish = False
    up_version = None
    max_version = None

    try:
        up_version = backend.get_version(project)
    except exceptions.AnityaPluginException as err:
        _log.exception("AnityaError catched:")
        project.logs = str(err)
        session.add(project)
        session.commit()
        raise

    if test:
        return up_version

    p_version = project.latest_version or ''

    if up_version:
        project.logs = 'Version retrieved correctly'

    if up_version and up_version not in project.versions:
        publish = True
        project.versions_obj.append(
            models.ProjectVersion(
                project_id=project.id,
                version=up_version
            )
        )

    odd_change = False
    if up_version and up_version != p_version:
        version_class = project.get_version_class()
        max_version = max(up_version, p_version, key=version_class)
        if project.latest_version and max_version != up_version:
            odd_change = True
            project.logs = 'Something strange occured, we found that this '\
                'project has released a version "%s" while we had the latest '\
                'version at "%s"' % (up_version, project.latest_version)
        else:
            project.latest_version = up_version

    if publish:
        log(
            session,
            project=project,
            topic="project.version.update",
            message=dict(
                project=project.__json__(),
                upstream_version=up_version,
                old_version=p_version,
                packages=[pkg.__json__() for pkg in project.packages],
                versions=project.versions,
                agent='anitya',
                odd_change=odd_change,
            ),
        )

    session.add(project)
    session.commit()


def _construct_substitutions(msg):
    """ Convert a fedmsg message into a dict of substitutions. """
    subs = {}
    for key1 in msg:
        if isinstance(msg[key1], dict):
            subs.update(dict([
                ('.'.join([key1, key2]), val2)
                for key2, val2 in _construct_substitutions(msg[key1]).items()
            ]))

        subs[key1] = msg[key1]

    return subs


def log(session, project=None, distro=None, topic=None, message=None):
    """ Take a partial fedmsg topic and message.

    Publish the message and log it in the db.
    """
    # A big lookup of fedmsg topics to models.Log template strings.
    templates = {
        'distro.add': '%(agent)s added the distro named: %(distro)s',
        'distro.edit': '%(agent)s edited distro name from: %(old)s to: '
                       '%(new)s',
        'distro.remove': '%(agent)s deleted the distro named: %(distro)s',
        'project.add': '%(agent)s added project: %(project)s',
        'project.add.tried': '%(agent)s tried to add an already existing '
                             'project: %(project)s',
        'project.edit': '%(agent)s edited the project: %(project)s fields: '
                        '%(changes)s',
        'project.flag': '%(agent)s flagged the project: %(project)s with '
                        'reason: %(reason)s',
        'project.flag.set': '%(agent)s set flag %(flag)s to %(state)s',
        'project.remove': '%(agent)s removed the project: %(project)s',
        'project.map.new': '%(agent)s mapped the name of %(project)s in '
                           '%(distro)s as %(new)s',
        'project.map.update': '%(agent)s update the name of %(project)s in '
                              '%(distro)s from: %(prev)s to: %(new)s',
        'project.map.remove': '%(agent)s removed the mapping of %(project)s '
                              'in %(distro)s',
        'project.version.remove': '%(agent)s removed the version %(version)s '
                                  'of %(project)s ',
        'project.version.update': 'new version: %(upstream_version)s found'
                                  ' for project %(project.name)s '
                                  '(project id: %(project.id)s).',
    }
    substitutions = _construct_substitutions(message)
    final_msg = templates[topic] % substitutions

    fedmsg_publish(topic=topic, msg=dict(
        project=project,
        distro=distro,
        message=message,
    ))

    models.Log.insert(
        session,
        user=message['agent'],
        project=project,
        distro=distro,
        description=final_msg)

    return final_msg


def init(db_url, alembic_ini=None, debug=False, create=False):  # pragma: no cover
    """ Create the tables in the database using the information from the
    url obtained.

    :deprecated: This function is deprecated as of Anitya 0.12. Use the
                 scoped session in :mod:`anitya.db`

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
        Base.metadata.create_all(engine)

    # Source: https://docs.sqlalchemy.org/en/latest/dialects/sqlite.html
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
        plugins.load_plugins(scopedsession)

    return scopedsession


def create_project(
        session, name, homepage, user_id, backend='custom',
        version_url=None, version_prefix=None, regex=None,
        check_release=False, insecure=False):
    """ Create the project in the database.

    """
    project = models.Project(
        name=name,
        homepage=homepage,
        backend=backend,
        version_url=version_url,
        regex=regex,
        version_prefix=version_prefix,
        insecure=insecure
    )

    session.add(project)

    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise exceptions.ProjectExists(project)
    except SQLAlchemyError as err:
        _log.exception(err)
        session.rollback()
        raise exceptions.AnityaException(
            'Could not add this project, already exists?')

    log(
        session,
        project=project,
        topic='project.add',
        message=dict(
            agent=user_id,
            project=project.name,
        )
    )
    session.commit()
    if check_release is True:
        check_project_release(project, session)
    return project


def edit_project(
        session, project, name, homepage, backend, version_url,
        version_prefix, regex, insecure, user_id, check_release=False):
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
    if version_url != project.version_url:
        old = project.version_url
        project.version_url = version_url.strip() if version_url else None
        if old != project.version_url:
            changes['version_url'] = {'old': old, 'new': project.version_url}
    if version_prefix != project.version_prefix:
        old = project.version_prefix
        project.version_prefix = version_prefix.strip() \
            if version_prefix else None
        if old != project.version_prefix:
            changes['version_prefix'] = {
                'old': old, 'new': project.version_prefix}
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
            log(
                session,
                project=project,
                topic='project.edit',
                message=dict(
                    agent=user_id,
                    project=project.name,
                    fields=list(changes.keys()),  # be backward compat
                    changes=changes,
                )
            )
            session.add(project)
            session.commit()
        if check_release is True:
            check_project_release(project, session)
    except SQLAlchemyError as err:
        _log.exception(err)
        session.rollback()
        raise exceptions.AnityaException(
            'Could not edit this project. Is there already a project '
            'with these name and homepage?')


def map_project(
        session, project, package_name, distribution, user_id,
        old_package_name=None, old_distro_name=None):
    """
    Map a project to a distribution.

    Args:
        session (sqlalchemy.orm.session.Session): The database session.
        project (anitya.db.modelss.Project): The project to map to a distribution.
        package_name (str): The name of the mapped package.
        distribution (str): The name of the distribution.
        user_id (str): The user ID.
        old_package_name (str): The name of the old package mapping, if this is being
            used to edit a mapping.
        old_distro_name (str): The name of the old distro of the package mapping, if this
            is being used to edit a mapping.
    """
    distribution = distribution.strip()

    distro_obj = models.Distro.get(session, distribution)

    if not distro_obj:
        distro_obj = models.Distro(name=distribution)
        log(
            session,
            distro=distro_obj,
            topic='distro.add',
            message=dict(
                agent=user_id,
                distro=distro_obj.name,
            )
        )
        session.add(distro_obj)
        try:
            session.flush()
        except SQLAlchemyError as err:  # pragma: no cover
            # We cannot test this situation
            session.rollback()
            raise exceptions.AnityaException(
                'Could not add the distribution %s to the database, '
                'please inform an admin.' % distribution, 'errors')

    pkgname = old_package_name or package_name
    distro = old_distro_name or distribution
    pkg = models.Packages.get(
        session, project.id, distro, pkgname)

    # See if the new mapping would clash with an existing mapping
    try:
        other_pkg = models.Packages.query.filter_by(
            distro=distribution, package_name=package_name).one()
    except NoResultFound:
        other_pkg = None
    if other_pkg:
        raise exceptions.AnityaInvalidMappingException(
            pkgname, distro, package_name, distribution,
            other_pkg.project.id, other_pkg.project.name)

    edited = None
    if not pkg:
        topic = 'project.map.new'
        if not other_pkg:
            pkg = models.Packages(
                distro=distro_obj.name,
                project_id=project.id,
                package_name=package_name
            )
        else:
            other_pkg.project = project
            pkg = other_pkg
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
        _log.exception(err)
        # We cannot test this situation
        session.rollback()
        raise exceptions.AnityaException(
            'Could not add the mapping of %s to %s, please inform an '
            'admin.' % (package_name, distribution))

    message = dict(
        agent=user_id,
        project=project.name,
        distro=distro_obj.name,
        new=package_name,
    )
    if edited:
        message['prev'] = old_package_name or package_name
        message['edited'] = edited

    log(
        session,
        project=project,
        distro=distro_obj,
        topic=topic,
        message=message,
    )

    return pkg


def flag_project(session, project, reason, user_email, user_id):
    """ Flag a project in the database.

    """

    flag = models.ProjectFlag(
        user=user_email,
        project=project,
        reason=reason)

    session.add(flag)

    try:
        session.flush()
    except SQLAlchemyError as err:
        _log.exception(err)
        session.rollback()
        raise exceptions.AnityaException(
            'Could not flag this project.')

    log(
        session,
        project=project,
        topic='project.flag',
        message=dict(
            agent=user_id,
            project=project.name,
            reason=reason,
            packages=[pkg.__json__() for pkg in project.packages],
        )
    )
    session.commit()
    return flag


def set_flag_state(session, flag, state, user_id):
    """ Change the state of a ProjectFlag in the database.

    """

    # Don't toggle the state or send a new fedmsg if the flag's
    # state wouldn't actually be changed.
    if flag.state == state:
        raise exceptions.AnityaException(
            'Flag state unchanged.')

    flag.state = state
    session.add(flag)

    try:
        session.flush()
    except SQLAlchemyError as err:
        _log.exception(err)
        session.rollback()
        raise exceptions.AnityaException(
            'Could not set the state of this flag.')

    log(
        session,
        topic='project.flag.set',
        message=dict(
            agent=user_id,
            flag=flag.id,
            state=state,
        )
    )
    session.commit()
    return flag


def get_last_cron(session):
    """ Retrieve the last log entry about the cron
    """
    return models.Run.last_entry(session)
