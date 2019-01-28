# -*- coding: utf-8 -*-
#
# This file is part of the Anitya project.
# Copyright (C) 2017 Red Hat, Inc.
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
"""
A `fedmsg consumer`_ that is designed to consume fedmsgs generated using
`sse2fedmsg`_ with the `libraries.io firehose`_ SSE feed.

Using this, it is possible for Anitya to discover new upstream releases using
`libraries.io`_. At the moment, the SSE feed is served over HTTP, so we confirm
the release is really available upstream before announce the new version.

When ``message`` is referenced in this module, it means the fedmsg that has been
deserialized to a Python dictionary with the following keys::
  {
    "body": {
      "username": "jcline",
      "i": 1,
      "timestamp": 1486743185,
      "msg_id": "2017-dcfee1a8-16d4-4684-afea-50aa24754677",
      "topic": "org.fedoraproject.dev.sse2fedmsg.libraryio",
      "msg": {
        "retry": 500,
        "data": {
          "name": "react-sh",
          "project": {
            "status": null,
            "repository_url": "https://github.com/heineiuo/react-sh",
            "latest_release_published_at": "2017-02-10 16:11:54 UTC",
            "description": "A super easy shell for react app.",
            "language": null,
            "platform": "NPM",
            "rank": 7,
            "keywords": [],
            "package_manager_url": "https://www.npmjs.com/package/react-sh",
            "stars": 0,
            "latest_release_number": "0.4.0",
            "normalized_licenses": [
              "MIT"
            ],
            "forks": 0,
            "homepage": "https://github.com/heineiuo/react-sh",
            "name": "react-sh"
          },
          "platform": "NPM",
          "published_at": "2017-02-10 16:11:54 UTC",
          "version": "0.4.0",
          "package_manager_url": "https://www.npmjs.com/package/react-sh"
        },
        "event": "event",
        "id": null
      }
    }
  }

Note that the contents of ``msg`` is the actual server-sent event converted to
JSON.


.. libraries.io: https://libraries.io/
.. libraries.io firehose: https://github.com/librariesio/firehose
.. sse2fedmsg: https://pypi.python.org/pypi/sse2fedmsg
.. fedmsg consumer: http://www.fedmsg.com/en/latest/consuming/#the-hub-consumer-approach
"""
from __future__ import absolute_import, unicode_literals

import logging

from fedmsg.consumers import FedmsgConsumer

from anitya import config
from anitya.db import models, Session, initialize
from anitya.lib import exceptions, plugins, utilities


_log = logging.getLogger(__name__)


class LibrariesioConsumer(FedmsgConsumer):
    """
    A fedmsg consumer.

    Attributes:
        topic (list): A list of strings that indicates the message topics this
            consumer gets. This consumer accepts a single topic,
            ``org.fedoraproject.prod.sse2fedmsg.libraryio``
        config_key (str): A string that must be set to `True` in the fedmsg
            configuration to enable this consumer.
    """
    topic = [
        'sse2fedmsg.librariesio',
    ]

    config_key = 'anitya.libraryio.enabled'

    def __init__(self, hub):
        # If we're in development mode, add the dev versions of the topics so
        # local playback with fedmsg-dg-replay works as expected.
        prefix, env = hub.config['topic_prefix'], hub.config['environment']
        self.topic = ['.'.join([prefix, env, topic]) for topic in self.topic]
        _log.info('Subscribing to the following fedmsg topics: %r', self.topic)

        initialize(config.config)

        super(LibrariesioConsumer, self).__init__(hub)
        hub.config['topic_prefix'] = "org.release-monitoring"

    def consume(self, message):
        """
        This method is called when a message with a topic this consumer
        subscribes to arrives.

        If the project is unknown to Anitya, a new :class:`Project` is created,
        but only if the 'create_librariesio_projects' configuration key is set.
        If it's an existing project, this will call Anitya's ``check_project_release``
        API to update the latest version information. This is because we are
        subscribed to libraries.io over HTTP and therefore have no
        authentication.

        Checking the version ourselves serves two purposes. Firstly, we connect
        to libraries.io over HTTP so we don't have any authentication.
        Secondly, we might map the libraries.io project to the wrong Anitya
        project, so this is a good opportunity to catch those problems.

        Args:
            message (dict): The fedmsg to process.
        """
        librariesio_msg = message['body']['msg']['data']
        name = librariesio_msg['name']
        platform = librariesio_msg['platform'].lower()
        version = librariesio_msg['version']
        homepage = librariesio_msg['package_manager_url']
        for ecosystem in plugins.ECOSYSTEM_PLUGINS.get_plugins():
            if platform == ecosystem.name or platform in ecosystem.aliases:
                break
        else:
            _log.debug('Dropped librariesio update to %s for %s (%s) since it is on the '
                       'unsupported %s platform', version, name, homepage, platform)
            return

        session = Session()
        project = models.Project.by_name_and_ecosystem(session, name, ecosystem.name)
        if project is None and platform in config.config['LIBRARIESIO_PLATFORM_WHITELIST']:
            try:
                project = utilities.create_project(
                    session,
                    name,
                    homepage,
                    'anitya',
                    backend=ecosystem.default_backend,
                    check_release=True,
                )
                _log.info('Discovered new project at version %s via libraries.io: %r',
                          version, project)
            except exceptions.AnityaException as e:
                _log.error('A new project was discovered via libraries.io, %r, '
                           'but we failed with "%s"', project, str(e))
        elif project is None:
            _log.info('Discovered new project, %s, on the %s platform, but anitya is '
                      'configured to not create the project', name, platform)
        else:
            _log.info('libraries.io has found an update (version %s) for project %r',
                      version, project)
            # This will fetch the version, emit fedmsgs, add log entries, and
            # commit the transaction.
            try:
                utilities.check_project_release(project, session)
            except exceptions.AnityaPluginException as e:
                _log.warning('libraries.io found an update for %r, but we failed with %s',
                             project, str(e))

        # Refresh the project object that was committed by either
        # ``create_project`` or ``check_project_release`` above
        project = models.Project.by_name_and_ecosystem(session, name, ecosystem.name)
        if project and project.latest_version != version:
            _log.info('libraries.io found %r had a latest version of %s, but Anitya found %s',
                      project, version, project.latest_version)

        Session.remove()
