#-*- coding: utf-8 -*-

""" Forms used in anitya. """

from flask.ext import wtf
from wtforms import TextField, IntegerField, validators


class ProjectForm(wtf.Form):
    name = TextField('Project name', [validators.Required()])
    homepage = TextField('Homepage', [validators.Required()])

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor and fill in additional information.
        """
        super(ProjectForm, self).__init__(*args, **kwargs)

        if 'project' in kwargs:
            project = kwargs['project']
            self.name.data = project.name
            self.homepage.data = project.homepage


class MappingForm(wtf.Form):
    distro = TextField('Distribution', [validators.Required()])
    package_name = TextField('Package name', [validators.Required()])
    version_url = TextField('Version URL', [validators.Required()])
    regex = TextField('Regex', [validators.Required()])

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


class ConfirmationForm(wtf.Form):
    pass


class DistroForm(wtf.Form):
    name = TextField('Distribution name', [validators.Required()])

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor and fill in additional information.
        """
        super(DistroForm, self).__init__(*args, **kwargs)

        if 'distro' in kwargs:
            distro = kwargs['distro']
            self.name.data = distro.name
