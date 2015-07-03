#!/usr/bin/python

import os
import sys
import subprocess
import argparse
import shutil

PYTHON_RELEASE = ['2','7','8']

FIRMWARE_REPOSITORY     = 'https://github.com/openwsn-berkeley/openwsn-fw.git'
SOFTWARE_REPOSITORY     = 'https://github.com/openwsn-berkeley/openwsn-sw.git'

FIRMWARE_PATH           = '"build/wsn430v14_mspgcc/projects/common/03oos_openwsn_prog.ihex"'

openwsn_on_iotlab_dir = os.getcwd()
openwsn_on_iotlab_parentdir = os.path.join(openwsn_on_iotlab_dir,'..')
openwsn_fw_dir = os.path.join(openwsn_on_iotlab_parentdir,'openwsn-fw')
openwsn_sw_dir = os.path.join(openwsn_on_iotlab_parentdir,'openwsn-sw')
home = os.path.expanduser('~')
home_usr = os.path.join(home,'usr')
home_usr_local = os.path.join(home_usr,'local')
home_usr_local_bin = os.path.join(home_usr_local,'bin')
home_dotlocal = os.path.join(home,'.local')
home_dotlocal_bin = os.path.join(home_dotlocal,'bin')
python_dir = 'Python-{0}'.format('.'.join(PYTHON_RELEASE))
python_path = os.path.join(home,python_dir)

def parse_options():
    
    # main parser
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-fr','--firmwareRepository',
                        default     = None,
                        help        = 'sets the git remote repository to track for openwsn-fw',
                        )
    
    parser.add_argument('-fb','--firmwareBranch',
                        default     = None,
                        help        = 'sets the git branch to track for openwsn-fw',
                        )
    
    parser.add_argument('-sr','--softwareRepository',
                        default     = None,
                        help        = 'sets the git remote repository to track for openwsn-sw',
                        )
    
    parser.add_argument('-sb','--softwareBranch',
                        default     = None,
                        help        = 'sets the git branch to track for openwsn-sw',
                        )
    
    parser.add_argument('-u','--uninstall',
                        action      = 'store_true',
                        default     = False,
                        help        = 'uninstall openwsn-on-iotlab environment',
                        )
                        
    parser.add_argument('-d','--dagrootFirmwarePath',
                        default     = FIRMWARE_PATH,
                        help        = 'specify the dagroot firmware location',
                        )
    
    args = parser.parse_args()
    
    return args

