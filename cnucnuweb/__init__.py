# -*- coding: utf-8 -*-

import logging

from cnucnu.package_list import Package
from cnucnu.errors import CnuCnuError
from cnucnu.helper import upstream_max


LOG = logging.getLogger(__name__)


def check_release(project, session):
    ''' Check if the provided project has a new release available or not.

    :arg package: a Package object has defined in cnucnuweb.model.Project

    '''
    pkg = Package(
        name=project.name,
        regex=project.regex,
        url=project.version_url,
    )

    updated = False

    up_version = None
    try:
        up_version = pkg.latest_upstream
    except CnuCnuError as err:
        LOG.exception("CnuCnuError catched:")
        project.logs = err.message
        updated = True

    p_version = project.version
    if not p_version:
        p_version = ''

    if up_version and up_version != p_version:

        max_version = upstream_max([up_version, p_version])
        updated = True
        if max_version != up_version:
            project.logs = 'Something strange occured, we found that this '\
                'project has released a version "%s" while we had the latest '\
                'version at "%s"' %(up_version, project.version)
        else:
            project.version = up_version
            project.logs = 'Version retrieved correctly'

    if updated:
        session.add(project)
    session.commit()
