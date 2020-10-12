#!/usr/bin/env python

"""
Setup script
"""

from setuptools import setup, find_packages
import re


def get_project_version():
    """Read the declared version of the project from the source code"""
    version_file = "anitya/__init__.py"
    with open(version_file, "rb") as f:
        version_pattern = b'^__version__ = "(.+)"$'
        match = re.search(version_pattern, f.read(), re.MULTILINE)
    if match is None:
        err_msg = "No line matching  %r found in %r"
        raise ValueError(err_msg % (version_pattern, version_file))
    return match.groups()[0].decode("utf-8")


def get_requirements(requirements_file="requirements.txt"):
    """Get the contents of a file listing the requirements.

    :arg requirements_file: path to a requirements file
    :type requirements_file: string
    :returns: the list of requirements, or an empty list if
              `requirements_file` could not be opened or read
    :return type: list
    """

    lines = open(requirements_file).readlines()
    dependencies = []
    for line in lines:
        maybe_dep = line.strip()
        if maybe_dep.startswith("#"):
            # Skip pure comment lines
            continue
        if maybe_dep.startswith("git+"):
            # VCS reference for dev purposes, expect a trailing comment
            # with the normal requirement
            __, __, maybe_dep = maybe_dep.rpartition("#")
        else:
            # Ignore any trailing comment
            maybe_dep, __, __ = maybe_dep.partition("#")
        # Remove any whitespace and assume non-empty results are dependencies
        maybe_dep = maybe_dep.strip()
        if maybe_dep:
            dependencies.append(maybe_dep)
    return dependencies


setup(
    name="anitya",
    description="anitya is a project to monitor upstream releases in a distro.",
    version=get_project_version(),
    author="Pierre-Yves Chibon",
    author_email="pingou@pingoured.fr",
    maintainer="Pierre-Yves Chibon",
    maintainer_email="pingou@pingoured.fr",
    license="GPLv2+",
    download_url="https://fedorahosted.org/releases/a/n/anitya/",
    url="https://fedorahosted.org/anitya/",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    packages=find_packages(exclude=["anitya.tests", "anitya.tests.*"]),
    include_package_data=True,
    scripts=[
        "anitya/check_service.py",
        "anitya/sar.py",
        "anitya/librariesio_consumer.py",
    ],
    install_requires=get_requirements(),
    test_suite="anitya.tests",
)
