import json
import os
from functools import lru_cache
from os.path import join, exists

from .common import lazyproperty
from .config import config

class InvalidCachePackage(Exception):
    pass
    
class PackageInfo(object):
    """
    Represent a package and its files in the pkg cache.
    """
    def __init__(self, path):
        """
        Provide an interface to a cached package.

        A valid path should have 
        """
        self.path = path
        self._info = join(path, 'info')
        if exists(path) and exists(self._info):
            self._index = join(self._info, 'index.json')
            self._files = join(self._info, 'files')
        else:
            raise InvalidCachePackage("{} does not exist".format(self._info))
    
    @lru_cache(maxsize=16)
    def __getattr__(self, name):
        """
        Provide attribute access in to self.index

        If an attribute is not resolvable, return None.
        """
        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self.index:
            return self.index[name]

    @lazyproperty
    def index(self):
        with open(self._index, 'r') as f:
            x = json.load(f)
        return x

    @lazyproperty
    def files(self):
        with open(self._files, 'r') as f:
            x = map(str.strip, f.readlines())
        return frozenset(x)

    @lazyproperty
    def full_spec(self):
        return '{}-{}-{}'.format(self.name, self.version, self.build)

    def __eq__(self, other):
        if not isinstance(other, PackageInfo):
            return False

        if self.path == other.path:
            return True
        return False

    def __hash__(self):
        return hash(self.path)

    def __repr__(self):
        return 'PackageInfo({}) @ {}'.format(self.path, hex(id(self)))

    def __str__(self):
        return '{}::{}'.format(self.name, self.version)


def packages(path, verbose=False):
    if not exists(path):
        raise IOError('{} cache does not exist!'.format(path))

    result = []
    cache = os.walk(path, topdown=True)
    root, dirs, files = next(cache)
    for d in dirs:
        try:
            result.append(PackageInfo(join(root, d)))
        except InvalidCachePackage:
            if verbose:
                print("Skipping {}".format(d))
            continue
    return tuple(result)

def named_cache(path):
    """
    Return dictionary of cache with (package name, package version) mapped to cache entry.
    :param path: path to pkg cache
    :return: dict
    """
    return {(i.name, i.version): i for i in packages(path)}
