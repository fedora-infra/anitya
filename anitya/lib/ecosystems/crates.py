# -*- coding: utf-8 -*-

"""
 © 2017 Igor Gnatenko <ignatenkobrain@fedoraproject.org>

"""

from . import BaseEcosystem


class CratesEcosystem(BaseEcosystem):
    ''' The crates.io ecosystem class. '''

    name = 'crates.io'
    default_backend = 'crates.io'
