#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of the Anitya project.
# Copyright (C) 2017-2019 Red Hat, Inc.
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
A `sseclient`_ wrapper that is designed to consumed `libraries.io firehose`_ SSE feed.

Using this, it is possible for Anitya to discover new upstream releases using
`libraries.io`_. At the moment, the SSE feed is served over HTTP, so we confirm
the release is really available upstream before announce the new version.

.. _libraries.io: https://libraries.io/
.. _libraries.io firehose: https://github.com/librariesio/firehose
.. _sseclient: https://pypi.python.org/pypi/sseclient/
"""
import logging
import json

from anitya import config
from anitya.db import models, Session, initialize
from anitya.lib import exceptions, plugins, utilities

from sseclient import SSEClient

_log = logging.getLogger(__name__)


class LibrariesioConsumer(object):
    """
    This class connects to the Server-Sent Events feed provided and creates or
    updates the project according to the event.

    Attributes:
        feed (str): The Server-Sent events feed URL.
        whitelist (list): Whitelisted platforms. See `https://libraries.io/`_
            for the list of available platforms.
    """

    def __init__(self):
        """
        Constructor loads relevant values from configuration.
        """
        self.feed = config.config["SSE_FEED"]
        self.whitelist = config.config["LIBRARIESIO_PLATFORM_WHITELIST"]
        _log.info("Subscribing to the following SSE feed: {}".format(self.feed))

        initialize(config.config)

    def run(self):  # pragma: no cover
        """
        Start the SSE client.
        This call is blocking and will continue until the underlying TCP
        connection is closed.
        """
        _log.info("Starting Server-Sent Events client for {}".format(self.feed))
        sse_stream = SSEClient(self.feed)
        for sse_message in sse_stream:
            # If the server sends too many newlines the client can generate
            # messages that are completely empty, so we filter those here.
            if sse_message.data:
                self.process_message(sse_message)
                _log.debug("Received message from SSE: {}".format(sse_message))

    def process_message(self, message):
        """
        This method is called when a incoming SSE message is received.

        If the project is unknown to Anitya, a new :class:`Project` is created,
        but only if the platform is whitelisted. See `self.whitelist`.
        If it's an existing project, this will call Anitya's ``check_project_release``
        API to update the latest version information. This is because we are
        subscribed to libraries.io over HTTP and therefore have no
        authentication.

        Checking the version ourselves serves two purposes. Firstly, we connect
        to libraries.io over HTTP so we don't have any authentication.
        Secondly, we might map the libraries.io project to the wrong Anitya
        project, so this is a good opportunity to catch those problems.

        Args:
            message (dict): The message to process.
        """
        # The SSE spec requires all data to be UTF-8 encoded
        try:
            librariesio_msg = json.loads(message.data, encoding="utf-8")
        except json.JSONDecodeError:
            _log.warning(
                "Dropping librariesio update message. Invalid json '{}'.".format(
                    message.data
                )
            )
            return
        name = librariesio_msg["name"]
        platform = librariesio_msg["platform"].lower()
        version = librariesio_msg["version"]
        homepage = librariesio_msg["package_manager_url"]
        for ecosystem in plugins.ECOSYSTEM_PLUGINS.get_plugins():
            if platform == ecosystem.name or platform in ecosystem.aliases:
                break
        else:
            _log.debug(
                "Dropped librariesio update to {} for {} ({}) since"
                " it is on the unsupported {} platform".format(
                    version, name, homepage, platform
                )
            )
            return

        session = Session()
        project = models.Project.query.filter_by(
            name=name, ecosystem_name=ecosystem.name
        ).one_or_none()
        if project is None and platform in self.whitelist:
            try:
                project = utilities.create_project(
                    session, name, homepage, "anitya", backend=ecosystem.default_backend
                )
                utilities.check_project_release(project, Session)
                _log.info(
                    "Discovered new project at version {} via libraries.io: {}".format(
                        version, project
                    )
                )
            except exceptions.AnityaException as e:
                _log.error(
                    "A new project was discovered via libraries.io, {}, "
                    'but we failed with "{}"'.format(name, str(e))
                )
        elif project is None:
            _log.info(
                "Discovered new project, {}, on the {} platform, but anitya is "
                "configured to not create the project".format(name, platform)
            )
        else:
            _log.info(
                "libraries.io has found an update (version {}) for project {}".format(
                    version, project.name
                )
            )
            # This will fetch the version, emit anitya message, add log entries, and
            # commit the transaction.
            try:
                utilities.check_project_release(project, session)
            except exceptions.AnityaPluginException as e:
                _log.warning(
                    "libraries.io found an update for {}, but we failed with {}".format(
                        project, str(e)
                    )
                )

        # Refresh the project object that was committed by either
        # ``create_project`` or ``check_project_release`` above
        project = models.Project.query.filter_by(
            name=name, ecosystem_name=ecosystem.name
        ).one_or_none()
        if project and project.latest_version != version:
            _log.info(
                "libraries.io found {} had a latest version of {}, but Anitya found {}".format(
                    project, version, project.latest_version
                )
            )

        Session.remove()


if __name__ == "__main__":
    """
    Main section.
    """
    client = LibrariesioConsumer()
    client.run()
