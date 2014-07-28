# -*- coding: utf-8 -*-
#
# Copyright © 2014  Red Hat, Inc.
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
#

'''
anitya tests for the flask application.
'''

__requires__ = ['SQLAlchemy >= 0.8']
import pkg_resources

import json
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import anitya
from anitya.lib import model
from tests import Modeltests, create_distro, create_project


class FlaskTest(Modeltests):
    """ Flask tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskTest, self).setUp()

        anitya.app.APP.config['TESTING'] = True
        anitya.SESSION = self.session
        anitya.ui.SESSION = self.session
        anitya.app.SESSION = self.session
        anitya.admin.SESSION = self.session
        anitya.api.SESSION = self.session
        self.app = anitya.app.APP.test_client()

    def test_index(self):
        """ Test the index function. """
        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)

        expected = """
      <h2><span class="glyphicon glyphicon-bullhorn"></span> Announce</h2>
      <p>We monitor upstream releases and broadcast them on
      <a href="http://fedmsg.com">fedmsg</a>, the FEDerated MeSsaGe bus. </p>
      <p>Use <a href="https://apps.fedoraproject.org/notifications">fedmsg
      notifications (FMN)</a>, to set up your own, <em>personalized</em>,
      alerts.</p>"""

        self.assertTrue(expected in output.data)

        expected = """
      <h2><span class="glyphicon glyphicon-search"></span> Search</h2>
      <p>Currently 0 projects are being monitored by Anitya.
      Your project of interest might be there, or not. To check it
      <a href="/projects/">browse the list of all projects</a>
      or simply search for them!</p>"""

        self.assertTrue(expected in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
