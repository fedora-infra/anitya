# -*- coding: utf-8 -*-

"""
 (c) 2016 - Copyright Red Hat Inc

 Authors:
   Nick Coghlan <ncoghlan@redhat.com>

"""
from . import BaseEcosystem


class PypiEcosystem(BaseEcosystem):
    """ The PyPI ecosystem class"""

    name = "pypi"
    default_backend = "PyPI"
