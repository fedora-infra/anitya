# -*- coding: utf-8 -*-

"""
 (c) 2016 - Copyright Red Hat Inc

 Authors:
   Nick Coghlan <ncoghlan@redhat.com>

"""
from . import BaseEcosystem


class MavenEcosystem(BaseEcosystem):
    """ The Maven ecosystem class"""

    name = "maven"
    default_backend = "Maven Central"
