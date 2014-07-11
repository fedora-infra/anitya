# -*- coding: utf-8 -*-

import logging
import warnings

from pkg_resources import parse_version

import anitya.lib.plugins
import anitya.lib.exceptions


LOG = logging.getLogger('anitya')


def fedmsg_publish(*args, **kwargs):  # pragma: no cover
    ''' Try to publish a message on the fedmsg bus. '''
    # We catch Exception if we want :-p
    # pylint: disable=W0703
    # Ignore message about fedmsg import
    # pylint: disable=F0401
    kwargs['modname'] = 'anitya'
    try:
        import fedmsg
        fedmsg.publish(*args, **kwargs)
    except Exception, err:
        warnings.warn(str(err))


def order_versions(vlist):
    ''' For a provided list of versions, return the list ordered from the
    oldest to the newest version.
    '''
    return sorted(
        vlist,
        cmp=lambda x, y: cmp(parse_version(x), parse_version(y)))


def check_release(project, session):
    ''' Check if the provided project has a new release available or not.

    :arg package: a Package object has defined in anitya.lib.model.Project

    '''
    backend = anitya.lib.plugins.get_plugin(project.backend)
    if not backend:
        raise anitya.lib.exceptions.AnityaException(
            'No backend was found for "%s"' % project.backend)

    publish = False
    up_version = None
    max_version = None

    try:
        up_version = backend.get_version(project)
    except anitya.lib.exceptions.AnityaPluginException as err:
        LOG.exception("AnityaError catched:")
        project.logs = err.message
        session.add(project)
        session.commit()
        raise

    if up_version and up_version not in project.versions:
        project.versions_obj.append(
            anitya.lib.model.ProjectVersion(
                project_id=project.id,
                version=up_version
            )
        )

    p_version = project.latest_version or ''

    if up_version and up_version != p_version:
        max_version = order_versions([up_version, p_version])[-1]
        if max_version != up_version:
            project.logs = 'Something strange occured, we found that this '\
                'project has released a version "%s" while we had the latest '\
                'version at "%s"' % (up_version, project.latest_version)
        else:
            publish = True
            project.latest_version = up_version
            project.logs = 'Version retrieved correctly'

    if publish:
        fedmsg_publish(topic="project.version.update", msg=dict(
            project=project.__json__(),
            upstream_version=up_version,
            old_version=p_version,
            packages=[pkg.__json__() for pkg in project.packages],
            versions=project.versions,
        ))

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
        'project.add': '%(agent)s added project: %(project)s',
        'project.add.tried': '%(agent)s tried to add an already existing '
                             'project: %(project)s',
        'project.edit': '%(agent)s edited the fields: %(fields)s of '
                        'project: %(project)s',

        'project.remove': '%(agent)s removed the project: %(project)s',
        'project.map.new': '%(agent)s mapped the name of %(project)s in '
                           '%(distro)s as %(new)s',
        'project.map.update': '%(agent)s update the name of %(project)s in '
                              '%(distro)s from: %(prev)s to: %(new)s',
        'project.map.remove': '%(agent)s removed the mapping of %(project)s '
                              'in %(distro)s',
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
