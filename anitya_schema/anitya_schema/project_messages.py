# Copyright (C) 2018  Red Hat, Inc.
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""The schema for project-related messages sent by Anitya."""

from fedora_messaging import message


project_schema = {
    "type": "object",
    "properties": {
        "backend": {"type": "string"},
        "created_on": {"type": "number"},
        "homepage": {"type": "string"},
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "regex": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "updated_on": {"type": "number"},
        "version": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "version_url": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "versions": {"type": "array"},
    },
    "required": [
        "backend",
        "created_on",
        "homepage",
        "id",
        "name",
        "regex",
        "updated_on",
        "version",
        "version_url",
        "versions",
    ],
}


class ProjectCreated(message.Message):
    """The message sent when a new project is created in Anitya."""

    topic = "org.release-monitoring.prod.anitya.project.add"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_createdv1.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent when a new project is created in Anitya",
        "type": "object",
        "required": ["project", "message", "distro"],
        "properties": {
            "distro": {"type": "null"},
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "project": {"type": "string"},
                },
                "required": ["agent", "project"],
            },
            "project": {
                "type": "object",
                "properties": {
                    "backend": {"type": "string"},
                    "created_on": {"type": "number"},
                    "homepage": {"type": "string"},
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "regex": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "updated_on": {"type": "number"},
                    "version": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "version_url": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "versions": {"type": "array"},
                },
                "required": [
                    "backend",
                    "created_on",
                    "homepage",
                    "id",
                    "name",
                    "regex",
                    "updated_on",
                    "version",
                    "version_url",
                    "versions",
                ],
            },
        },
    }

    def __str__(self):
        """
        Return a complete human-readable representation of the message, which
        in this case is equivalent to the summary.
        """
        return self.summary

    @property
    def summary(self):
        """Return a summary of the message."""
        return "A new project, {}, was added to release-monitoring.".format(self.name)

    @property
    def name(self):
        """The name of the project that was created."""
        return self._body["project"]["name"]


class ProjectEdited(message.Message):
    """The message sent when a project is edited in Anitya."""

    topic = "org.release-monitoring.prod.anitya.project.edit"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_createdv1.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent when a new project is created in Anitya",
        "type": "object",
        "required": ["project", "message", "distro"],
        "properties": {
            "distro": {"type": "null"},
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "project": {"type": "string"},
                },
                "required": ["agent", "project"],
            },
            "project": {
                "type": "object",
                "properties": {
                    "backend": {"type": "string"},
                    "created_on": {"type": "number"},
                    "homepage": {"type": "string"},
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "regex": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "updated_on": {"type": "number"},
                    "version": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "version_url": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "versions": {"type": "array"},
                },
                "required": [
                    "backend",
                    "created_on",
                    "homepage",
                    "id",
                    "name",
                    "regex",
                    "updated_on",
                    "version",
                    "version_url",
                    "versions",
                ],
            },
        },
    }

    def __str__(self):
        """
        Return a complete human-readable representation of the message, which
        in this case is equivalent to the summary.
        """
        return self.summary

    @property
    def summary(self):
        """Return a summary of the message."""
        return "A new project, {}, was added to release-monitoring.".format(self.name)

    @property
    def name(self):
        """The name of the project that was created."""
        return self._body["project"]["name"]


class ProjectDeleted(message.Message):
    """The message sent when a project is deleted in Anitya."""

    topic = "org.release-monitoring.prod.anitya.project.remove"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_deletedv1.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent when a project is deleted in Anitya",
        "type": "object",
        "required": ["project", "message", "distro"],
        "properties": {
            "distro": {"type": "null"},
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "project": {"type": "string"},
                },
                "required": ["agent", "project"],
            },
            "project": {
                "type": "object",
                "properties": {
                    "backend": {"type": "string"},
                    "created_on": {"type": "number"},
                    "homepage": {"type": "string"},
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "regex": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "updated_on": {"type": "number"},
                    "version": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "version_url": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "versions": {"type": "array"},
                },
                "required": [
                    "backend",
                    "created_on",
                    "homepage",
                    "id",
                    "name",
                    "regex",
                    "updated_on",
                    "version",
                    "version_url",
                    "versions",
                ],
            },
        },
    }

    def __str__(self):
        """
        Return a complete human-readable representation of the message, which
        in this case is equivalent to the summary.
        """
        return self.summary

    @property
    def summary(self):
        """Return a summary of the message."""
        return "A project, {}, was deleted in release-monitoring.".format(self.name)

    @property
    def name(self):
        """The name of the project that was created."""
        return self._body["project"]["name"]


class ProjectFlag(message.Message):
    """Sent when a new flag is created for a project."""

    topic = "org.release-monitoring.prod.anitya.project.flag"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya.project.flag.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "required": ["project", "message"],
        "properties": {
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "packages": {"type": "array"},
                    "project": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["agent", "project", "packages"],
            },
            "project": {
                "type": "object",
                "properties": {
                    "backend": {"type": "string"},
                    "created_on": {"type": "number"},
                    "homepage": {"type": "string"},
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "regex": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "updated_on": {"type": "number"},
                    "version": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "version_url": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "versions": {"type": "array"},
                },
                "required": [
                    "backend",
                    "created_on",
                    "homepage",
                    "id",
                    "name",
                    "regex",
                    "updated_on",
                    "version",
                    "version_url",
                    "versions",
                ],
            },
        },
    }


class ProjectFlagSet(message.Message):
    """Sent when a flag is closed for a project."""

    topic = "org.release-monitoring.prod.anitya.project.flag.set"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya.project.flag.set.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "required": ["message", "project", "distro"],
        "properties": {
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "flag": {"type": "integer"},
                    "state": {"type": "string"},
                },
                "required": ["agent", "flag", "state"],
            },
            "project": {"type": "null"},
            "distro": {"type": "null"},
        },
    }


class ProjectMapCreated(message.Message):
    topic = "org.release-monitoring.prod.anitya.project.map.new"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya.project.map.created.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "required": ["project", "message", "distro"],
        "properties": {
            "distro": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "distro": {"type": "string"},
                    "project": {"type": "string"},
                    "new": {"type": "string"},
                },
                "required": ["agent", "distro", "project", "new"],
            },
            "project": {
                "type": "object",
                "properties": {
                    "backend": {"type": "string"},
                    "created_on": {"type": "number"},
                    "homepage": {"type": "string"},
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "regex": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "updated_on": {"type": "number"},
                    "version": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "version_url": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "versions": {"type": "array"},
                },
                "required": [
                    "backend",
                    "created_on",
                    "homepage",
                    "id",
                    "name",
                    "regex",
                    "updated_on",
                    "version",
                    "version_url",
                    "versions",
                ],
            },
        },
    }


class ProjectMapEdited(message.Message):
    topic = "org.release-monitoring.prod.anitya.project.map.update"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya.project.map.updated.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "required": ["project", "message", "distro"],
        "properties": {
            "distro": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "distro": {"type": "string"},
                    "edited": {"type": "array"},
                    "new": {"type": "string"},
                    "prev": {"type": "string"},
                    "project": {"type": "string"},
                },
                "required": ["agent", "distro", "edited", "new", "prev", "project"],
            },
            "project": {
                "type": "object",
                "properties": {
                    "backend": {"type": "string"},
                    "created_on": {"type": "number"},
                    "homepage": {"type": "string"},
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "regex": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "updated_on": {"type": "number"},
                    "version": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "version_url": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "versions": {"type": "array"},
                },
                "required": [
                    "backend",
                    "created_on",
                    "homepage",
                    "id",
                    "name",
                    "regex",
                    "updated_on",
                    "version",
                    "version_url",
                    "versions",
                ],
            },
        },
    }


class ProjectMapDeleted(message.Message):
    topic = "org.release-monitoring.prod.anitya.project.map.remove"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya.project.map.deleted.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "required": ["project", "message", "distro"],
        "properties": {
            "distro": {"type": "null"},
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "distro": {"type": "string"},
                    "project": {"type": "string"},
                },
                "required": ["agent", "distro", "project"],
            },
            "project": {
                "type": "object",
                "properties": {
                    "backend": {"type": "string"},
                    "created_on": {"type": "number"},
                    "homepage": {"type": "string"},
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "regex": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "updated_on": {"type": "number"},
                    "version": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "version_url": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "versions": {"type": "array"},
                },
                "required": [
                    "backend",
                    "created_on",
                    "homepage",
                    "id",
                    "name",
                    "regex",
                    "updated_on",
                    "version",
                    "version_url",
                    "versions",
                ],
            },
        },
    }


class ProjectVersionUpdate(message.Message):
    topic = "org.release-monitoring.prod.anitya.project.version.update"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya.project.version.update.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "required": ["project", "message", "distro"],
        "properties": {
            "distro": {"type": "null"},
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "odd_change": {"type": "boolean"},
                    "old_version": {"type": "string"},
                    "packages": {"type": "array"},
                    "project": project_schema,
                    "upstream_version": {"type": "string"},
                    "versions": {"type": "array"},
                },
                "required": [
                    "agent",
                    "odd_change",
                    "old_version",
                    "packages",
                    "project",
                    "upstream_version",
                    "versions",
                ],
            },
            "project": project_schema,
        },
    }


class ProjectVersionDeleted(message.Message):
    topic = "org.release-monitoring.prod.anitya.project.version.remove"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya.project.version.update.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "required": ["project", "message", "distro"],
        "properties": {
            "distro": {"type": "null"},
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "project": {"type": "string"},
                    "version": {"type": "string"},
                },
                "required": ["agent", "project", "version"],
            },
            "project": project_schema,
        },
    }
