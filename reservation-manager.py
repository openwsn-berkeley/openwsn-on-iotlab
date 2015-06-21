#!/usr/bin/python

import os
import sys
import subprocess

activate_this_file = os.path.join('..','..','venv','bin','activate_this.py')
execfile(activate_this_file, dict(__file__ = activate_this_file))
try:
    subprocess.call(['python','helper.py']+sys.argv[1:])
except KeyboardInterrupt:
    print