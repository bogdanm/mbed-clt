from commands.command import Command
from utils.helpers import is_mbed_dir, error, info, repo_name
from utils import get_project_dir
from utils.project import MbedProject
from utils.config import cfg

class CmdList(Command):
    def __init__(self):
        Command.__init__(self, "list")

    def get_help(self):
        return "list - list all the repositories that are part of this mbed project"

    def __call__(self, args):
        if args:
            return None
        if not is_mbed_dir():
            error("Run this command from a mbed project directory.")
            return False
        rname, rdata = MbedProject.read_repo_info()
        indent, indent2 = max([len(repo_name(k["url"])) for k in rdata]), max([len(k["url"]) for k in rdata])
        info("Base directory: %s" % get_project_dir())
        info("List of repositories for project %s:\n" % rname)
        fmt = "%%%ds: %%-%ds (cloned in %%s)" % (indent, indent2)
        for r in rdata:
            dirname = "the base directory" if r["dir"] == "." else r["dir"]
            info(fmt % (repo_name(r["url"]), r["url"], dirname))
        return True
