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
    description = StringField('Token description', [validators.optional()])


class ProjectForm(FlaskForm):
    name = StringField('Project name', [validators.DataRequired()])
    homepage = StringField(
        'Homepage', [validators.DataRequired(), validators.URL()])
    backend = SelectField(
        'Backend',
        [validators.DataRequired()],
        choices=[(item, item) for item in []]
    )
    version_url = StringField('Version URL', [validators.optional()])
    version_prefix = StringField('Version prefix', [validators.optional()])
    regex = StringField('Regex', [validators.optional()])
    insecure = BooleanField(
        'Use insecure connection', [validators.optional()])

    distro = StringField('Distro (optional)', [validators.optional()])
    package_name = StringField('Package (optional)', [validators.optional()])
    check_release = BooleanField(
        'Check latest release on submit', [validators.optional()])

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        uses the list of backends provided to fill the choices of the
        drop-down list.
        """
        super(ProjectForm, self).__init__(*args, **kwargs)
        if 'backends' in kwargs:
            self.backend.choices = [
                (backend, backend) for backend in sorted(kwargs['backends'])
            ]


class FlagProjectForm(FlaskForm):
    reason = TextAreaField('Reason for flagging', [validators.DataRequired()])


class MappingForm(FlaskForm):
    distro = StringField('Distribution', [validators.DataRequired()])
    package_name = StringField('Package name', [validators.DataRequired()])

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor and fill in additional information.
        """
        super(MappingForm, self).__init__(*args, **kwargs)

        if 'package' in kwargs:
            package = kwargs['package']
            self.distro.data = package.distro
            self.package_name.data = package.package_name
            self.version_url.data = package.version_url
            self.regex.data = package.regex


class ConfirmationForm(FlaskForm):
    pass


class DistroForm(FlaskForm):
    name = StringField('Distribution name', [validators.DataRequired()])
