#!/bin/bash

PYTHONPATH=anitya ./nosetests \
--with-coverage --cover-erase --cover-package=anitya $*
