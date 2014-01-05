# mbed project related operations

import os
from utils.helpers import hg_walk, parse_mbed_file, basedir, rel_path, hg_clone, repo_name
from utils.config import cfg
from utils import get_project_dir

class MbedProject(object):
    def __init__(self, where = None):
        self.where = where or get_project_dir()

    def clone(self, cloned = {}):
        rlist = []
        # Traverse the repository until there's nothing left to clone
        def _walker_cb(root, files):
            self._repo = None
            for f in files:
                if not f.endswith(('.bld', '.lib')):
                    continue
                full = os.path.join(root, f)
                if cloned.get(full, False):
                    continue
                self._repo = full
                return False
            return True
        crtdir = os.getcwd()
        while True:
            hg_walk(self.where, _walker_cb)
            if self._repo is None:
                break
            main_url, revision = parse_mbed_file(self._repo)
            os.chdir(basedir(self._repo))
            d = hg_clone(main_url, None, revision)
            cloned[self._repo] = True
            rlist.append({"url": main_url, "dir": rel_path(d), "file": rel_path(self._repo)})
        os.chdir(crtdir)
        return rlist

    @staticmethod
    def write_repo_info(repo_name, rlist, conf = None):
        conf = conf or cfg
        conf.set("repo.n_repos", len(rlist))
        conf.set("repo.name", repo_name)
        for idx, k in enumerate(rlist):
            conf.set("repo.url_%d" % idx, k["url"])
            conf.set("repo.dir_%d" % idx, k["dir"])
            conf.set("repo.file_%d" % idx, k["file"])

    @staticmethod
    def read_repo_info(conf = None):
        conf, rlist = conf or cfg, []
        total = int(cfg.get("repo.n_repos"))
        for i in xrange(0, total):
            rurl = conf.get("repo.url_%d" % i)
            rdir = conf.get("repo.dir_%d" % i)
            rfile = conf.get("repo.file_%d" % i)
            rlist.append({"url": rurl, "dir": rdir, "file": rfile})
        return conf.get("repo.name"), rlist

    @staticmethod
    def get_repo_deps():
        rname, rlist = MbedProject.read_repo_info()
        rlist.sort(key=lambda e : 0 if e["dir"] == "." else e["dir"].count('/') + 1)
        main_repo = repo_name(rlist[0]["url"])
        deps = dict([(main_repo, [])])
        for r in rlist[1:]:
            d = r["dir"]
            if d.find('/') == -1:
                deps[main_repo].append(d)
            else:
                data = d.split('/')
                repo, dep = data[-2], data[-1]
                if deps.has_key(repo):
                    deps[repo].append(dep)
                else:
                    deps[repo] = [dep]
        return main_repo, deps
