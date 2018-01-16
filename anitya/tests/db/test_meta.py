# -*- coding: utf-8 -*-
#
# Copyright © 2018 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
import unittest

import mock

from anitya.db import meta, models
from anitya.tests.base import DatabaseTestCase, create_project


class InitalizeTests(unittest.TestCase):

    @mock.patch('anitya.db.meta.create_engine')
    @mock.patch('anitya.db.meta.Session')
    def test_initialize(self, mock_session, mock_create_engine):
        config = {'DB_URL': 'postgresql://postgres:pass@localhost/mydb'}
        engine = meta.initialize(config)
        mock_create_engine.assert_called_once_with(config['DB_URL'], echo=False)
        self.assertEqual(engine, mock_create_engine.return_value)
        mock_session.configure.assert_called_once_with(bind=engine)

    @mock.patch('anitya.db.meta.create_engine')
    @mock.patch('anitya.db.meta.event.listen')
    @mock.patch('anitya.db.meta.Session')
    def test_initalize_sqlite(self, mock_session, mock_listen, mock_create_engine):
        config = {'DB_URL': 'sqlite://', 'SQL_DEBUG': True}
        engine = meta.initialize(config)
        mock_create_engine.assert_called_once_with(config['DB_URL'], echo=True)
        mock_session.configure.assert_called_once_with(bind=engine)
        self.assertEqual(1, mock_listen.call_count)
        self.assertEqual(engine, mock_listen.call_args_list[0][0][0])
        self.assertEqual('connect', mock_listen.call_args_list[0][0][1])


class BaseQueryPaginateTests(DatabaseTestCase):
    """Tests for the BaseQuery queries."""

    def setUp(self):
        super(BaseQueryPaginateTests, self).setUp()
        self.query = meta.BaseQuery(models.Project, session=self.session)

    def test_defaults(self):
        """Assert paginate defaults to the first page and 25 items."""
        create_project(self.session)
        page = self.query.paginate()
        self.assertEqual(1, page.page)
        self.assertEqual(3, page.total_items)
        self.assertEqual(25, page.items_per_page)
        # Default ordering is just by id
        self.assertEqual(page.items[0].name, 'geany')
        self.assertEqual(page.items[1].name, 'subsurface')
        self.assertEqual(page.items[2].name, 'R2spec')

    def test_multiple_pages(self):
        """Assert multiple pages work with pagination."""
        create_project(self.session)
        page = self.query.paginate(items_per_page=2)
        page2 = self.query.paginate(page=2, items_per_page=2)
        self.assertEqual(1, page.page)
        self.assertEqual(3, page.total_items)
        self.assertEqual(2, page.items_per_page)
        self.assertEqual(page.items[0].name, 'geany')
        self.assertEqual(page.items[1].name, 'subsurface')

        self.assertEqual(2, page2.page)
        self.assertEqual(3, page2.total_items)
        self.assertEqual(2, page2.items_per_page)
        self.assertEqual(page2.items[0].name, 'R2spec')

    def test_no_results(self):
        """Assert an empty page is returned when page * items_per_page > total_items."""
        create_project(self.session)
        page = self.query.paginate(page=1000)
        self.assertEqual(1000, page.page)
        self.assertEqual(3, page.total_items)
        self.assertEqual(25, page.items_per_page)
        self.assertEqual(0, len(page.items))

    def test_nonsense_page(self):
        """Assert a page number less than 1 raises a ValueError."""
        self.assertRaises(ValueError, self.query.paginate, 0)
        self.assertRaises(ValueError, self.query.paginate, -1)

    def test_nonsense_items_per_page(self):
        """Assert an items_per_page number less than 1 raises a ValueError."""
        self.assertRaises(ValueError, self.query.paginate, 1, 0)
        self.assertRaises(ValueError, self.query.paginate, 1, -1)

    def test_order_by(self):
        """Assert you can alter the order of page results."""
        create_project(self.session)
        page = self.query.paginate(order_by=models.Project.name)
        self.assertEqual(1, page.page)
        self.assertEqual(3, page.total_items)
        self.assertEqual(25, page.items_per_page)
        self.assertEqual(page.items[0].name, 'R2spec')
        self.assertEqual(page.items[1].name, 'geany')
        self.assertEqual(page.items[2].name, 'subsurface')

    def test_as_dict(self):
        expected_dict = {
            u'items_per_page': 1,
            u'page': 1,
            u'total_items': 3,
            u'items': [{
                'id': 3,
                'backend': u'custom',
                'name': u'R2spec',
                'homepage': u'https://fedorahosted.org/r2spec/',
                'regex': None,
                'version': None,
                'version_url': None,
                'versions': [],
            }],
        }
        create_project(self.session)
        page = self.query.paginate(order_by=models.Project.name, items_per_page=1)
        actual_dict = page.as_dict()
        actual_dict['items'][0].pop('updated_on')
        actual_dict['items'][0].pop('created_on')
        self.assertEqual(expected_dict, actual_dict)
