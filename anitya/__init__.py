# -*- coding: utf-8 -*-

import logging
import re
import warnings

import fedmsg

import anitya.plugins


LOG = logging.getLogger(__name__)

def fedmsg_publish(*args, **kwargs):  # pragma: no cover
    ''' Try to publish a message on the fedmsg bus. '''
    ## We catch Exception if we want :-p
    # pylint: disable=W0703
    ## Ignore message about fedmsg import
    # pylint: disable=F0401
    kwargs['modname'] = 'anitya'
    try:
        import fedmsg
        fedmsg.publish(*args, **kwargs)
    except Exception, err:
        warnings.warn(str(err))


__rc_upstream_regex = re.compile("(.*?)\.?(-?(rc|pre|beta|alpha|dev)([0-9]*))",
                                 re.I)
__rc_release_regex = re.compile(r'0\.[0-9]+\.(rc|pre|beta|alpha|dev)([0-9]*)',
                                re.I)


def split_rc(version):
    """ Split (upstream) version into version and release candidate string +
    release candidate number if possible
    """
    match = __rc_upstream_regex.match(version)
    if not match:
        return (version, "", "")

    rc_str = match.group(3)
    if rc_str:
        v = match.group(1)
        rc_num = match.group(4)
        return (v, rc_str, rc_num)
    else:
        # if version contains a dash, but no release candidate string is found,
        # v != version, therefore use version here
        # Example version: 1.8.23-20100128-r1100
        # Then: v=1.8.23, but rc_str=""
        return (version, "", "")


def rpm_cmp(v1, v2):
    import rpm
    diff = rpm.labelCompare((None, v1, None), (None, v2, None))
    return diff


def rpm_max(list):
    list.sort(cmp=rpm_cmp)
    return list[-1]


def upstream_cmp(v1, v2):
    """ Compare two upstream versions

    :Parameters:
        v1 : str
            Upstream version string 1
        v2 : str
            Upstream version string 2

    :return:
        - -1 - second version newer
        - 0  - both are the same
        - 1  - first version newer

    :rtype: int

    """

    v1, rc1, rcn1 = split_rc(v1)
    v2, rc2, rcn2 = split_rc(v2)

    diff = rpm_cmp(v1, v2)
    if diff != 0:
        # base versions are different, ignore rc-status
        return diff

    if rc1 and rc2:
        # both are rc, higher rc is newer
        diff = cmp(rc1.lower(), rc2.lower())
        if diff != 0:
            # rc > pre > beta > alpha
            return diff
        if rcn1 and rcn2:
            # both have rc number
            return cmp(int(rcn1), int(rcn2))
        if rcn1:
            # only first has rc number, then it is newer
            return 1
        if rcn2:
            # only second has rc number, then it is newer
            return -1
        # both rc numbers are missing or same
        return 0

    if rc1:
        # only first is rc, then second is newer
        return -1
    if rc2:
        # only second is rc, then first is newer
        return 1

    # neither is a rc
    return 0


def upstream_max(list):
    list.sort(cmp=upstream_cmp)
    return list[-1]


def check_release(project, session):
    ''' Check if the provided project has a new release available or not.

    :arg package: a Package object has defined in anitya.lib.model.Project

    '''
    backend = anitya.plugins.get_plugin(project.backend)

    publish = False
    up_version = None
    max_version = None

    try:
        up_version = backend.get_version(project)
    except AnityaError as err:
        LOG.exception("AnityaError catched:")
        package.logs = err.message

    if up_version not in project.versions:
        project.versions_obj.append(
            anitya.lib.model.ProjectVersion(
                project_id=project.id,
                version=up_version
            )
        )

    p_version = project.latest_version or ''

    if up_version and up_version != p_version:
        max_version = upstream_max([up_version, p_version])
        if max_version != up_version:
            project.logs = 'Something strange occured, we found that this '\
                'project has released a version "%s" while we had the latest '\
                'version at "%s"' % (up_version, package.version)
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
                              '%(distro)s %(new)s',
                              # from: %(prev)s to: %(new)s',
        'project.map.remove': '%(agent)s removed the mapping of %(project)s'
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
