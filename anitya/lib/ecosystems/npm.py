# -*- coding: utf-8 -*-

"""
 (c) 2016 - Copyright Red Hat Inc

 Authors:
   Nick Coghlan <ncoghlan@redhat.com>

"""
from . import BaseEcosystem


class NpmEcosystem(BaseEcosystem):
    """ The npm ecosystem class"""

    name = "npm"
    default_backend = "npmjs"
