#-*- coding: utf-8 -*-

""" Forms used in Cnucnu Web. """

from flask.ext import wtf
from wtforms import TextField, IntegerField, validators


class ProjectForm(wtf.Form):
    name = TextField('Project name', [validators.Required()])
    homepage = TextField('Homepage', [validators.Required()])
    version_url = TextField('Version URL', [validators.Required()])
    regex = TextField('Regex', [validators.Required()])
    fedora_name = TextField('Fedora package')
    debian_name = TextField('Debian package')

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor and fill in additional information.
        """
        super(ProjectForm, self).__init__(*args, **kwargs)

        if 'project' in kwargs:
            project = kwargs['project']
            self.name.data = project.name
            self.homepage.data = project.homepage
            self.version_url.data = project.version_url
            self.regex.data = project.regex
            self.fedora_name.data = project.fedora_name
            self.debian_name.data = project.debian_name
