# -*- coding: utf-8 -*-


# (c) 2016 - Copyright Red Hat Inc

"""
 The Anitya ecosystems API.

 Authors:
   Nick Coghlan <ncoghlan@redhat.com>

"""


class BaseEcosystem(object):
    """
    The base class that all the different ecosystems should extend.

    Attributes:
        name (str): The ecosystem name. This name is used to associate projects
            with an ecosystem and is user-facing. It is also used in URLs.
        default_backend (str): The default backend to use for projects in this
            ecosystem if they don't explicitly define one to use.
        default_version_scheme (str): The default version scheme to use for
            projects in this ecosystem if a they don't explicitly define one to
            use.
        aliases (list): A list of alternate names for this ecosystem. These
            should be lowercase.
    """

    name = None
    default_backend = None
    default_version_scheme = None
    aliases = []
