# -*- coding: utf-8 -*-
#
# This file is part of the Anitya project.
# Copyright (C) 2014-2020 Red Hat, Inc.
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

import arrow
from fedora_messaging import api, message as fm_message, exceptions as fm_exceptions
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from anitya.db import models

from . import exceptions, plugins

_log = logging.getLogger(__name__)


def publish_message(topic, project=None, distro=None, message=None):  # pragma: no cover
    """Try to publish a message.

    Args:
        topic (str): Topic of the message
        project (dict): Dictionary representing project
        distro (str): Name of the distribution
        message (dict): Additional data needed for the topic
    """

    msg = dict(project=project, distro=distro, message=message)
    try:
        message_class = fm_message.get_class("anitya." + topic)
        api.publish(message_class(topic="anitya.{}".format(topic), body=msg))
    except (
        fm_exceptions.ConnectionException,
        fm_exceptions.PublishException,
    ) as err:
        # For now, continue just logging the error. Once the messaging has
        # been untangled into SQLAlchemy events, it should probably result
        # in an exception and the client should try again later.
        _log.error(str(err))


def check_project_release(project, session, test=False):
    """Check if the provided project has a new release available or not.

    :arg package: a Package object has defined in anitya.db.modelss.Project

    """
    backend = plugins.get_plugin(project.backend)
    if not backend:
        raise exceptions.AnityaException(
            'No backend was found for "%s"' % project.backend
        )

    if project.archived:
        raise exceptions.AnityaException(
            "Project is archived, can't check new versions"
        )

    publish = False
    versions_prefix = []
    max_version = ""

    # don't change actual data during test run
    if not test:
        project.last_check = arrow.utcnow().datetime
        project.next_check = project.last_check + backend.check_interval

    try:
        versions_prefix = backend.get_versions(project)
        _log.debug("Versions retrieved: '{}'".format(versions_prefix))
    except exceptions.RateLimitException as err:
        _log.error(f"{project.name} ({project.backend}): {str(err)}")
        if not test:
            project.logs = str(err)
            project.next_check = err.reset_time.to("utc").datetime
            project.check_successful = False
            session.add(project)
            session.commit()
        raise
    except exceptions.AnityaPluginException as err:
        _log.error(f"{project.name} ({project.backend}): {str(err)}")
        if not test:
            project.logs = str(err)
            project.check_successful = False
            project.error_counter += 1
            session.add(project)
            session.commit()
        raise

    # Remove prefix
    versions = project.create_version_objects(versions_prefix)

    # There is always at least one version retrieved,
    # otherwise this backend raises exception
    project.logs = "Version retrieved correctly"
    project.check_successful = True
    project.error_counter = 0

    p_versions = project.get_sorted_version_objects()
    old_version = project.latest_version or ""
    version_column_len = models.ProjectVersion.version.property.columns[0].type.length
    upstream_versions = []
    for version in versions:
        if version not in p_versions:
            if len(version.version) < version_column_len:
                project.versions_obj.append(
                    models.ProjectVersion(
                        project_id=project.id,
                        version=version.version,
                        commit_url=version.commit_url,
                    )
                )
                upstream_versions.append(version.parse())
            else:
                _log.info(
                    "Version '{}' was skipped. Reason: too long.".format(
                        version.version
                    )
                )

    sorted_versions = project.get_sorted_version_objects()
    if sorted_versions:
        max_version_obj = sorted_versions[0]
        max_version = max_version_obj.parse()
    if project.latest_version != max_version:
        project.latest_version = max_version
        publish = True
    else:
        project.logs = "No new version found"

    if test:
        return upstream_versions[::-1]

    if not test:
        if publish:
            publish_message(
                project=project.__json__(),
                topic="project.version.update",
                message=dict(
                    project=project.__json__(),
                    upstream_version=max_version,
                    old_version=old_version,
                    packages=[pkg.__json__() for pkg in project.packages],
                    versions=project.versions,
                    stable_versions=[
                        str(version) for version in project.stable_versions
                    ],
                    ecosystem=project.ecosystem_name,
                    agent="anitya",
                    odd_change=False,
                ),
            )

            publish_message(
                project=project.__json__(),
                topic="project.version.update.v2",
                message=dict(
                    project=project.__json__(),
                    upstream_versions=upstream_versions,
                    old_version=old_version,
                    packages=[pkg.__json__() for pkg in project.packages],
                    versions=project.versions,
                    stable_versions=[
                        str(version) for version in project.stable_versions
                    ],
                    ecosystem=project.ecosystem_name,
                    agent="anitya",
                ),
            )
        session.add(project)
        session.commit()


