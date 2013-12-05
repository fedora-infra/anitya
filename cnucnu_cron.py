#!/usr/bin/env python
#-*- coding: utf-8 -*-

import cnucnuweb
import cnucnuweb.app
import cnucnuweb.model

import logging

PBAR = True
try:
    from progressbar import Bar, ETA, Percentage, ProgressBar, RotatingMarker
except ImportError:
    PBAR = False

def main():
    ''' Retrieve all the packages and for each of them update the release
    version.
    '''
    session = cnucnuweb.app.SESSION
    projects = cnucnuweb.model.Project.all(session)

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
        cnucnuweb.check_release(project, session)
        cnt += 1
        if PBAR:
            pbar.update(cnt)
    if PBAR:
        pbar.finish()


if __name__ == '__main__':
    main()
