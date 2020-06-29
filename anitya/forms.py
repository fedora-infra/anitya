# -*- coding: utf-8 -*-

""" Forms used in anitya. """

from wtforms import StringField, TextAreaField, validators, SelectField
from wtforms import BooleanField

from anitya.compat import FlaskForm


class TokenForm(FlaskForm):
    """
    Form for API tokens.

    Attributes:
        description (StringField): The human-readable API token description, useful
            for users to describe the token's purpose.
    """

    description = StringField("Token description", [validators.optional()])


class ProjectForm(FlaskForm):
    name = StringField("Project name", [validators.DataRequired()])
    homepage = StringField("Homepage", [validators.DataRequired(), validators.URL()])
    backend = SelectField(
        "Backend", [validators.DataRequired()], choices=[(item, item) for item in []]
    )
    version_url = StringField("Version URL", [validators.optional()])
    version_prefix = StringField("Version prefix", [validators.optional()])
    pre_release_filter = StringField("Pre-release filter", [validators.optional()])
    version_filter = StringField("Version filter", [validators.optional()])
    version_scheme = SelectField(
        "Version scheme", [validators.Required()], choices=[(item, item) for item in []]
    )
    version_pattern = StringField("Version pattern", [validators.optional()])
    regex = StringField("Regex", [validators.optional()])
    insecure = BooleanField("Use insecure connection", [validators.optional()])

    distro = SelectField("Distro (optional)", [validators.optional()], choices=[])
    package_name = StringField("Package (optional)", [validators.optional()])
    check_release = BooleanField(
        "Check latest release on submit", [validators.optional()]
    )
    releases_only = BooleanField(
        "Check releases instead of tags", [validators.optional()]
    )

    def __init__(self, *args, **kwargs):
        """Calls the default constructor with the normal argument but
        uses the list of backends provided to fill the choices of the
        drop-down list.
        """
        super(ProjectForm, self).__init__(*args, **kwargs)
        if "backends" in kwargs:
            self.backend.choices = [
                (backend, backend) for backend in sorted(kwargs["backends"])
            ]
        if "version_schemes" in kwargs:
            self.version_scheme.choices = [
                (version_scheme, version_scheme)
                for version_scheme in sorted(kwargs["version_schemes"])
            ]
        if "distros" in kwargs:
            self.distro.choices = [
                (distro, distro)
                for distro in sorted(kwargs["distros"], key=lambda s: s.lower())
            ]
            self.distro.choices.insert(0, ("", ""))


class FlagProjectForm(FlaskForm):
    reason = TextAreaField("Reason for flagging", [validators.DataRequired()])


class MappingForm(FlaskForm):
    distro = SelectField("Distribution", [validators.DataRequired()], choices=[])
    package_name = StringField("Package name", [validators.DataRequired()])

    def __init__(self, *args, **kwargs):
        """Calls the default constructor and fill in additional information."""
        super(MappingForm, self).__init__(*args, **kwargs)

        if "distros" in kwargs:
            self.distro.choices = [
                (distro, distro)
                for distro in sorted(kwargs["distros"], key=lambda s: s.lower())
            ]


class ConfirmationForm(FlaskForm):
    pass


class DistroForm(FlaskForm):
    name = StringField("Distribution name", [validators.DataRequired()])