def should_install_pip_libraries():

    # to be called when venv is activated
    
    install_fw_pip_libraries = False
    install_sw_pip_libraries = False
    
    if not os.path.isfile(os.path.join(home,'venv','bin','scons')):
        install_fw_pip_libraries = True
    s = subprocess.Popen(['pip','freeze'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,_ = s.communicate()
    packages_installed = stdout.strip().split('\n')
    with open(os.path.join(openwsn_sw_dir,'requirements.txt')) as f:
        packages_required = f.readlines()
    for package_required in packages_required:
        if not package_required.strip() in packages_installed:
            install_sw_pip_libraries = True
            break
    return install_fw_pip_libraries, install_sw_pip_libraries

def install(args):
    
    # download, untar, install Python 2.7, and append ~/usr/local/bin to the PATH environment variable
    
    os.chdir(home)
    if not os.path.isfile(os.path.join(home,'{0}.tgz'.format(python_dir))):
        subprocess.call(['wget','https://www.python.org/ftp/python/{0}/{1}.tgz'.format('.'.join(PYTHON_RELEASE),python_dir)])
    if not os.path.exists(python_path):
        subprocess.call(['tar','zxvf','{0}.tgz'.format(python_dir)])
    os.chdir(python_path)
    if not os.path.isfile(os.path.join(python_path,'Makefile')):
        subprocess.call(['./configure'])
    if not os.path.exists(home_usr_local):
        os.makedirs(home_usr_local)
    if not os.path.isfile(os.path.join(home_usr_local_bin,'python{0}'.format('.'.join(PYTHON_RELEASE[:2])))):
        subprocess.call(['make','altinstall','prefix={0}'.format(home_usr_local),'exec-prefix={0}'.format(home_usr_local)])
    if not os.path.isfile(os.path.join(home_usr_local_bin,'python')):
        os.symlink(os.path.join(home_usr_local_bin,'python{0}'.format('.'.join(PYTHON_RELEASE[:2]))), os.path.join(home_usr_local_bin,'python'))
    os.environ['PATH'] = ':'.join([home_usr_local_bin,os.environ['PATH']])
    
    # download get-pip, run it with Python 2.7, and append ~/.local/bin to the PATH environment variable
    
    os.chdir(home)
    if not os.path.isfile(os.path.join(home,'get-pip.py')):
        subprocess.call(['wget','--no-check-certificate','https://bootstrap.pypa.io/get-pip.py'])
    if not os.path.isfile(os.path.join(home_dotlocal_bin,'pip')):
        subprocess.call(['python','get-pip.py','--user'])
    os.environ['PATH'] = ':'.join([home_dotlocal_bin,os.environ['PATH']])
    
    # install virtualenv, create a new environment called venv and activate it
    
    if not os.path.isfile(os.path.join(home_dotlocal_bin,'virtualenv')):
        subprocess.call('pip install --install-option="--user" virtualenv',shell=True)
    if not os.path.exists(os.path.join(home,'venv')):
        subprocess.call(['virtualenv','venv'])
    activate_this_file = os.path.join(home,'venv','bin','activate_this.py')
    execfile(activate_this_file, dict(__file__ = activate_this_file))
    
    # git clone openwsn-fw and openwsn-sw; switch branches if required
    
    os.chdir(openwsn_on_iotlab_parentdir)
    if args.firmwareRepository is None:
        if not os.path.exists(openwsn_fw_dir):
            subprocess.call(['git','clone',FIRMWARE_REPOSITORY])
    else:
        if not os.path.exists(openwsn_fw_dir):
            subprocess.call(['git','clone',args.firmwareRepository])
        else:
            os.chdir(openwsn_fw_dir)
            s = subprocess.Popen(['git','remote','-v'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            stdout,stderr = s.communicate()
            if stderr:
                print stderr
                return
            if args.firmwareRepository != stdout.splitlines()[0].split('\t')[1].split()[0]:
                os.chdir(openwsn_on_iotlab_parentdir)
                shutil.rmtree(openwsn_fw_dir)
                subprocess.call(['git','clone',args.firmwareRepository])
    if args.firmwareBranch:
        os.chdir(openwsn_fw_dir)
        s = subprocess.Popen(['git','branch'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = s.communicate()
        branches = stdout.split(None)
        other_branches = []
        current_branch = None
        while branches:
            branch = branches.pop(0)
            if branch == '*':
                current_branch = branches.pop(0)
            else:
                other_branches.append(branch)
        if not (args.firmwareBranch is current_branch):
            if args.firmwareBranch is in other_branches:
                subprocess.call(['git','checkout',args.firmwareBranch])
            else:
                subprocess.call(['git','checkout','-b',args.firmwareBranch,'origin/{0}'.format(args.firmwareBranch)])
    os.chdir(openwsn_on_iotlab_parentdir)
    if args.softwareRepository is None:
        if not os.path.exists(openwsn_sw_dir):
            subprocess.call(['git','clone',SOFTWARE_REPOSITORY])
    else:
        if not os.path.exists(openwsn_sw_dir):
            subprocess.call(['git','clone',args.softwareRepository])
        else:
            os.chdir(openwsn_sw_dir)
            s = subprocess.Popen(['git','remote','-v'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            stdout,stderr = s.communicate()
            if stderr:
                print stderr
                return
            if args.softwareRepository != stdout.splitlines()[0].split('\t')[1].split()[0]:
                os.chdir(openwsn_on_iotlab_parentdir)
                shutil.rmtree(openwsn_sw_dir)
                subprocess.call(['git','clone',args.softwareRepository])
    if args.softwareBranch:
        os.chdir(openwsn_sw_dir)
        s = subprocess.Popen(['git','branch'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = s.communicate()
        branches = stdout.split(None)
        other_branches = []
        current_branch = None
        while branches:
            branch = branches.pop(0)
            if branch == '*':
                current_branch = branches.pop(0)
            else:
                other_branches.append(branch)
        if not (args.softwareBranch is current_branch):
            if args.softwareBranch is in other_branches:
                subprocess.call(['git','checkout',args.softwareBranch])
            else:
                subprocess.call(['git','checkout','-b',args.softwareBranch,'origin/{0}'.format(args.softwareBranch)])
    
    # install python libraries required
    
    install_fw_pip_libraries, install_sw_pip_libraries = should_install_pip_libraries()
    if install_fw_pip_libraries:
        subprocess.call(['pip','install','--egg','scons'])
    if install_sw_pip_libraries: 
        subprocess.call(['pip','install','-r',os.path.join(openwsn_sw_dir,'requirements.txt')])
    
    # create settings file for reservation (it can be modified by any user, without being tracked by git)
    
    if not os.path.isfile(os.path.join(openwsn_on_iotlab_dir,'helper-tool','settings.py')) or (args.dagrootFirmwarePath != FIRMWARE_PATH):
        with open(os.path.join(openwsn_on_iotlab_dir,'helper-tool','settings.py'),'w') as f:
            f.write('MOTETYPE        = "wsn430"\n')
            f.write('FW_REGULAR_PATH = {0}\n'.format(FIRMWARE_PATH))
            f.write('FW_DAGROOT_PATH = {0}\n'.format(args.dagrootFirmwarePath))
    
    # run auth-cli: once done, it won't be executed again in the future, unless ~/.iotlabrc is deleted (uninstall will never do it)
    
    if not os.path.isfile(os.path.join(home,'.iotlabrc')):
        s = subprocess.Popen('users',stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,_ = s.communicate()
        username = stdout.strip()
        subprocess.call(['auth-cli','-u',username])

def uninstall(args):
    if os.path.isfile(os.path.join(home,'{0}.tgz'.format(python_dir))):
        os.remove(os.path.join(home,'{0}.tgz'.format(python_dir)))
    if os.path.exists(python_path):
        shutil.rmtree(python_path)
    if os.path.exists(home_usr):
        shutil.rmtree(home_usr)
    if os.path.isfile(os.path.join(home,'get-pip.py')):
        os.remove(os.path.join(home,'get-pip.py'))
    if os.path.exists(home_dotlocal):
        shutil.rmtree(home_dotlocal)
    if os.path.exists(os.path.join(home,'venv')):
        shutil.rmtree(os.path.join(home,'venv'))
    if os.path.exists(openwsn_fw_dir):
        shutil.rmtree(openwsn_fw_dir)
    if os.path.exists(openwsn_sw_dir):
        shutil.rmtree(openwsn_sw_dir)
    

def main():
    args = parse_options()
    if args.uninstall:
        uninstall(args)
    else:
        install(args)

#============================ main ============================================

if __name__=="__main__":
    main()
