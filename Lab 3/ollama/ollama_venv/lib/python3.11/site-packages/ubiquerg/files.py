"""Functions facilitating file operations"""

import os
import sys
import logging
import errno
import time

from warnings import warn
from tarfile import open as topen
from hashlib import md5

_LOGGER = logging.getLogger(__name__)


__all__ = [
    "checksum",
    "size",
    "filesize_to_str",
    "untar",
    "create_lock",
    "remove_lock",
    "wait_for_lock",
    "create_file_racefree",
    "make_lock_path",
]
FILE_SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
LOCK_PREFIX = "lock."


def checksum(path, blocksize=int(2e9)):
    """
    Generate a md5 checksum for the file contents in the provided path.

    :param str path: path to file for which to generate checksum
    :param int blocksize: number of bytes to read per iteration, default: 2GB
    :return str: checksum hash
    """
    m = md5()
    with open(path, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()


def size(path, size_str=True):
    """
    Gets the size of a file or directory or list of them in the provided path

    :param str|list path: path or list of paths to the file or directories
        to check size of
    :param bool size_str: whether the size should be converted to a
        human-readable string, e.g. convert B to MB
    :return int|str: file size or file size string
    """

    if isinstance(path, list):
        s_list = sum(filter(None, [size(x, size_str=False) for x in path]))
        return filesize_to_str(s_list) if size_str else s_list

    if os.path.isfile(path):
        s = os.path.getsize(path)
    elif os.path.isdir(path):
        s = 0
        symlinks = []
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    s += os.path.getsize(fp)
                else:
                    s += os.lstat(fp).st_size
                    symlinks.append(fp)
        if len(symlinks) > 0:
            _LOGGER.info(
                "{} symlinks were found: {}".format(len(symlinks), "\n".join(symlinks))
            )
    else:
        warn("size could not be determined for: {}".format(path))
        s = None
    return filesize_to_str(s) if size_str else s


def filesize_to_str(size):
    """
    Converts the numeric bytes to the size string

    :param int|float size: file size to convert
    :return str: file size string
    """
    if isinstance(size, (int, float)):
        for unit in FILE_SIZE_UNITS:
            if size < 1024:
                return "{}{}".format(round(size, 1), unit)
            size /= 1024
    warn(
        "size argument was neither an int nor a float, " "returning the original object"
    )
    return size


def untar(src, dst):
    """
    Unpack a path to a target folder.
    All the required directories will be created

    :param str src: path to unpack
    :param str dst: path to output folder
    """
    with topen(src) as tf:
        tf.extractall(path=dst)


def get_file_mod_time(pth):
    """
    Safely get last modification time for a file. Prevents situation when file
    is deleted between file existence check and last file modification check.

    :param str pth: file path to check
    :return float: number of seconds since Jan 1, 1970 00:00:00
    """
    try:
        return os.path.getmtime(pth)
    except Exception as e:
        _LOGGER.info(
            "Could not determine timestamp for '{}'. Returning current time. "
            "Caught exception: {}".format(pth, getattr(e, "message", repr(e)))
        )
        return time.time()


def wait_for_lock(lock_file, wait_max=30):
    """
    Just sleep until the lock_file does not exist

    :param str lock_file: Lock file to wait upon.
    :param int wait_max: max wait time if the file in question is already locked
    """
    sleeptime = 0.001
    first_message_flag = False
    dot_count = 0
    totaltime = 0
    ori_timestamp = None
    if os.path.isfile(lock_file):
        ori_timestamp = get_file_mod_time(lock_file)
    while os.path.isfile(lock_file):
        if first_message_flag is False:
            _LOGGER.info(f"Waiting for file lock: {os.path.basename(lock_file)}")
            # sys.stdout.write("Waiting for file lock: {} ".format(os.path.basename(lock_file)))
            first_message_flag = True
        else:
            sys.stdout.write(".")
            dot_count += 1
            if dot_count % 60 == 0:
                sys.stdout.write("")
        sys.stdout.flush()
        time.sleep(sleeptime)
        totaltime += sleeptime
        sleeptime = min((sleeptime + 0.1) * 1.25, 10)
        if totaltime >= wait_max:
            if os.path.isfile(lock_file):
                timestamp = get_file_mod_time(lock_file)
                if ori_timestamp and timestamp > ori_timestamp:
                    ori_timestamp = timestamp
                    totaltime = 0
                    sleeptime = 0
                    continue
                raise RuntimeError(
                    "The maximum wait time ({}) has been reached and the lock "
                    "file still exists.".format(wait_max)
                )
    if first_message_flag:
        _LOGGER.info(f" File unlocked: {os.path.basename(lock_file)}")


def create_file_racefree(file):
    """
    Creates a file, but fails if the file already exists.

    This function will thus only succeed if this process actually creates
    the file; if the file already exists, it will cause an
    OSError, solving race conditions.

    :param str file: File to create.
    :raise OSError: if the file to be created already exists
    """
    write_lock_flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(file, write_lock_flags)
    os.close(fd)
    return file


def make_lock_path(lock_name_base):
    """
    Create a collection of path to locks file with given name as bases.

    :param str | list[str] lock_name_base: Lock file names
    :return str | list[str]: Path to the lock files.
    """

    def _mk_lock(lnb):
        base, name = os.path.split(lnb)
        lock_name = name if name.startswith(LOCK_PREFIX) else LOCK_PREFIX + name
        return lock_name if not base else os.path.join(base, lock_name)

    return (
        [_mk_lock(x) for x in lock_name_base]
        if isinstance(lock_name_base, list)
        else _mk_lock(lock_name_base)
    )


def remove_lock(filepath):
    """
    Remove lock

    :param str filepath: path to the file to remove the lock for.
        Not the path to the lock!
    :return bool: whether the lock was found and removed
    """
    lock = make_lock_path(filepath)
    if os.path.exists(lock):
        os.remove(lock)
        return True
    return False


def _create_lock(lock_path, filepath, wait_max):
    try:
        create_file_racefree(lock_path)
    except FileNotFoundError:
        parent_dir = os.path.dirname(filepath)
        os.makedirs(parent_dir)
        _create_lock(lock_path, filepath, wait_max)
    except Exception as e:
        if e.errno == errno.EEXIST:
            # Rare case: file already exists;
            # the lock has been created in the split second since the
            # last lock existence check,
            # wait for the lock file to be gone, but no longer than
            # `wait_max`.
            _LOGGER.info(
                "The lock has been created in the split second since the "
                "last lock existence check. Waiting"
            )
            wait_for_lock(lock_path, wait_max)
            _create_lock(lock_path, filepath, wait_max)
        else:
            raise e


def create_lock(filepath, wait_max=10):
    """
    Securely create a lock file

    :param str filepath: path to a file to lock
    :param int wait_max: max wait time if the file in question is already locked
    """
    lock_path = make_lock_path(filepath)
    # wait until no lock is present
    wait_for_lock(lock_path, wait_max)
    _create_lock(lock_path, filepath, wait_max)
