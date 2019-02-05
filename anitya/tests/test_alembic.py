# (c) 2017 - Copyright Red Hat Inc

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#   Pierre-Yves Chibon <pingou@pingoured.fr>
"""This test module contains tests for the migration system."""

import os
import subprocess
import unittest


REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestAlembic(unittest.TestCase):
    """This test class contains tests pertaining to alembic."""

    def test_alembic_history(self):
        """Enforce a linear alembic history.

        This test runs the `alembic history | grep ' (head), '` command,
        and ensure it returns only one line.
        """
        proc1 = subprocess.Popen(
            ["alembic", "history"], cwd=REPO_PATH, stdout=subprocess.PIPE
        )
        proc2 = subprocess.Popen(
            ["grep", " (head), "], stdin=proc1.stdout, stdout=subprocess.PIPE
        )

        stdout = proc2.communicate()[0]
        stdout = stdout.strip().split(b"\n")
        self.assertEqual(len(stdout), 1)
        proc1.communicate()
