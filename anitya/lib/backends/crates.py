# -*- coding: utf-8 -*-

from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException

"""
 © 2017 Igor Gnatenko <ignatenkobrain@fedoraproject.org>

"""


class CratesBackend(BaseBackend):
    ''' The crates class for projects hosted on crates.io. '''

    name = 'crates.io'
    examples = [
        'https://crates.io/crates/clap',
        'https://crates.io/crates/serde',
    ]

    @classmethod
    def _get_versions(cls, project):
        url = 'https://crates.io/api/v1/crates/%s/versions' % project.name
        try:
            req = cls.call_url(url)
        except Exception:  # pragma: no cover
            raise AnityaPluginException('Could not contact %r' % url)

        try:
            data = req.json()
        except Exception:  # pragma: no cover
            raise AnityaPluginException('No JSON returned by %r' % url)

        return data['versions']

    @classmethod
    def get_version(cls, project):
        return self._get_versions(project)[0]['num']

    @classmethod
    def get_versions(cls, project):
        return [v['num'] for v in self._get_versions(project)]

    @classmethod
    def get_ordered_versions(cls, project):
        # crates API returns already ordered versions
        return self.get_versions()
