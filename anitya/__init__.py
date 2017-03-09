# -*- coding: utf-8 -*-

import logging

import anitya.lib.plugins
import anitya.lib.exceptions
# Import the events to ensure the event handlers are registered with SQLAlchemy
# This _really_ shouldn't have to happen here, but there's nasty circular
# dependencies that need to get fixed before this can be put somewhere
# reasonable
from anitya.lib import events  # noqa


__api_version__ = '1.0'


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


def check_release(project, session, test=False):
    ''' Check if the provided project has a new release available or not.

    :arg package: a Package object has defined in anitya.lib.model.Project

    '''
    backend = anitya.lib.plugins.get_plugin(project.backend)
    if not backend:
        raise anitya.lib.exceptions.AnityaException(
            'No backend was found for "%s"' % project.backend)

    publish = False
    up_version = None

    try:
        up_version = backend.get_version(project)
    except anitya.lib.exceptions.AnityaPluginException as err:
        _log.exception("AnityaError catched:")
        project.logs = str(err)
        session.add(project)
        session.commit()
        raise

    try:
        # This validates the string is a sane version and strips any leading
        # 'v'. In the future we will use this to sort releases, ignore
        # pre-releases (if configured to), note odd versions, etc.
        up_version = str(project.version_class(version=up_version))
    except anitya.lib.exceptions.InvalidVersion:
        pass

    if test:
        return up_version

    p_version = project.latest_version or ''

    if up_version:
        project.logs = 'Version retrieved correctly'

    if up_version and up_version not in project.versions:
        publish = True
        project.versions_obj.append(
            anitya.lib.model.ProjectVersion(
                project_id=project.id,
                version=up_version
            )
        )

    odd_change = False
    if up_version and up_version != p_version:
        _version = project.version_class(version=up_version)
        up_version_newer = _version.newer(project.versions)
        if project.latest_version and not up_version_newer:
            odd_change = True
            project.logs = 'Something strange occured, we found that this '\
                'project has released a version "%s" while we had the latest '\
                'version at "%s"' % (up_version, project.latest_version)
        else:
            project.latest_version = up_version

    if publish:
        anitya.log(
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

    # To avoid a circular import.
    import anitya.lib.model as model

    # A big lookup of fedmsg topics to model.Log template strings.
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

    model.Log.insert(
        session,
        user=message['agent'],
        project=project,
        distro=distro,
        description=final_msg)

    return final_msg
