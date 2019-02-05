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
"""
Unit tests for the anitya.lib.backends module.
"""
from __future__ import absolute_import, unicode_literals

import unittest
import re

import mock
import urllib.request as urllib
from urllib.error import URLError

from anitya.config import config
from anitya.lib import backends
from anitya.lib.exceptions import AnityaPluginException
from anitya.tests.base import AnityaTestCase
import anitya


class BaseBackendTests(AnityaTestCase):
    def setUp(self):
        super(BaseBackendTests, self).setUp()
        self.backend = backends.BaseBackend()
        self.headers = {
            "User-Agent": "Anitya {0} at release-monitoring.org".format(
                anitya.app.__version__
            ),
            "From": config.get("ADMIN_EMAIL"),
        }

    @mock.patch("anitya.lib.backends.http_session")
    def test_call_http_url(self, mock_http_session):
        """Assert HTTP urls are handled by requests"""
        url = "https://www.example.com/"
        self.backend.call_url(url)

        mock_http_session.get.assert_called_once_with(
            url, headers=self.headers, timeout=60, verify=True
        )

    @mock.patch("anitya.lib.backends.requests.Session")
    def test_call_insecure_http_url(self, mock_session):
        """Assert HTTP urls are handled by requests"""
        url = "https://www.example.com/"
        self.backend.call_url(url, insecure=True)

        insecure_session = mock_session.return_value.__enter__.return_value
        insecure_session.get.assert_called_once_with(
            url, headers=self.headers, timeout=60, verify=False
        )

    @mock.patch("urllib.request.urlopen")
    def test_call_ftp_url(self, mock_urllib):
        """Assert FTP urls are handled by requests"""
        url = "ftp://ftp.heanet.ie/debian/"
        req_exp = urllib.Request(url)
        req_exp.add_header("User-Agent", self.headers["User-Agent"])
        req_exp.add_header("From", self.headers["From"])
        self.backend.call_url(url)

        mock_urllib.assert_called_once_with(mock.ANY)

        args, kwargs = mock_urllib.call_args
        req = args[0]

        self.assertEqual(req_exp.get_full_url(), req.get_full_url())
        self.assertEqual(req_exp.header_items(), req.header_items())

    @mock.patch("urllib.request.urlopen")
    def test_call_ftp_url_decode(self, mock_urlopen):
        """Assert decoding is working"""
        url = "ftp://ftp.heanet.ie/debian/"
        exp_resp = "drwxr-xr-x  9 ftp  ftp  4096 Aug 23 09:02 debian\r\n"
        mc = mock.Mock()
        mc.read.return_value = b"drwxr-xr-x  9 ftp  ftp  4096 Aug 23 09:02 debian\r\n"
        mock_urlopen.return_value = mc
        resp = self.backend.call_url(url)

        self.assertEqual(resp, exp_resp)

    @mock.patch("urllib.request.urlopen")
    def test_call_ftp_url_decode_not_utf(self, mock_urlopen):
        """Assert decoding is working"""
        url = "ftp://ftp.heanet.ie/debian/"
        mc = mock.Mock()
        mc.read.return_value = b"\x80\x81"
        mock_urlopen.return_value = mc

        self.assertRaises(AnityaPluginException, self.backend.call_url, url)

    @mock.patch("urllib.request.urlopen")
    def test_call_ftp_url_Exceptions(self, mock_urllib):
        """Assert FTP urls are handled by requests"""
        mock_urllib.side_effect = URLError(mock.Mock("not_found"))
        url = "ftp://example.com"

        self.assertRaises(AnityaPluginException, self.backend.call_url, url)

    def test_expand_subdirs(self):
        """Assert expanding subdirs"""
        exp = "http://ftp.fi.muni.cz/pub/linux/fedora/linux/"
        url = self.backend.expand_subdirs("http://ftp.fi.muni.cz/pub/linux/fedora/*/")

        self.assertEqual(exp, url)

    @mock.patch(
        "anitya.lib.backends.BaseBackend.call_url",
        return_value="drwxr-xr-x  9 ftp  ftp  4096 Aug 23 09:02 debian\r\n",
    )
    def test_expand_subdirs_ftp(self, mock_call_url):
        """Assert expanding subdirs"""
        exp = "ftp://ftp.heanet.ie/debian/"
        url = self.backend.expand_subdirs("ftp://ftp.heanet.ie/deb*/")

        self.assertEqual(exp, url)


class GetVersionsByRegexTextTests(unittest.TestCase):
    """
    Unit tests for anitya.lib.backends.get_versions_by_regex_text
    """

    def test_get_versions_by_regex_for_text(self):
        """Assert finding versions with a simple regex in text works"""
        text = """
        some release: 0.0.1
        some other release: 0.0.2
        The best release: 1.0.0
        """
        regex = r"\d\.\d\.\d"
        mock_project = mock.Mock(version_prefix="")
        versions = backends.get_versions_by_regex_for_text(
            text, "url", regex, mock_project
        )
        self.assertEqual(sorted(["0.0.1", "0.0.2", "1.0.0"]), sorted(versions))

    def test_get_versions_by_regex_for_text_tuples(self):
        """Assert regex that result in tuples are joined into a string"""
        text = """
        some release: 0.0.1
        some other release: 0.0.2
        The best release: 1.0.0
        """
        regex = r"(\d)\.(\d)\.(\d)"
        mock_project = mock.Mock(version_prefix="")
        versions = backends.get_versions_by_regex_for_text(
            text, "url", regex, mock_project
        )
        self.assertEqual(sorted(["0.0.1", "0.0.2", "1.0.0"]), sorted(versions))
        # Demonstrate that the regex does result in an iterable
        self.assertEqual(3, len(re.findall(regex, "0.0.1")[0]))

    def test_get_versions_by_regex_for_text_no_versions(self):
        """Assert an exception is raised if no matches are found"""
        text = "This text doesn't have a release!"
        regex = r"(\d)\.(\d)\.(\d)"
        mock_project = mock.Mock(version_prefix="")
        self.assertRaises(
            AnityaPluginException,
            backends.get_versions_by_regex_for_text,
            text,
            "url",
            regex,
            mock_project,
        )


if __name__ == "__main__":
    unittest.main()
