#!/usr/bin/python

import os
import sys
import subprocess
from prepare import *

activate_this_file = os.path.join(home,'venv','bin','activate_this.py')
print_prepare = True
if os.path.isfile(activate_this_file):
    execfile(activate_this_file, dict(__file__ = activate_this_file))
    if all([os.path.exists(openwsn_fw_dir),
            os.path.exists(openwsn_sw_dir),
            not any(should_install_pip_libraries())
            ]):
        print_prepare = False
        s = subprocess.Popen(['python','./helper-tool/helper.py']+sys.argv[1:])
        while s.poll() == None:
            try:
                s.wait()
            except KeyboardInterrupt:
                pass
        
if print_prepare:
    print 'PLEASE, RUN ./prepare.py'