import argparse
import os
import logging as log  # for verbose output
import subprocess
import six

import virtualenv
from tabulate import tabulate
from .utils import symlink, make_sure_path_exists, ensure_file_is_absent
import shutil


def confirm_smth(question):
    reply = str(six.moves.input(question+' (y/Nn): ')).lower().strip()
    if reply[0] == 'y':
        return True
    else:
        return False


def get_venvs_dir(system_wide = False):
    if not system_wide:
        return os.path.join(os.path.expanduser('~'), '.virtualenvs')
    else:
        return '/opt/safe-pip'


def get_bin_dir(system_wide = False):
    if not system_wide:
        return os.path.join(os.path.expanduser('~'), '.local', 'bin')
    else:
        return '/usr/local/bin'


def get_venv_dir(name, system_wide = False):
    venvs_dir = get_venvs_dir(system_wide=system_wide)
    return os.path.join(venvs_dir, name)


def get_venv_pip(name, system_wide = False):
    return os.path.join(
        get_venv_dir(name, system_wide=system_wide),
        'bin',
        'pip'
    )

def get_venv_executable_names(name, system_wide = False):
    log.debug("Checking what was installed to virtualenv's bin")
    bin_names = []
    venv_pip = get_venv_pip(name, system_wide)
    file_cmd = [venv_pip, 'show', '-f', name]
    log.debug('Running {}'.format(file_cmd))
    for line in virtualenv.call_subprocess(
        file_cmd,
        show_stdout=False,
        raise_on_return_code=False,
    ):
        line = line.strip()
        if line.startswith('../../../bin/'):
            basename = os.path.basename(line)
            bin_names.append(basename)
    return bin_names


def get_current_version(name, system_wide = False):
    from email.parser import BytesHeaderParser
    venv_pip = get_venv_pip(name, system_wide=system_wide)
    p = subprocess.run([venv_pip, 'show', name], stdout=subprocess.PIPE)
    h = BytesHeaderParser().parsebytes(p.stdout)
    return h['Version']


def install_package(name, system_wide = False):
    # create and activate the virtual environment
    venvs_dir = get_venvs_dir(system_wide=system_wide)
    bin_dir = get_bin_dir(system_wide=system_wide)

    make_sure_path_exists(venvs_dir)

    venv_dir = os.path.join(venvs_dir, name)

    log.info('Installing {} {} ...'.format(name, 'system-wide' if system_wide else 'for current user'))
    log.debug('Creating virtualenv at {}'.format(venv_dir))
    virtualenv.create_environment(venv_dir)

    log.debug("Running virtualenv's pip install {}".format(name))
    # call_subprocess here is used for convinience: since we already import this, why not :)
    virtualenv.call_subprocess([venv_dir + '/bin/pip', 'install', name, '--quiet'])

    pkg_bin_names = get_venv_executable_names(name, system_wide)
    for bin_name in pkg_bin_names:
        src = os.path.join(venv_dir, 'bin', bin_name)
        dst = os.path.join(bin_dir, bin_name)
        log.debug('Creating symlink: {} -> {}'.format(src, dst))
        make_sure_path_exists(bin_dir)
        symlink(src, dst, overwrite=True)

    if not pkg_bin_names:
        log.error('The package does not seem to provide any executable script.')
        if confirm_smth('Shall I remove it as smth useless?'):
            remove_package(name, system_wide)
        else:
            log.info('Oh, alright. You can peak around in {}'.format(venv_dir))
    else:
        if not is_bin_in_path(system_wide):
            log.warn(
                '{} is not in PATH so you can only launch programs like "{}" by their complete filename, e.g. {} !'.format(
                    bin_dir, pkg_bin_names[0], bin_dir + '/' + pkg_bin_names[0]
                )
            )
            log.info("Setup your environment PATH variable by running: ")
            log.info("echo 'export PATH=$PATH:{}' >> ~/.bashrc && source ~/.bashrc".format(bin_dir if system_wide else '$HOME/.local/bin'))
        else:
            log.info('Programs installed: {}'.format(', '.join(pkg_bin_names)))
            log.info('Done!')


def list_packages():
    user_package_names = next(os.walk(get_venvs_dir()))[1]
    user_packages = [['Package', 'Version']]
    for pkg_name in user_package_names:
        current_version = get_current_version(pkg_name)
        user_packages.append([pkg_name, current_version])
    print(
        tabulate(user_packages, headers="firstrow")
    )

def is_bin_in_path(system_wide = False):
    path_env = os.environ['PATH']
    bin_dir = get_bin_dir(system_wide)
    path_dirs = path_env.split(':')
    return bin_dir in path_dirs


def remove_package(name, system_wide = False, confirmation_needed = True):
    venv_dir = get_venv_dir(name, system_wide)
    if not os.path.exists(venv_dir):
        log.warn('Looks like {} already does not exist. Nothing to do'.format(venv_dir))
        return False
    if confirmation_needed:
        if not confirm_smth('Are you sure you want to remove package "{}"'.format(name)):
            log.info('Deletion cancelled')
            return False
    pkg_bin_names = get_venv_executable_names(name, system_wide)
    bin_dir = get_bin_dir(system_wide=system_wide)

    for bin_name in pkg_bin_names:
        dst = os.path.join(bin_dir, bin_name)
        log.info('Removing symlink: {}'.format(dst))
        ensure_file_is_absent(dst)
    log.debug('Going to remove: {}'.format(venv_dir))
    if os.path.exists(venv_dir):
        shutil.rmtree(venv_dir)
    log.info('{} was removed.'.format(name))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', metavar='<command>', default=None)
    parser.add_argument('package', metavar='package-name', nargs='?', default=None)
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true')
    parser.add_argument('-y', '--assumeyes', dest='confirmation_needed', action='store_false', default=True)
    parser.add_argument('--system', dest='system', action='store_true')
    parser.set_defaults(verbose=False, verbose_more=False, system=False)
    args = parser.parse_args()

    if args.verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
        log.info("Verbose output.")
    else:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.INFO)

    if args.command == 'install':
        install_package(name=args.package, system_wide=args.system)
    elif args.command == 'list':
        list_packages()
    elif args.command == 'remove':
        remove_package(name=args.package, system_wide=args.system, confirmation_needed=args.confirmation_needed)
    else:
        log.error('Unknown command "{}". Possible: install, list, remove'.format(args.command))


