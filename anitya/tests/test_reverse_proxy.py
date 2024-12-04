"""Test module for testing anitya.reverse_proxy."""

import unittest

import mock

from anitya.reverse_proxy import ReverseProxied


class ReverseProxiedCallTests(unittest.TestCase):
    """Unit tests for the :func:anitya.reverse_proxy.ReverseProxied.__call__."""

    def setUp(self):
        """Setup the tests."""
        self.wsgi_app = mock.Mock()
        self.config = {}
        self.reverse_proxy = ReverseProxied(self.wsgi_app, self.config)

    def test__call__preferred(self):
        """
        Test the correct schema is set when provided in config.
        """
        self.reverse_proxy.config = {"PREFERRED_URL_SCHEME": "https"}
        self.environ = {}

        self.reverse_proxy.__call__(self.environ, None)

        self.assertEqual(self.environ["wsgi.url_scheme"], "https")

    def test__call__forwarded(self):
        """
        Test the correct schema is set when in environ.
        """
        self.environ = {"HTTP_X_FORWARDED_PROTO": "https"}

        self.reverse_proxy.__call__(self.environ, None)

        self.assertEqual(self.environ["wsgi.url_scheme"], "https")

    def test__call__default(self):
        """
        Test that nothing is set when the value is not configured.
        """
        self.environ = {}

        self.reverse_proxy.__call__(self.environ, None)

        self.assertNotIn("wsgi.url_scheme", self.environ)
