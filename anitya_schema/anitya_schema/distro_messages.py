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
"""The schema for distribution-related messages sent by Anitya."""

from fedora_messaging import message


class DistroCreated(message.Message):
    """
    Message sent by Anitya to the "anitya.distro.add" topic when a new
    distribution is added.
    """

    topic = "org.release-monitoring.prod.anitya.distro.add"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_distro_createdv1.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent when a new distro is created in Anitya",
        "type": "object",
        "required": ["project", "message", "distro"],
        "properties": {
            "project": {"type": "null"},
            "message": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "distro": {"type": "string"},
                },
                "required": ["agent", "distro"],
            },
            "distro": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    }

    def __str__(self):
        """Return a complete human-readable representation of the message"""
        return self.summary

    @property
    def summary(self):
        """Return a short summary of the message."""
        return "A new distribution, {}, was added to release-monitoring.".format(self.name)

    @property
    def name(self):
        """The new distribution's name."""
        return self.body["distro"]["name"]


class DistroEdited(message.Message):
    """
    Message sent by Anitya when a distribution is edited.
    """

    topic = "org.release-monitoring.prod.anitya.distro.edit"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_distro_editedv1.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent when a new distro is created in Anitya",
        "type": "object",
        "required": ["project", "message", "distro"],
        "properties": {
            "project": {"type": "null"},
            "message": {
                "type": "object",
                "properties": {
                    "agent": {
                        "type": "string",
                        "description": "The user who made the change",
                    },
                    "new": {
                        "type": "string",
                        "description": "The new distribution name",
                    },
                    "old": {
                        "type": "string",
                        "description": "The old distribution name",
                    },
                },
                "required": ["agent", "old", "new"],
            },
            "distro": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    }

    def __str__(self):
        """Return a complete human-readable representation of the message"""
        return self.summary

    @property
    def summary(self):
        """Return a short summary of the message."""
        return "The name of the {} distribution changed to {}.".format(
            self.old_name, self.new_name
        )

    @property
    def new_name(self):
        """The distribution's new name."""
        return self.body["message"]["new"]

    @property
    def old_name(self):
        """The distribution's old name."""
        return self.body["message"]["old"]


class DistroDeleted(message.Message):
    """Message sent by Anitya when a distribution is removed."""

    topic = "org.release-monitoring.prod.anitya.distro.remove"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_distro_editedv1.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent when a distribution is deleted in Anitya.",
        "type": "object",
        "required": ["project", "message", "distro"],
        "properties": {
            "project": {"type": "null"},
            "message": {
                "type": "object",
                "properties": {
                    "agent": {
                        "type": "string",
                        "description": "The user who made the change",
                    },
                    "distro": {
                        "type": "string",
                        "description": "The distribution name",
                    },
                },
                "required": ["agent", "distro"],
            },
            "distro": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    }

    def __str__(self):
        """Return a complete human-readable representation of the message"""
        return self.summary

    @property
    def summary(self):
        """Return a short summary of the message."""
        return "The {} distribution was removed from release-monitoring.".format(
            self.name
        )

    @property
    def name(self):
        """The distribution's new name."""
        return self.body["message"]["distro"]
