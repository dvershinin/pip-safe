import argparse
import json
import logging
import os
import shutil

import six
import virtualenv
from tabulate import tabulate

from .__about__ import __version__
from .utils import symlink, make_sure_path_exists, ensure_file_is_absent, call_subprocess

log = logging.getLogger('pip-safe')


def confirm_smth(question):
    reply = str(six.moves.input(question + ' (y/Nn): ')).lower().strip()
    if reply and reply[0] == 'y':
        return True
    else:
        return False


def get_venvs_dir(system_wide=False):
    if not system_wide:
        return os.path.join(os.path.expanduser('~'), '.virtualenvs')
    else:
        return '/opt/pip-safe'


def get_bin_dir(system_wide=False):
    if not system_wide:
        return os.path.join(os.path.expanduser('~'), '.local', 'bin')
    else:
        return '/usr/local/bin'


def get_venv_dir(name, system_wide=False):
    # replace any slashes in the 'name', for a case when git URL is passed
    # as a dumb way to make result directory creatable
    name = name.replace('https://', '')
    name = name.replace('/', '_')
    # sanitize version specifier if user installs, e.g. lastversion==1.2.4
    name = name.split('==')[0]
    venvs_dir = get_venvs_dir(system_wide=system_wide)
    return os.path.join(venvs_dir, name)


def get_venv_pip(name, system_wide=False):
    venv_pip = os.path.join(
        get_venv_dir(name, system_wide=system_wide),
        'bin',
        'pip'
    )
    if not os.path.exists(venv_pip):
        return None

    return venv_pip


def get_venv_executable_names(name, system_wide=False):
    log.debug("Checking what was installed to virtualenv's bin")
    bin_names = []
    venv_pip = get_venv_pip(name, system_wide)
    if not venv_pip:
        return []
    # sanitize version specifier if user installs, e.g. lastversion==1.2.4
    main_package_name = name.split('==')[0]
    # if the passed name was a URL, we have to figure out the name of the "main"
    # package that was installed, by listing non-dependent packages and weeding
    # out known stuff like wheel and pip itself
    if name.startswith('git+'):
        list_cmd = [venv_pip, 'list', '--not-required', '--format', 'json']
        log.debug('Running {}'.format(list_cmd))
        list_output = call_subprocess(
                list_cmd,
                show_stdout=False,
                raise_on_return_code=False,
        )
        packages = json.loads(list_output[0])
        for package in packages:
            if package['name'] not in ['pip', 'setuptools', 'wheel']:
                main_package_name = package['name']
                break

    file_cmd = [venv_pip, 'show', '-f', main_package_name]
    log.debug('Running {}'.format(file_cmd))
    try:
        for line in call_subprocess(
                file_cmd,
                show_stdout=False,
                raise_on_return_code=True,
        ):
            line = line.strip()
            if line.startswith('../../../bin/'):
                basename = os.path.basename(line)
                bin_names.append(basename)
    except OSError:
        return []
    return bin_names


def get_current_version(name, system_wide=False):
    venv_pip = get_venv_pip(name, system_wide=system_wide)
    if venv_pip is None:
        return 'damaged (no inner pip)'
    try:
        p = call_subprocess([venv_pip, 'show', name],
                            show_stdout=False,
                            raise_on_return_code=False)
    except FileNotFoundError:
        return 'damaged (Python interpreter is not found)'
    v = 'n/a'
    package_not_found = False
    for line in p:
        if 'Version:' in line:
            v = line.split(':')[-1].strip()
        if 'Package(s) not found':
            package_not_found = True
    if v == 'n/a' and package_not_found:
        return 'empty!'
    return v


