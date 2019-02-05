# -*- coding: utf-8 -*-

"""
 (c) 2016 - Copyright Red Hat Inc

 Authors:
   Nick Coghlan <ncoghlan@redhat.com>

"""
from . import BaseEcosystem


class RubygemsEcosystem(BaseEcosystem):
    """ The rubygems ecosystem class"""

    name = "rubygems"
    default_backend = "Rubygems"
