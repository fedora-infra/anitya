#!/usr/bin/env python
#-*- coding: utf-8 -*-

import anitya
import anitya.app
import anitya.lib.exceptions
import anitya.lib.model

import fedmsg
import fedmsg.config

import logging

PBAR = True
try:
    from progressbar import Bar, ETA, Percentage, ProgressBar, RotatingMarker
except ImportError:
    PBAR = False


def fedmsg_init():
    config = fedmsg.config.load_config()
    config['active'] = True
    config['name'] = 'relay_inbound'
    config['cert_prefix'] = 'anitya'
    fedmsg.init(**config)


def main():
    ''' Retrieve all the packages and for each of them update the release
    version.
    '''
    session = anitya.app.SESSION
    LOG = logging.getLogger('anitya')
    LOG.setLevel(logging.CRITICAL)
    projects = anitya.lib.model.Project.all(session)

    if PBAR:
        widgets = ['Release update: ',
                   Percentage(),
                   ' ',
                   Bar(marker=RotatingMarker()),
                   ' ',
                   ETA()]
        pbar = ProgressBar(widgets=widgets, maxval=len(projects)).start()

    cnt = 0
    for project in projects:
        logging.info(project.name)
        try:
            anitya.check_release(project, session)
        except anitya.lib.exceptions.AnityaException as err:
            pass
        cnt += 1
        if PBAR:
            pbar.update(cnt)
    if PBAR:
        pbar.finish()


if __name__ == '__main__':
    fedmsg_init()
    main()
