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
import warnings

from fedora_messaging import message

ANITYA_URL = "https://release-monitoring.org/"


class ProjectMessage(message.Message):
    """
    Base class for every project message.

    Attributes:
        project_schema (str): Project schema definition
    """

    project_schema = {
        "type": "object",
        "properties": {
            "backend": {"type": "string"},
            "created_on": {"type": "number"},
            "ecosystem": {"type": "string"},
            "homepage": {"type": "string"},
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "regex": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "updated_on": {"type": "number"},
            "version": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "version_url": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "versions": {"type": "array", "items": {"type": "string"}},
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

    @property
    def project_backend(self):
        """Backend of the project."""
        return self.body["project"]["backend"]

    @property
    def project_ecosystem(self):
        """Ecosystem of the project."""
        return self.body["project"]["ecosystem"]

    @property
    def project_homepage(self):
        """Homepage url for project."""
        return self.body["project"]["homepage"]

    @property
    def project_id(self):
        """Id of the project in Anitya."""
        return self.body["project"]["id"]

    @property
    def project_name(self):
        """The name of the project."""
        return self.body["project"]["name"]

    @property
    def project_version(self):
        """The latest version associated with the project."""
        return self.body["project"]["version"]

    @property
    def project_versions(self):
        """The versions associated with the project."""
        return self.body["project"]["versions"]

    @property
    def project_url(self):
        """The project url in Anitya."""
        return ANITYA_URL + "projects/" + str(self.project_id) + "/"


class ProjectCreated(ProjectMessage):
    """The message sent when a new project is created in Anitya."""

    topic = "org.release-monitoring.prod.anitya.project.add"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_add.json",
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
            "project": ProjectMessage.project_schema,
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
        return "A new project, {}, was added to release-monitoring.".format(
            self.project_name
        )

    @property
    def agent(self):
        """User that did the action."""
        return self.body["message"]["agent"]


class ProjectEdited(ProjectMessage):
    """The message sent when a project is edited in Anitya."""

    topic = "org.release-monitoring.prod.anitya.project.edit"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_edit.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent when a project is edited in Anitya",
        "type": "object",
        "required": ["project", "message", "distro"],
        "properties": {
            "distro": {"type": "null"},
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "changes": {
                        "type": "object",
                        "properties": {
                            "new": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "old": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        },
                    },
                    "fields": {"type": "array", "items": {"type": "string"}},
                    "project": {"type": "string"},
                },
                "required": ["agent", "project", "changes", "fields"],
            },
            "project": ProjectMessage.project_schema,
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
        return "A project, {}, was edited in release-monitoring.".format(
            self.project_name
        )

    @property
    def agent(self):
        """User that did the action."""
        return self.body["message"]["agent"]


class ProjectDeleted(ProjectMessage):
    """The message sent when a project is deleted in Anitya."""

    topic = "org.release-monitoring.prod.anitya.project.remove"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_remove.json",
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
            "project": ProjectMessage.project_schema,
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
        return "A project, {}, was deleted in release-monitoring.".format(
            self.project_name
        )

    @property
    def agent(self):
        """User that did the action."""
        return self.body["message"]["agent"]


class ProjectFlag(ProjectMessage):
    """Sent when a new flag is created for a project."""

    topic = "org.release-monitoring.prod.anitya.project.flag"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_flag.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "required": ["project", "message"],
        "properties": {
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "packages": {
                        "type": "array",
                        "items": {
                            "distro": {"type": "string"},
                            "package_name": {"type": "string"},
                        },
                    },
                    "project": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["agent", "project", "packages"],
            },
            "project": ProjectMessage.project_schema,
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
        return "A flag was created on project {} in release-monitoring.".format(
            self.project_name
        )

    @property
    def agent(self):
        """User that did the action."""
        return self.body["message"]["agent"]

    @property
    def mappings(self):
        """
        Mappings of package name to distros for project.

        Returns:
            (list): List of mappings
        """
        return self.body["message"]["packages"]

    @property
    def flag_url(self):
        """The anitya url for the flag."""
        return ANITYA_URL + "flags/"

    @property
    def reason(self):
        """Reason for the flag creation."""
        return self.body["message"]["reason"]


class ProjectFlagSet(message.Message):
    """Sent when a flag is closed for a project."""

    topic = "org.release-monitoring.prod.anitya.project.flag.set"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_flag_set.json",
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

    def __str__(self):
        """
        Return a complete human-readable representation of the message, which
        in this case is equivalent to the summary.
        """
        return self.summary

    @property
    def summary(self):
        """Return a summary of the message."""
        return "A flag '{}' was {} in release-monitoring.".format(self.flag, self.state)

    @property
    def agent(self):
        """User that did the action."""
        return self.body["message"]["agent"]

    @property
    def flag(self):
        """The id of the flag."""
        return self.body["message"]["flag"]

    @property
    def flag_url(self):
        """The anitya url for the flag."""
        return ANITYA_URL + "flags/"

    @property
    def state(self):
        """The new state of the flag."""
        return self.body["message"]["state"]


class ProjectMapCreated(ProjectCreated):
    topic = "org.release-monitoring.prod.anitya.project.map.new"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_map_new.json",
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
            "project": ProjectMessage.project_schema,
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
        return "A new mapping was created for project {} in release-monitoring.".format(
            self.project_name
        )

    @property
    def distro(self):
        """Name of distro for new mapping."""
        return self.body["distro"]["name"]

    @property
    def agent(self):
        """User that did the action."""
        return self.body["message"]["agent"]

    @property
    def package_name(self):
        """Package name for the new mapping."""
        return self.body["message"]["new"]


class ProjectMapEdited(ProjectMessage):
    topic = "org.release-monitoring.prod.anitya.project.map.update"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_map_update.json",
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
            "project": ProjectMessage.project_schema,
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
        return "A mapping for project {} was edited in release-monitoring.".format(
            self.project_name
        )

    @property
    def distro(self):
        """Name of distro for mapping."""
        return self.body["distro"]["name"]

    @property
    def agent(self):
        """User that did the action."""
        return self.body["message"]["agent"]

    @property
    def edited(self):
        """List of edited fields."""
        return self.body["message"]["edited"]

    @property
    def package_name_new(self):
        """New package name for the mapping."""
        return self.body["message"]["new"]

    @property
    def package_name_prev(self):
        """Previous package name for the mapping."""
        return self.body["message"]["prev"]


class ProjectMapDeleted(ProjectMessage):
    topic = "org.release-monitoring.prod.anitya.project.map.remove"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_map_remove.json",
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
            "project": ProjectMessage.project_schema,
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
        return "A mapping for project {} was deleted in release-monitoring.".format(
            self.project_name
        )

    @property
    def agent(self):
        """User that did the action."""
        return self.body["message"]["agent"]

    @property
    def distro(self):
        """Name of distro for mapping."""
        return self.body["message"]["distro"]


class ProjectVersionUpdated(ProjectMessage):
    topic = "org.release-monitoring.prod.anitya.project.version.update"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_version_update.json",
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
                    "packages": {
                        "type": "array",
                        "items": {
                            "distro": {"type": "string"},
                            "package_name": {"type": "string"},
                        },
                    },
                    "project": ProjectMessage.project_schema,
                    "upstream_version": {"type": "string"},
                    "versions": {"type": "array", "items": {"type": "string"}},
                    "stable_versions": {"type": "array", "items": {"type": "string"}},
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
            "project": ProjectMessage.project_schema,
        },
    }

    def __init__(
        self, body=None, headers=None, topic=None, properties=None, severity=None
    ):
        """
        Message constructor.
        """
        super().__init__(body, headers, topic, properties, severity)
        warnings.warn(
            "ProjectVersionUpdated class is deprecated, please use ProjectVersionUpdatedV2 instead",
            DeprecationWarning,
            stacklevel=2,
        )

    def __str__(self):
        """
        Return a complete human-readable representation of the message, which
        in this case is equivalent to the summary.
        """
        return self.summary

    @property
    def summary(self):
        """Return a summary of the message."""
        return (
            "A new version '{}' was found for project {} in release-monitoring.".format(
                self.version, self.project_name
            )
        )

    @property
    def agent(self):
        """User that did the action."""
        return self.body["message"]["agent"]

    @property
    def old_version(self):
        """Old version of project."""
        return self.body["message"]["old_version"]

    @property
    def distros(self):
        """Distros mapped to project."""
        distros = []
        for package in self.body["message"]["packages"]:
            distros.append(package["distro"])
        return distros

    @property
    def mappings(self):
        """
        Mappings of package name to distros for project.

        Returns:
            (list): List of mappings
        """
        return self.body["message"]["packages"]

    @property
    def version(self):
        """The version that was found."""
        return self.body["message"]["upstream_version"]

    @property
    def versions(self):
        """All versions on the project."""
        return self.body["message"]["versions"]

    @property
    def stable_versions(self):
        """All stable versions on the project."""
        return self.body["message"]["stable_versions"]


