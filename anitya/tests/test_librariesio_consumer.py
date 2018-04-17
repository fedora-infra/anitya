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
Tests for the libraries.io fedmsg consumer.
"""

from __future__ import absolute_import, unicode_literals

import unittest

import mock

from anitya import config
from anitya.db import Project
from anitya.lib.exceptions import AnityaPluginException, AnityaException
from anitya.librariesio_consumer import LibrariesioConsumer
from anitya.tests.base import DatabaseTestCase


@mock.patch('anitya.librariesio_consumer.initialize', mock.Mock())
class LibrariesioConsumerTests(DatabaseTestCase):

    def setUp(self):
        super(LibrariesioConsumerTests, self).setUp()

        self.supported_fedmsg = {
            'body': {
                'username': 'vagrant',
                'i': 236,
                'timestamp': 1488561045,
                'msg_id': '2017-630afdfd-4780-48ce-ba99-3a306d8de2d2',
                'topic': 'org.fedoraproject.dev.sse2fedmsg.librariesio',
                'msg': {
                    'retry': 500,
                    'data': {
                        'name': 'ImageMetaTag',
                        'project': {
                            'status': None,
                            'repository_url': 'https://github.com/SciTools-incubator/',
                            'latest_release_published_at': '2017-03-03 16:44:46 UTC',
                            'description': 'Tags images created by matplotlib with ...',
                            'language': 'Python',
                            'platform': 'Pypi',
                            'package_manager_url': 'https://pypi.org/project/ImageMetaTag/',
                            'latest_release_number': '0.6.9',
                            'rank': 4,
                            'stars': 1,
                            'keywords': [],
                            'normalized_licenses': ['BSD-3-Clause'],
                            'forks': 1,
                            'homepage': 'https://github.com/SciTools-incubator/image-meta-tag',
                            'name': 'ImageMetaTag'
                        },
                        'platform': 'Pypi',
                        'published_at': '2017-03-03 16:44:46 UTC',
                        'version': '0.6.9',
                        'package_manager_url': 'https://pypi.org/project/ImageMetaTag/0.6.9'
                    },
                    'event': 'event',
                    'id': None
                }
            }
        }
        self.mock_hub = mock.Mock(config={'environment': 'dev', 'topic_prefix': 'anitya'})

    def test_dev_environment_topics(self):
        """Assert when the environment is set to dev, the dev topic is used."""
        mock_hub = mock.Mock(config={'environment': 'dev', 'topic_prefix': 'anitya'})
        consumer = LibrariesioConsumer(mock_hub)

        self.assertEqual([u'anitya.dev.sse2fedmsg.librariesio'], consumer.topic)

    def test_prod_environment_topics(self):
        """Assert when the environment is set to prod, only the prod topic is used."""
        mock_hub = mock.Mock(config={'environment': 'prod', 'topic_prefix': 'anitya'})
        consumer = LibrariesioConsumer(mock_hub)

        self.assertEqual([u'anitya.prod.sse2fedmsg.librariesio'], consumer.topic)

    @mock.patch('anitya.librariesio_consumer._log')
    def test_no_ecosystem(self, mock_log):
        """Assert that messages about platforms we don't support are handled gracefully"""
        consumer = LibrariesioConsumer(self.mock_hub)
        unsupported_fedmsg = {
            'body': {
                'username': 'vagrant',
                'i': 211,
                'timestamp': 1488560762,
                'msg_id': '2017-a7dbddc2-8ce5-4291-9986-c8584ec97fdd',
                'topic': 'org.fedoraproject.dev.sse2fedmsg.librariesio',
                'msg': {
                    'retry': 500,
                    'data': {
                        'name': 'GreatProject',
                        'project': {
                            'status': None,
                            'repository_url': None,
                            'latest_release_published_at': '2017-03-03 00:00:00 UTC',
                            'description': 'A great description of the project',
                            'language': None,
                            'platform': 'GREAT',
                            'package_manager_url': 'https://example.com/GreatProject.git',
                            'latest_release_number': '1.5.0',
                            'rank': 0,
                            'stars': 0,
                            'keywords': [],
                            'normalized_licenses': ['GPL-3.0+'],
                            'forks': 0,
                            'homepage': 'https://example.com/GreatProject',
                            'name': 'GreatProject',
                        },
                        'platform': 'GREAT',
                        'published_at': '2017-03-03 00:00:00 UTC',
                        'version': '1.5.0',
                        'package_manager_url': 'https://example.com/GreatProject.git',
                    },
                    'event': 'event',
                    'id': None,
                }
            }
        }
        self.assertEqual(0, self.session.query(Project).count())
        consumer.consume(unsupported_fedmsg)
        self.assertEqual(0, self.session.query(Project).count())
        self.assertTrue('Dropped librariesio update' in mock_log.debug.call_args_list[0][0][0])

    def test_new_project_configured_off(self):
        """libraries.io events shouldn't create projects if the configuration is off."""
        consumer = LibrariesioConsumer(self.mock_hub)
        with mock.patch.dict(config.config, {'LIBRARIESIO_PLATFORM_WHITELIST': []}):
            consumer.consume(self.supported_fedmsg)
        self.assertEqual(0, self.session.query(Project).count())

    def test_new_project_configured_on(self):
        """Assert that a libraries.io event about an unknown project creates that project"""
        consumer = LibrariesioConsumer(self.mock_hub)
        with mock.patch.dict(config.config, {'LIBRARIESIO_PLATFORM_WHITELIST': ['pypi']}):
            consumer.consume(self.supported_fedmsg)
        self.assertEqual(1, self.session.query(Project).count())
        project = self.session.query(Project).first()
        self.assertEqual('ImageMetaTag', project.name)
        self.assertEqual('pypi', project.ecosystem_name)
        self.assertEqual('0.6.9', project.latest_version)

    @mock.patch('anitya.librariesio_consumer._log')
    @mock.patch('anitya.librariesio_consumer.utilities.create_project')
    def test_new_project_failure(self, mock_create, mock_log):
        """Assert failures to create projects are logged as errors."""
        mock_create.side_effect = AnityaException("boop")
        consumer = LibrariesioConsumer(self.mock_hub)
        with mock.patch.dict(config.config, {'LIBRARIESIO_PLATFORM_WHITELIST': ['pypi']}):
            consumer.consume(self.supported_fedmsg)
        self.assertEqual(0, self.session.query(Project).count())
        mock_log.error.assert_called_once_with(
            'A new project was discovered via libraries.io, %r, but we failed with "%s"',
            None, 'boop')

    def test_existing_project(self):
        """Assert that a libraries.io event about an existing project updates that project"""
        project = Project(
            name='ImageMetaTag',
            homepage='https://pypi.org/project/ImageMetaTag/',
            ecosystem_name='pypi',
            backend='PyPI',
        )
        self.session.add(project)
        self.session.commit()
        consumer = LibrariesioConsumer(self.mock_hub)

        self.assertEqual(1, self.session.query(Project).count())
        consumer.consume(self.supported_fedmsg)
        self.assertEqual(1, self.session.query(Project).count())
        project = self.session.query(Project).first()
        self.assertEqual('ImageMetaTag', project.name)
        self.assertEqual('pypi', project.ecosystem_name)
        self.assertEqual('0.6.9', project.latest_version)

    @mock.patch('anitya.librariesio_consumer.utilities.check_project_release')
    def test_existing_project_check_failure(self, mock_check):
        """Assert that when an existing project fails a version check nothing happens"""
        consumer = LibrariesioConsumer(self.mock_hub)
        mock_check.side_effect = AnityaPluginException()
        project = Project(
            name='ImageMetaTag',
            homepage='https://pypi.python.org/pypi/ImageMetaTag',
            ecosystem_name='pypi',
            backend='PyPI',
        )
        self.session.add(project)
        self.session.commit()
        self.assertEqual(1, self.session.query(Project).count())
        consumer.consume(self.supported_fedmsg)
        self.assertEqual(1, self.session.query(Project).count())
        project = self.session.query(Project).first()
        self.assertIs(project.latest_version, None)

    @mock.patch('anitya.librariesio_consumer._log')
    def test_mismatched_versions(self, mock_log):
        """Assert when libraries.io and Anitya disagree on version, it's logged"""
        consumer = LibrariesioConsumer(self.mock_hub)
        project = Project(
            name='ImageMetaTag',
            homepage='https://pypi.org/project/ImageMetaTag/',
            ecosystem_name='pypi',
            backend='PyPI',
        )
        self.session.add(project)
        self.session.commit()
        self.supported_fedmsg['body']['msg']['data']['version'] = '0.6.11'
        consumer.consume(self.supported_fedmsg)
        project = self.session.query(Project).first()
        self.assertEqual('0.6.9', project.latest_version)
        self.assertIn(
            'libraries.io has found an update (version %s) for project %r',
            mock_log.info.call_args_list[1][0],
        )


if __name__ == '__main__':
    unittest.main()