def create_project(
    session,
    name,
    homepage,
    user_id,
    backend="custom",
    version_scheme="RPM",
    version_pattern=None,
    version_url=None,
    version_prefix=None,
    pre_release_filter=None,
    version_filter=None,
    regex=None,
    insecure=False,
    releases_only=False,
    dry_run=False,
):
    """Create the project in the database."""
    project = models.Project(
        name=name,
        homepage=homepage,
        backend=backend,
        version_scheme=version_scheme,
        version_pattern=version_pattern,
        version_url=version_url,
        regex=regex,
        version_prefix=version_prefix,
        pre_release_filter=pre_release_filter,
        version_filter=version_filter,
        insecure=insecure,
        releases_only=releases_only,
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
        raise exceptions.AnityaException("Could not add this project, already exists?")

    if not dry_run:
        publish_message(
            project=project.__json__(),
            topic="project.add",
            message=dict(agent=user_id, project=project.name),
        )
        session.commit()
    return project


def edit_project(
    session,
    project,
    name,
    homepage,
    backend,
    version_scheme,
    version_pattern,
    version_url,
    version_prefix,
    pre_release_filter,
    version_filter,
    regex,
    insecure,
    releases_only,
    user_id,
    check_release=False,
    archived=False,
    dry_run=False,
):
    """Edit a project in the database."""
    changes = {}
    if name != project.name:
        old = project.name
        project.name = name.strip() if name else None
        changes["name"] = {"old": old, "new": project.name}
    if homepage != project.homepage:
        old = project.homepage
        project.homepage = homepage.strip() if homepage else None
        changes["homepage"] = {"old": old, "new": project.homepage}
    if backend != project.backend:
        old = project.backend
        project.backend = backend
        changes["backend"] = {"old": old, "new": project.backend}
    if version_scheme != project.version_scheme:
        old = project.version_scheme
        project.version_scheme = version_scheme
        changes["version_scheme"] = {"old": old, "new": project.version_scheme}
    if version_pattern != project.version_pattern:
        old = project.version_pattern
        project.version_pattern = version_pattern.strip() if version_pattern else None
        if old != project.version_pattern:
            changes["version_pattern"] = {"old": old, "new": project.version_pattern}
    if version_url != project.version_url:
        old = project.version_url
        project.version_url = version_url.strip() if version_url else None
        if old != project.version_url:
            changes["version_url"] = {"old": old, "new": project.version_url}
    if version_prefix != project.version_prefix:
        old = project.version_prefix
        project.version_prefix = version_prefix.strip() if version_prefix else None
        if old != project.version_prefix:
            changes["version_prefix"] = {"old": old, "new": project.version_prefix}
    if pre_release_filter != project.pre_release_filter:
        old = project.pre_release_filter
        project.pre_release_filter = (
            pre_release_filter.strip() if pre_release_filter else None
        )
        if old != project.pre_release_filter:
            changes["pre_release_filter"] = {
                "old": old,
                "new": project.pre_release_filter,
            }
    if version_filter != project.version_filter:
        old = project.version_filter
        project.version_filter = version_filter.strip() if version_filter else None
        if old != project.version_filter:
            changes["version_filter"] = {"old": old, "new": project.version_filter}
    if regex != project.regex:
        old = project.regex
        project.regex = regex.strip() if regex else None
        if old != project.regex:
            changes["regex"] = {"old": old, "new": project.regex}
    if insecure != project.insecure:
        old = project.insecure
        project.insecure = insecure
        changes["insecure"] = {"old": old, "new": project.insecure}
    if releases_only != project.releases_only:
        old = project.releases_only
        project.releases_only = releases_only
        changes["releases_only"] = {"old": old, "new": project.releases_only}
    if archived != project.archived:
        old = project.archived
        project.archived = archived
        changes["archived"] = {"old": old, "new": project.archived}

    try:
        if not dry_run:
            if changes:
                publish_message(
                    project=project.__json__(),
                    topic="project.edit",
                    message=dict(
                        agent=user_id,
                        project=project.name,
                        fields=list(changes.keys()),  # be backward compat
                        changes=changes,
                    ),
                )
                session.add(project)
                session.commit()
            if check_release is True:
                check_project_release(project, session)
        else:
            session.add(project)
            session.flush()
    except SQLAlchemyError as err:
        _log.exception(err)
        session.rollback()
        raise exceptions.AnityaException(
            "Could not edit this project. Is there already a project "
            "with these name and homepage?"
        )

    return changes


def map_project(
    session,
    project,
    package_name,
    distribution,
    user_id,
    old_package_name=None,
    old_distro_name=None,
):
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
        session.add(distro_obj)
        try:
            session.flush()
        except SQLAlchemyError:
            session.rollback()
            raise exceptions.AnityaException(
                "Could not add the distribution %s to the database, "
                "please inform an admin." % distribution,
                "errors",
            )

        publish_message(
            distro=distro_obj.__json__(),
            topic="distro.add",
            message=dict(agent=user_id, distro=distro_obj.name),
        )
        session.add(distro_obj)
        try:
            session.flush()
        except SQLAlchemyError:  # pragma: no cover
            # We cannot test this situation
            session.rollback()
            raise exceptions.AnityaException(
                "Could not add the distribution %s to the database, "
                "please inform an admin." % distribution,
                "errors",
            )

    pkgname = old_package_name or package_name
    distro = old_distro_name or distribution
    pkg = models.Packages.get(session, project.id, distro, pkgname)

    # See if the new mapping would clash with an existing mapping
    try:
        other_pkg = models.Packages.query.filter_by(
            distro_name=distribution, package_name=package_name
        ).one()
    except NoResultFound:
        other_pkg = None
    # Only raise exception if the package is already associated
    # to project
    if other_pkg and other_pkg.project:
        raise exceptions.AnityaInvalidMappingException(
            pkgname,
            distro,
            package_name,
            distribution,
            other_pkg.project.id,
            other_pkg.project.name,
        )

    edited = None
    if not pkg:
        topic = "project.map.new"
        if not other_pkg:
            pkg = models.Packages(
                distro_name=distro_obj.name,
                project_id=project.id,
                package_name=package_name,
            )
        else:
            other_pkg.project = project
            pkg = other_pkg
    else:
        topic = "project.map.update"
        edited = []
        if pkg.distro_name != distro_obj.name:
            pkg.distro_name = distro_obj.name
            edited.append("distribution")
        if pkg.package_name != package_name:
            pkg.package_name = package_name
            edited.append("package_name")

    session.add(pkg)
    try:
        session.flush()
    except SQLAlchemyError as err:
        _log.exception(err)
        session.rollback()
        raise exceptions.AnityaException(
            "Could not add the mapping of %s to %s, please inform an "
            "admin." % (package_name, distribution)
        )

    message = dict(
        agent=user_id, project=project.name, distro=distro_obj.name, new=package_name
    )
    if edited:
        message["prev"] = old_package_name or package_name
        message["edited"] = edited

    publish_message(
        project=project.__json__(),
        distro=distro_obj.__json__(),
        topic=topic,
        message=message,
    )

    return pkg


def flag_project(session, project, reason, user_email, user_id):
    """Flag a project in the database."""

    flag = models.ProjectFlag(user=user_email, project=project, reason=reason)

    session.add(flag)

    try:
        session.flush()
    except SQLAlchemyError as err:
        _log.exception(err)
        session.rollback()
        raise exceptions.AnityaException("Could not flag this project.")

    publish_message(
        project=project.__json__(),
        topic="project.flag",
        message=dict(
            agent=user_id,
            project=project.name,
            reason=reason,
            packages=[pkg.__json__() for pkg in project.packages],
        ),
    )
    session.commit()
    return flag


def set_flag_state(session, flag, state, user_id):
    """Change the state of a ProjectFlag in the database."""

    # Don't toggle the state or send a new message if the flag's
    # state wouldn't actually be changed.
    if flag.state == state:
        raise exceptions.AnityaException("Flag state unchanged.")

    flag.state = state
    session.add(flag)

    try:
        session.flush()
    except SQLAlchemyError as err:
        _log.exception(err)
        session.rollback()
        raise exceptions.AnityaException("Could not set the state of this flag.")

    publish_message(
        topic="project.flag.set",
        message=dict(agent=user_id, flag=flag.id, state=state),
    )
    session.commit()
    return flag


def get_last_cron(session):
    """Retrieve the last log entry about the cron"""
    return models.Run.last_entry(session)
