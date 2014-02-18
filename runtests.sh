#!/bin/bash

PYTHONPATH=cnucnuweb ./nosetests \
--with-coverage --cover-erase --cover-package=cnucnuweb $*
