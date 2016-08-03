# -*- coding: utf-8 -*-

"""
 (c) 2016 - Copyright Red Hat Inc

 Authors:
   Nick Coghlan <ncoghlan@redhat.com>

"""


class BaseEcosystem(object):
    ''' The base class that all the different ecosystems should extend. '''

    name = None
    default_backend = None
