# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.
"""This module runs flake8 on the entire code base"""

import os
import subprocess
import unittest


REPO_PATH = os.path.abspath(
    os.path.dirname(os.path.join(os.path.dirname(__file__), '../')))


class TestStyle(unittest.TestCase):
    """
    Run flake8 on the repository directory as part of the unit tests.

    This currently only checks the anitya package, not the unit tests.
    The unit tests will be incrementally styled.
    """

    def test_code_with_flake8(self):
        """Assert the code is PEP8-compliant"""
        enforced_paths = [
            'anitya/',
        ]

        enforced_paths = [os.path.join(REPO_PATH, p) for p in enforced_paths]

        flake8_command = ['flake8', '--max-line-length', '100'] + enforced_paths
        self.assertEqual(subprocess.call(flake8_command), 0)


if __name__ == '__main__':
    unittest.main()
