from commands.command import Command
from utils.helpers import repo_name_to_url, is_mbed_dir, parse_hg_url, info, error, repo_name
from utils.helpers import full_path, rel_path, is_url_live, get_hg_tip_revision
from utils.project import MbedProject
from os.path import exists, abspath, join
import os

class CmdAdd(Command):

    def __init__(self):
        Command.__init__(self, "add")

    def get_help(self):
        return "add <repo> [dirname] - adds the given repository (and clones it)"

    def __call__(self, args):
        if len(args) == 0 or len(args) > 2:
            return None
        if not is_mbed_dir():
            error("Run this command from a mbed project directory.")
            return False
        mbedrepo = repo_name_to_url(args[0])
        info("Using '%s' as the project URL" % mbedrepo)
        if not is_url_live(mbedrepo):
            error("Unable to access URL '%s'." % mbedrepo)
            return False
        if len(args) == 2:
            dirname = args[1]
        else:
            dirname, _ = parse_hg_url(mbedrepo)
        if exists(dirname):
            error("'%s' already exists, choose another directory." % dirname)
            return False
        dirname = abspath(dirname)
        # Create library file in the given directory
        libfname = join(os.getcwd(), repo_name(mbedrepo) + ".lib")
        if exists(libfname):
            error("'%s' already exists, choose another project or directory" % libfname)
            return False
        with open(libfname, "w") as f:
            f.write(mbedrepo)
        # Clone project again, but only the parts that aren't cloned yet
        # (in other words, just the lib file created above)
        prj = MbedProject()
        rname, rlist = prj.read_repo_info()
        rlist = rlist + prj.clone(dict([(full_path(e["file"]), True) for e in rlist]))
        # Re-write lib file with the revision hash
        rev = get_hg_tip_revision(dirname)
        with open(libfname, "w") as f:
            f.write('%s#%s' % (mbedrepo, rev))
        # Re-write project data
        prj.write_repo_info(rname, rlist)
        return True
