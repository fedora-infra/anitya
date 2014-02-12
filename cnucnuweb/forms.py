#-*- coding: utf-8 -*-

""" Forms used in Cnucnu Web. """

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
