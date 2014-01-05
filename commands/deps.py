from commands.command import Command
from utils.helpers import info, error, is_mbed_dir, repo_name
from utils.project import MbedProject
import os

class CmdDeps(Command):

    def __init__(self):
        Command.__init__(self, "deps")

    def get_help(self):
        return "deps - lists repositories with all their dependencies"

    def print_deps(self, deps, key, indent = 0, sim = False):
        prefix = " " * indent
        if sim:
            self.pos = max(self.pos, len(prefix + key) + 1)
        else:
            fmt = "%%-%ds[%%s]" % self.pos
            info(fmt % (prefix + key, self.info[key]))
        if not deps.has_key(key):
            return
        for dep in deps[key]:
            self.print_deps(deps, dep, indent + 4, sim)

    def __call__(self, args):
        if len(args) != 0:
            return None
        if not is_mbed_dir():
            error("Run this command from a mbed project directory.")
            return False
        base, deps = MbedProject.get_repo_deps()
        _, rinfo = MbedProject.read_repo_info()
        self.info = {}
        for r in rinfo:
            self.info[repo_name(r["url"])] = r["url"]
        if not deps:
            error("Unable to get dependency information.")
            os._exit(1)
        try:
            if len(deps) == 0:
                info("The project doesn't have any dependencies")
            else:
                self.pos = 0
                self.print_deps(deps, base, 0, True)
                self.print_deps(deps, base)
        except:
            raise
            error("Unable to process dependency chain, probably internal error.")
            os._exit(1)
        return True