class ProjectVersionUpdatedV2(ProjectMessage):
    topic = "org.release-monitoring.prod.anitya.project.version.update.v2"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_version_update_v2.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "required": ["project", "message", "distro"],
        "properties": {
            "distro": {"type": "null"},
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "old_version": {"type": "string"},
                    "packages": {
                        "type": "array",
                        "items": {
                            "distro": {"type": "string"},
                            "package_name": {"type": "string"},
                        },
                    },
                    "project": ProjectMessage.project_schema,
                    "upstream_versions": {"type": "array", "items": {"type": "string"}},
                    "versions": {"type": "array", "items": {"type": "string"}},
                    "stable_versions": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "agent",
                    "old_version",
                    "packages",
                    "project",
                    "upstream_versions",
                    "versions",
                    "stable_versions",
                ],
            },
            "project": ProjectMessage.project_schema,
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
        return "A new versions '{}' were found for project {} in release-monitoring.".format(
            ", ".join(self.upstream_versions), self.project_name
        )

    @property
    def agent(self):
        """User that did the action."""
        return self.body["message"]["agent"]

    @property
    def old_version(self):
        """Old version of project."""
        return self.body["message"]["old_version"]

    @property
    def distros(self):
        """Distros mapped to project."""
        distros = []
        for package in self.body["message"]["packages"]:
            distros.append(package["distro"])
        return distros

    @property
    def mappings(self):
        """
        Mappings of package name to distros for project.

        Returns:
            (list): List of mappings
        """
        return self.body["message"]["packages"]

    @property
    def upstream_versions(self):
        """The versions that were found in upstream."""
        return self.body["message"]["upstream_versions"]

    @property
    def versions(self):
        """All versions on the project."""
        return self.body["message"]["versions"]

    @property
    def stable_versions(self):
        """All stable versions on the project."""
        return self.body["message"]["stable_versions"]


class ProjectVersionDeleted(ProjectMessage):
    topic = "org.release-monitoring.prod.anitya.project.version.remove"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_project_version_remove.json",
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
            "project": ProjectMessage.project_schema,
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
        return "A version '{}' was deleted in project {} in release-monitoring.".format(
            self.version, self.project_name
        )

    @property
    def agent(self):
        """User that did the action."""
        return self.body["message"]["agent"]

    @property
    def version(self):
        """The version that was deleted."""
        return self.body["message"]["version"]
