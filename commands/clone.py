from commands.command import Command
from utils.config import cfg
from utils.helpers import is_hg_dir, parse_hg_url, hg_clone, error, info, repo_name, gen_private_settings
from utils.helpers import repo_name_to_url
from utils.project import MbedProject
from constants import cfg_fname
from os.path import exists, abspath, join
import os
from utils import set_project_dir

################################################################################
# .hgignore helper

class HgIgnore(object):
    def __init__(self, d = None):
        self.fname = join(d or os.getcwd(), ".hgignore")
        self.patterns = ['.hgignore']
        self._read()

    def _read(self):
        try:
            f = open(self.fname, "rt")
            for line in f:
                line = line.replace('\n', '').replace('\r', '')
                if line.beginswith(('#', 'syntax:')):
                    continue
                self.patterns.append(line)
            f.close()
            return True
        except:
            return False

    def add(self, mask):
        if type(mask) != type([]):
            mask = [mask]
        self.patterns = self.patterns + mask

    def write(self):
        try:
            f = open(self.fname, "wt")
            f.write("# Automatically generated file\n\n")
            f.write("syntax: glob\n")
            f.write("\n".join(self.patterns))
            f.close()
        except:
            return False

    def sync(self):
        self.write()

################################################################################
# Actual command

class CmdClone(Command):
    repo_url_pattern = "http://mbed.org/users/%s/code/%s/"

    def __init__(self):
        Command.__init__(self, "clone")

    def get_help(self):
        return "clone <repo> [dirname] - clones the given repository"

    def __call__(self, args):
        if len(args) == 0 or len(args) > 2:
            return None
        if is_hg_dir():
            error("This directory already contains a mercurial repository.")
            error("Please clone in a directory that doesn't contain a mercurial repository.")
            return False
        mbedrepo = repo_name_to_url(args[0])
        if mbedrepo == False:
            return False
        info("Using '%s' as the URL to clone" % mbedrepo)
        if len(args) == 2:
            dirname = args[1]
        else:
            dirname, _ = parse_hg_url(mbedrepo)
        if exists(dirname):
            error("'%s' already exists, choose another directory." % dirname)
            return False
        dirname = abspath(dirname)
        set_project_dir(dirname)
        # Clone main repository
        d = hg_clone(mbedrepo, dirname)
        # Traverse the repository until there's nothing left to clone
        rlist = [{"url": mbedrepo, "dir": '.', "file": 'None'}] + MbedProject(dirname).clone()
        info("Setting up repo...")
        # Setup internal config file
        os.chdir(join(os.getcwd(), dirname))
        open(join(os.getcwd(), cfg_fname), "w").close()
        cfg.reload()
        # Generate private_settings.py starting from the configuration
        gen_private_settings()
        # Now create list of files/dirs that will be ignored in the repo
        hgi = HgIgnore()
        hgi.add([cfg_fname, "mbed_settings.py*", ".build", ".export"])
        hgi.sync()
        # Setup repository data in the sync file
        MbedProject.write_repo_info(repo_name(mbedrepo), rlist)
        info("Cloned %s into %s" % (mbedrepo, os.getcwd()))
        return True
