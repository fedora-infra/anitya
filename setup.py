#!/usr/bin/env python

"""
Setup script
"""

# Required to build on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

from setuptools import setup
import re

def get_project_version():
    """Read the declared version of the project from the source code"""
    version_file = "anitya/app.py"
    with open(version_file, "rb") as f:
        version_pattern = b"^__version__ = '(.+)'$"
        match = re.search(version_pattern, f.read(), re.MULTILINE)
    if match is None:
        err_msg = "No line matching  %r found in %r"
        raise ValueError(err_msg % (version_pattern, version_file))
    return match.groups()[0].decode("utf-8")

def get_requirements(requirements_file='requirements.txt'):
    """Get the contents of a file listing the requirements.

    :arg requirements_file: path to a requirements file
    :type requirements_file: string
    :returns: the list of requirements, or an empty list if
              `requirements_file` could not be opened or read
    :return type: list
    """

    lines = open(requirements_file).readlines()
    return [
        line.rstrip().split('#')[0]
        for line in lines
        if not line.startswith('#')
    ]


setup(
    name='anitya',
    description='anitya is a project to monitor upstream releases in a distro.',
    version=get_project_version(),
    author='Pierre-Yves Chibon',
    author_email='pingou@pingoured.fr',
    maintainer='Pierre-Yves Chibon',
    maintainer_email='pingou@pingoured.fr',
    license='GPLv2+',
    download_url='https://fedorahosted.org/releases/a/n/anitya/',
    url='https://fedorahosted.org/anitya/',
    packages=['anitya'],
    include_package_data=True,
    scripts=['files/anitya_cron.py'],
    install_requires=get_requirements(),
)
