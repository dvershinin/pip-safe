"""Utilities for pip-safe"""
import errno
import logging as log  # for verbose output
import os
import subprocess
import sys
import tempfile


def make_sure_path_exists(path):
    try:
        original_umask = os.umask(0)
        # 0755 is required for /opt/safe-pip to be traversible
        # for home it is safe anyway
        os.makedirs(path, 0o755)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    finally:
        os.umask(original_umask)


def ensure_file_is_absent(file_path):
    """Remove file if it exists"""
    try:
        os.remove(file_path)
    except OSError:
        pass


def symlink(target, link_name, overwrite=False):
    """
    Create a symbolic link named link_name pointing to target.
    The whole point of this is being able to overwrite
    Whereas default Python os.symlink will fail on existing file
    See https://stackoverflow.com/questions/8299386/modifying-a-symlink-in-python
    """

    if not overwrite:
        os.symlink(target, link_name)
        return

    # os.replace() may fail if files are on different filesystems
    link_dir = os.path.dirname(link_name)

    # Create link to target with temporary filename
    while True:
        temp_link_name = tempfile.mktemp(dir=link_dir)

        # os.* functions mimic as closely as possible system functions
        # The POSIX symlink() returns EEXIST if link_name already exists
        # https://pubs.opengroup.org/onlinepubs/9699919799/functions/symlink
        # .html
        try:
            os.symlink(target, temp_link_name)
            break
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    # Replace link_name with temp_link_name
    try:
        # Pre-empt os.replace on a directory with a nicer message
        if os.path.isdir(link_name):
            raise IsADirectoryError(
                "Cannot symlink over existing directory: {}".format(link_name)
            )
        import six

        if six.PY2:
            os.rename(temp_link_name, link_name)
        else:
            os.replace(temp_link_name, link_name)
    except Exception:
        if os.path.islink(temp_link_name):
            os.remove(temp_link_name)
        raise


def call_subprocess(
    cmd,
    show_stdout=True,
    filter_stdout=None,
    cwd=None,
    raise_on_return_code=True,
    extra_env=None,
    remove_from_env=None,
    stdin=None,
):
    cmd_parts = []
    for part in cmd:
        if len(part) > 45:
            part = part[:20] + "..." + part[-20:]
        if " " in part or "\n" in part or '"' in part or "'" in part:
            part = '"{}"'.format(part.replace('"', '\\"'))
        if hasattr(part, "decode"):
            try:
                part = part.decode(sys.getdefaultencoding())
            except UnicodeDecodeError:
                part = part.decode(sys.getfilesystemencoding())
        cmd_parts.append(part)
    cmd_desc = " ".join(cmd_parts)
    if show_stdout:
        stdout = None
    else:
        stdout = subprocess.PIPE
    log.debug("Running command {}".format(cmd_desc))
    if extra_env or remove_from_env:
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        if remove_from_env:
            for var_name in remove_from_env:
                env.pop(var_name, None)
    else:
        env = None
    try:
        proc = subprocess.Popen(
            cmd,
            stderr=subprocess.STDOUT,
            stdin=None if stdin is None else subprocess.PIPE,
            stdout=stdout,
            cwd=cwd,
            env=env,
        )
    except Exception:
        e = sys.exc_info()[1]
        log.critical("Error {} while executing command {}".format(e, cmd_desc))
        raise
    all_output = []
    if stdout is not None:
        if stdin is not None:
            with proc.stdin:
                proc.stdin.write(stdin)

        encoding = sys.getdefaultencoding()
        fs_encoding = sys.getfilesystemencoding()
        with proc.stdout as stdout:
            while 1:
                line = stdout.readline()
                try:
                    line = line.decode(encoding)
                except UnicodeDecodeError:
                    line = line.decode(fs_encoding)
                if not line:
                    break
                line = line.rstrip()
                all_output.append(line)
                if filter_stdout:
                    level = filter_stdout(line)
                    if isinstance(level, tuple):
                        level, line = level
                    log.debug(level, line)
                    if not log.stdout_level_matches(level):
                        log.show_progress()
                else:
                    log.debug(line)
    else:
        proc.communicate(stdin)
    proc.wait()
    if proc.returncode:
        if raise_on_return_code:
            if all_output:
                log.debug("Complete output from command {}:".format(cmd_desc))
                log.debug(
                    "\n".join(all_output) + "\n----------------------------------------"
                )
            raise OSError(
                "Command {} failed with error code {}".format(cmd_desc, proc.returncode)
            )
        else:
            log.warning(
                "Command {} had error code {}".format(cmd_desc, proc.returncode)
            )
    return all_output