def install_package(name, system_wide=False, upgrade=False):
    # create and activate the virtual environment
    bin_dir = get_bin_dir(system_wide=system_wide)

    venv_dir = get_venv_dir(name, system_wide=system_wide)
    make_sure_path_exists(venv_dir)

    install_for = 'system-wide' if system_wide else 'for current user'
    create_virtualenv = True
    venv_pip = venv_dir + '/bin/pip'
    if upgrade:
        log.info(
            'Upgrading {} {} ...'.format(name, install_for)
        )
        # if pip is there, do not recreate virtualenv
        if os.path.exists(venv_pip):
            create_virtualenv = False
    else:
        log.info(
            'Installing {} {} ...'.format(name, install_for)
        )

    if create_virtualenv:
        log.debug('Creating virtualenv at {}'.format(venv_dir))
        try:
            virtualenv.create_environment(venv_dir)
        except AttributeError:
            # use cli_run for newer versions of virtualenv
            from virtualenv import cli_run
            cli_run([venv_dir])

    # before invoking pip, ensure it is the latest by upgrading it
    args = [venv_pip, 'install', '--upgrade', 'pip', '--quiet']
    # the env var is supposed to hide the "old version" warning emitted
    # in the very first run
    log.info('Ensuring latest pip in the virtualenv')
    log.debug("PIP_DISABLE_PIP_VERSION_CHECK=1 " + " ".join(args))
    call_subprocess(args, extra_env={'PIP_DISABLE_PIP_VERSION_CHECK': '1'})

    log.debug("Running pip install in the virtualenv {}".format(name))
    # call_subprocess here is used for convenience: since we already import
    # this, why not :)
    args = [venv_pip, 'install']
    if upgrade:
        args.append('-U')
    args.append(name)
    args.append('--quiet')
    try:
        call_subprocess(args)
    except OSError:
        # clean up virtualenv on pip error
        return remove_package(name, system_wide, confirmation_needed=False,
                              silent=True)

    pkg_bin_names = get_venv_executable_names(name, system_wide)
    for bin_name in pkg_bin_names:
        src = os.path.join(venv_dir, 'bin', bin_name)
        dst = os.path.join(bin_dir, bin_name)
        log.debug('Creating symlink: {} -> {}'.format(src, dst))
        make_sure_path_exists(bin_dir)
        symlink(src, dst, overwrite=True)

    if not pkg_bin_names:
        log.error(
            'The package does not seem to provide any executables.'
        )
        if confirm_smth('Shall I remove it as smth useless?'):
            remove_package(name, system_wide)
        else:
            log.info('Oh, alright. You can peak around in {}'.format(venv_dir))
    else:
        if not is_bin_in_path(system_wide):
            log.warning(
                '{} is not in PATH so you can only launch programs like "{}" '
                'by their complete filename, e.g. {} !'.format(
                    bin_dir, pkg_bin_names[0], bin_dir + '/' + pkg_bin_names[0]
                )
            )
            log.info("Setup your environment PATH variable by running: ")
            log.info(
                "echo 'export PATH=$PATH:{}' >> ~/.bashrc && source "
                "~/.bashrc".format(
                    bin_dir if system_wide else '$HOME/.local/bin'))
        else:
            log.info('Programs installed. You can run them by typing: {}'.format(', '.join(pkg_bin_names)))


def list_packages():
    all_packages = [['Package', 'Version']]

    if os.path.exists(get_venvs_dir()):
        user_package_names = next(os.walk(get_venvs_dir()))[1]
        user_packages = []
        for pkg_name in user_package_names:
            current_version = get_current_version(pkg_name)
            user_packages.append([pkg_name, current_version])
        all_packages.extend(user_packages)

    if os.path.exists(get_venvs_dir(system_wide=True)):
        system_package_names = next(os.walk(get_venvs_dir(system_wide=True)))[1]
        system_packages = []
        for pkg_name in system_package_names:
            current_version = get_current_version(pkg_name, system_wide=True)
            system_packages.append(['*' + pkg_name, current_version])
        all_packages.extend(system_packages)

    print(
        tabulate(all_packages, headers="firstrow")
    )


def is_bin_in_path(system_wide=False):
    if system_wide:
        # assume that /usr/local/bin is always in PATH
        # the assumption here is because we don't want to falsely emit warning
        # for sudo pip-safe --system install <foo>
        # such calls would not load profile stuff and fail to detect PATH properly
        return True
    path_env = os.environ['PATH']
    bin_dir = get_bin_dir(system_wide)
    path_dirs = path_env.split(':')
    return bin_dir in path_dirs


def remove_package(name, system_wide=False, confirmation_needed=True, silent=False):
    venv_dir = get_venv_dir(name, system_wide)
    if not os.path.exists(venv_dir):
        log.warning('Looks like {} already does not exist. Nothing to do'.format(
            venv_dir))
        return False
    if confirmation_needed:
        if not confirm_smth(
                'Are you sure you want to remove package "{}"'.format(name)):
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
    if silent:
        log.debug('Cleaned up {}'.format(name))
    else:
        log.info('{} was removed.'.format(name))


def main():
    parser = argparse.ArgumentParser(
        description='Safely install and remove PyPi (pip) programs '
                    'without breaking your system',
        prog='pip-safe')
    parser.add_argument('command', metavar='<command>', default=None,
                        choices=['install', 'update', 'upgrade', 'list', 'remove'],
                        help='Command to run, e.g. install, update, remove or list')
    parser.add_argument('package', metavar='package-name', nargs='?',
                        default=None)
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true')
    parser.add_argument('-y', '--assumeyes', dest='confirmation_needed',
                        action='store_false', default=True)
    parser.add_argument('--system', dest='system', action='store_true',
                        help='Install for all users')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {version}'.format(version=__version__))
    parser.set_defaults(verbose=False, verbose_more=False, system=False)
    args = parser.parse_args()

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    # create formatter
    fmt = '%(name)s - %(levelname)s - %(message)s' if args.verbose else '%(levelname)s: %(message)s'
    formatter = logging.Formatter(fmt)
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    log.addHandler(ch)

    if args.verbose:
        log.setLevel(logging.DEBUG)
        log.info("Verbose output.")
    else:
        log.setLevel(logging.INFO)

    if args.command == 'install':
        install_package(name=args.package,
                        system_wide=args.system)
    elif args.command in ['update', 'upgrade']:
        install_package(name=args.package,
                        system_wide=args.system,
                        upgrade=True)
    elif args.command == 'list':
        list_packages()
    elif args.command == 'remove':
        remove_package(name=args.package, system_wide=args.system,
                       confirmation_needed=args.confirmation_needed)
    else:
        log.error(
            'Unknown command "{}". Possible: install, list, remove'.format(
                args.command)
        )
