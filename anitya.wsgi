#!/usr/bin/python
import sys, os
sys.path.insert (0,'/opt/anitya/src')
os.chdir('/opt/anitya/src')

from anitya.app import create

application = create()
