"""Environment-related utilities"""

import os

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"

__all__ = ["TmpEnv"]


class TmpEnv(object):
    """Temporary environment variable setting."""

    def __init__(self, overwrite=False, **kwargs):
        if not overwrite:
            already_set = [k for k, v in kwargs.items() if os.getenv(k, v) != v]
            if already_set:
                msg = "{} variable(s) already set: {}".format(
                    len(already_set), ", ".join(already_set)
                )
                raise ValueError(msg)
        self._kvs = kwargs

    def __enter__(self):
        for k, v in self._kvs.items():
            os.environ[k] = v
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for k in self._kvs:
            try:
                del os.environ[k]
            except KeyError:
                pass
