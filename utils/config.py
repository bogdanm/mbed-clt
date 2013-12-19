# Configuration handler

from ConfigParser import SafeConfigParser
from os.path import expanduser, join
from utils.helpers import is_mbed_dir
from constants import default_config, cfg_fname
import os

# The configuration class uses two configuration files:
#   - global (in the user home directory)
#   - local (project configuration)
# get: if the same parameter is given both in the local configuration and in
# the global configuration, the one in the local configuration is used
# set: by default will set a local paramater, unless called with is_global=True

class _Configuration(object):
    default_section = "mbed"
    
    class _iter(object):
        def __init__(self, cfg):
            values = set()
            if cfg.g_parser.has_section(_Configuration.default_section):
                values = values | set(cfg.g_parser.options(_Configuration.default_section))
            if cfg.l_parser.has_section(_Configuration.default_section):
                values = values | set(cfg.l_parser.options(_Configuration.default_section))
            self.values, self.idx = list(values), 0

        def next(self):
            if self.idx < len(self.values):
                self.idx = self.idx + 1
                return self.values[self.idx - 1]
            raise StopIteration

    def __init__(self, lazy=False):
        self.lazy = lazy
        self.fnames = {}
        self.reload()

    def reload(self):
        if self.fnames:
            self.sync()
        self.g_parser = SafeConfigParser()
        self.fnames[self.g_parser] = join(expanduser("~"), cfg_fname)
        self.g_parser.read(self.fnames[self.g_parser])
        self.l_parser = SafeConfigParser()
        if is_mbed_dir():
            self.fnames[self.l_parser] = join(os.getcwd(), cfg_fname)
            self.l_parser.read(self.fnames[self.l_parser])
        else:
            self.fnames[self.l_parser] = False

    def has_local(self):
        return self.fnames[self.l_parser] != False

    def _write_config(self, parser):
        if not self.fnames[parser]:
            return True
        try:
            f = open(self.fnames[parser], 'w')
            parser.write(f)
            f.close()
        except:
            return False
        return True

    def _parse_key(self, key):
        idx = key.find(".")
        return (self.default_section, key) if idx == -1 else (key[:idx], key[idx + 1:])

    def _get_helper(self, parser, key):
        section, key = self._parse_key(key)
        if not parser.has_option(section, key):
            return None
        return parser.get(section, key)

    def _set_helper(self, parser, key, value):
        section, key = self._parse_key(key)
        if value is None: # this means 'remove key'
            if not parser.has_option(section, key):
                return False
            parser.remove_option(section, key)
            return True if self.lazy else self._write_config(parser)
        if not parser.has_section(section):
            parser.add_section(section)
        parser.set(section, key, str(value))
        return True if self.lazy else self._write_config(parser)

    def get(self, key):
        return self._get_helper(self.l_parser, key) or self._get_helper(self.g_parser, key)

    def get_bool(self,key):
        v = self.get(key)
        if not v:
            return False
        return v.lower() in ["1", "yes", "true", "on"]

    def set(self, key, value, is_global=False):
        return self._set_helper(self.g_parser, key, value) if is_global else self._set_helper(self.l_parser, key, value)

    def sync(self):
        if not self.lazy:
            return True
        wrote_l = self._write_config(self.l_parser)
        wrote_g = self._write_config(self.g_parser)
        return wrote_l and wrote_g

    def remove_section(self, name):
        g_res = self.g_parser.remove_section(name)
        l_res = self.l_parser.remove_section(name)
        if g_res or l_res:
            wrote = self.sync()
        return (g_res or l_res) and wrote

    def has_option(self, key):
        section, key = self._parse_key(key)
        return self.g_parser.has_option(section, key) or self.l_parser.has_option(section, key)
    
    def __iter__(self):
        return _Configuration._iter(self)

cfg = _Configuration()        
# Set default configuration parameters if needed
for conf in default_config:
    if not cfg.has_option(conf):
        cfg.set(conf, default_config[conf], is_global = True)
