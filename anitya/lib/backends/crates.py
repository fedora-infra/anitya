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
        '''
        Example of output:
        [
          {
            "crate": "itoa",
            "created_at": "2016-06-25T22:11:59Z",
            "dl_path": "/api/v1/crates/itoa/0.1.1/download",
            "downloads": 288856,
            "features": {},
            "id": 29172,
            "links": {
              "authors": "/api/v1/crates/itoa/0.1.1/authors",
              "dependencies": "/api/v1/crates/itoa/0.1.1/dependencies",
              "version_downloads": "/api/v1/crates/itoa/0.1.1/downloads"
            },
            "num": "0.1.1",
            "updated_at": "2016-06-25T22:11:59Z",
            "yanked": false
          }
        ]

        Schema is following:
        {
          "$schema": "http://json-schema.org/draft-04/schema#",
          "title": "crates.io versions",
          "description": "https://crates.io/api/v1/crates/$name/versions",
          "type": "array",
          "definitions": {
            "version": {
              "type": "object",
              "properties": {
                "crate":      { "type": "string" },
                "created_at": { "type": "string", "format": "date-time" },
                "dl_path":    { "type": "string" },
                "downloads":  { "type": "integer" },
                "features": {
                  "type": "object",
                  # FIXME: 0+ elements
                  # str: list(str)
                },
                "id":         { "type": "integer" },
                "links": {
                  "type": "object",
                  "properties": {
                    "authors":           { "type": "string" },
                    "dependencies":      { "type": "string" },
                    "version_downloads": { "type": "string" }
                  }
                  "required": ["authors", "dependencies", "version_downloads"]
                },
                "num":        { "type": "string" },
                "updated_at": { "type": "string", "format": "date-time" },
                "yanked":     { "type": "boolean" },
              },
              "required": ["crate", "created_at", "dl_path", "downloads", "features", "id", "links", "num", "updated_at", "yanked"]
            }
          },
          "items": {
            "anyOf": [
              { "$ref": "#/definitions/version" }
            ]
          },
        }

        :rtype: list
        '''
        url = 'https://crates.io/api/v1/crates/{}/versions'.format(project.name)
        try:
            req = cls.call_url(url)
        except requests.RequestException as e:  # pragma: no cover
            raise AnityaPluginException('Could not contact {url}: '
                                        '{reason!r}'.format(url=url, reason=e))

        try:
            data = req.json()
        except ValueError as e:  # pragma: no cover
            raise AnityaPluginException('Failed to decode JSON: {!r}'.format(e))

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
        return self.get_versions(project)
