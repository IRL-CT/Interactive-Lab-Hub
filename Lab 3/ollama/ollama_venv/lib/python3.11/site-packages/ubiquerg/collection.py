"""Tools for working with collections"""

import itertools
import sys
from warnings import warn

if sys.version_info < (3, 3):
    from collections import Iterable
else:
    from collections.abc import Iterable, Mapping

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


__all__ = [
    "is_collection_like",
    "powerset",
    "asciify_dict",
    "merge_dicts",
    "deep_update",
]


def merge_dicts(x, y):
    """
    Merge dictionaries

    :param Mapping x: dict to merge
    :param Mapping y: dict to merge
    :return Mapping: merged dict
    """
    z = x.copy()
    z.update(y)
    return z


def deep_update(old, new):
    """
    Recursively update nested dict, modifying source
    """
    for key, value in new.items():
        if isinstance(value, Mapping) and value:
            old[key] = deep_update(old.get(key, {}), value)
        else:
            old[key] = new[key]
    return old


def is_collection_like(c):
    """

    Determine whether an object is collection-like.

    :param object c: Object to test as collection
    :return bool: Whether the argument is a (non-string) collection
    """
    return isinstance(c, Iterable) and not isinstance(c, str)


def uniqify(seq):  # Dave Kirby
    """
    Return only unique items in a sequence, preserving order

    :param list seq: List of items to uniqify
    :return list[object]: Original list with duplicates removed
    """
    # Order preserving
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]


def powerset(items, min_items=None, include_full_pop=True, nonempty=False):
    """
    Build the powerset of a collection of items.

    :param Iterable[object] items: "Pool" of all items, the population for
        which to build the power set.
    :param int min_items: Minimum number of individuals from the population
        to allow in any given subset.
    :param bool include_full_pop: Whether to include the full population in
        the powerset (default True to accord with genuine definition)
    :param bool nonempty: force each subset returned to be nonempty
    :return list[object]: Sequence of subsets of the population, in
        nondecreasing size order
    :raise TypeError: if minimum item count is specified but is not an integer
    :raise ValueError: if minimum item count is insufficient to guarantee
        nonempty subsets
    """
    if min_items is None:
        min_items = 1 if nonempty else 0
    else:
        if not isinstance(min_items, int):
            raise TypeError(
                "Min items count for each subset isn't an integer: "
                "{} ({})".format(min_items, type(min_items))
            )
        if nonempty and min_items < 1:
            raise ValueError(
                "When minimum item count is {}, nonempty subsets "
                "cannot be guaranteed.".format(min_items)
            )
    # Account for iterable burn possibility; besides, collection should be
    # relatively small if building the powerset.
    items = list(items)
    n = len(items)
    if n == 0 or n < min_items:
        return []
    max_items = len(items) + 1 if include_full_pop else len(items)
    return list(
        itertools.chain.from_iterable(
            itertools.combinations(items, k) for k in range(min_items, max_items)
        )
    )


def asciify_dict(data):
    """https://gist.github.com/chris-hailstorm/4989643"""

    def _asciify_list(lst):
        ret = []
        for item in lst:
            if isinstance(item, unicode):
                item = item.encode("utf-8")
            elif isinstance(item, list):
                item = _asciify_list(item)
            elif isinstance(item, dict):
                item = asciify_dict(item)
            ret.append(item)
        return ret

    if sys.version_info[0] >= 3:
        warn("This operation is supported only in Python2", UserWarning)
        return data

    ret = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode("utf-8")
        if isinstance(value, unicode):
            value = value.encode("utf-8")
        elif isinstance(value, list):
            value = _asciify_list(value)
        elif isinstance(value, dict):
            value = asciify_dict(value)
        ret[key] = value
    return ret
