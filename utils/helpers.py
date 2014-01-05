import sys, os
from os.path import isdir, join, exists, abspath, splitext, split, relpath, normpath, isfile
from subprocess import call, check_output, CalledProcessError
from constants import cfg_fname, mbed_builds_base
from utils import get_project_dir
import urllib

try:
    from colorama import init as cl_init
    from termcolor import colored
    cl_init()
    def print_color(text, col, stream = sys.stdout):
        from utils.config import cfg
        text = text + '\n'
        stream.write(colored(text, col, attrs=['bold']) if cfg.get_bool("use_colors") else text)
except:
    def print_color(text, color, stream = sys.stdout):
        stream.write(text + '\n')

def info(text):
    from utils.config import cfg
    print_color(text, cfg.get("info_color"))

def warn(text):
    from utils.config import cfg
    print_color(text, cfg.get("warn_color"))

def error(text):
    from utils.config import cfg
    print_color(text, cfg.get("error_color"), stream = sys.stderr)

def cmd_output(text, stream = sys.stdout):
    from utils.config import cfg
    print_color(text, cfg.get("cmd_output_color"), stream = stream)

def exec_helper(cmd, check = True):
    if type(cmd) == type([]):
        cmd = ' '.join(cmd)
    res = call(cmd, shell = False, cwd = os.getcwd())
    if check and res != 0:
        return False
    return True

def silent_exec(cmdline):
    try:
        output = check_output(cmdline)
    except CalledProcessError as e:
        if len(e.output.split()) > 0:
            error("Error executing '%s', error message below.\n" % cmdline[0])
            error("\n".join([">> " + l for l in e.output.split("\n")]))
        else:
            error("Error executing '%s'.\n" % cmdline[0])
        os._exit(1)
    return output      

def parse_hg_url(url):
    if not url.endswith('/'):
        url = url + '/'
    parts = url.split('/')[:-1]
    return parts[-1], '/'.join(parts[0:-1])

def hg_clone(url, dirname = None, revision = None, basedir = None):
    name, _ = parse_hg_url(url)
    dirname, renamed = dirname or name, False
    initial = dirname
    if exists(dirname):
        warn("WARNING: directory '%s' already exists!" % join(os.getcwd(), dirname))
        idx, renamed = 1, True
        while True:
            dirname = "%s_%d" % (initial, idx)
            if not exists(dirname):
                break
            idx = idx + 1
    info("[%s] -> %s... (%s) %s" % (url, abspath(dirname), revision or "default", ("(renamed from '%s' to '%s')" % (initial, dirname)) if renamed else ""))
    if not exec_helper(['hg', 'clone', url, dirname, '-u', revision or "default"]):
        error("Error running 'hg clone', aborting.")
        os._exit(1)
    return abspath(dirname)

def is_hg_dir(d = None):
    base = d or os.getcwd()
    if not isdir(join(base, '.hg')):
        return False
    if not isfile(join(base, '.hg', 'hgrc')):
        return False
    return True

def is_mbed_dir(d = None):
    base = d or os.getcwd()
    if not is_hg_dir(base):
        return False
    if not isfile(join(base, cfg_fname)):
        return False
    return True

def find_mbed_dir(d = None):
    now = os.getcwd()
    d = d or now
    while True:
        if is_mbed_dir(d):
            os.chdir(d)
            return d
        crtdir = os.getcwd()
        os.chdir("..")
        d = os.getcwd()
        if crtdir == d:
            break
    os.chdir(now)
    return False

def gen_private_settings(base = None):
    from utils.config import cfg
    def format_path(path):
        return abspath(path).replace('\\', '/')
    base = base or os.getcwd()
    with open(join(base, "mbed_settings.py"), "wt") as f:
        f.write("# Automatically generated file\n")
        f.write("from os.path import join\n\n")
        f.write('BUILD_DIR = "%s"\n' % format_path((cfg.get("build_dir") or join(base, ".build"))))
        armcc = cfg.get("armcc")
        if armcc:
            f.write('ARM_PATH = "%s"\n' % format_path(armcc))
            f.write('ARM_BIN = join(ARM_PATH, "bin")\n')
            f.write('ARM_INC = join(ARM_PATH, "include")\n')
            f.write('ARM_LIB = join(ARM_PATH, "lib")\n')
            f.write('ARM_CPPLIB = join(ARM_LIB, "cpplib")\n')
            f.write('uARM_CLIB = join(ARM_PATH, "lib", "microlib")\n')
        for gcc in ["gcc_arm", "gcc_cr", "gcc_cs"]:
            d = cfg.get(gcc)
            if d:
                f.write('%s_PATH = "%s"\n' % (gcc.upper(), format_path(join(d, 'bin'))))
        iar = cfg.get("iar")
        if iar:
            f.write('IAR_PATH = "%s"\n' % format_path(iar))

def repo_name(url):
    name, _ = parse_hg_url(url)
    return name

def hg_walk(path, cb, ign_dirs = []):
    for root, dirs, files in os.walk(path):
        for d in dirs[:]:
            if d == '.hg' or d in ign_dirs:
                dirs.remove(d)
        if not cb(root, files):
            break

def parse_mbed_file(fname):
    url = open(fname, 'r').readline().strip().replace('\r', '').replace('\n', '')
    _, ext = splitext(fname)
    if ext == '.lib':
        info = url.split('#')
        if len(info) == 1:
            info.append('tip')
        main_url, revision = info[0], info[1]
    elif ext == '.bld': # .bld file
        if url.endswith('/'):
            url = url[:-1]
        if url.find(mbed_builds_base) != 0:
            error("Internal error while parsing .bld file, will abort script.")
            os._exit(2)
        revision = url[len(mbed_builds_base):] if url != mbed_builds_base else 'tip'
        main_url = mbed_builds_base.replace("builds/", "")
    else:
        error("Unknown file type '%s' (probably internal error)." % fname)
        os._exit(1)
    return main_url, revision

def basedir(path):
    base, _ = split(path)
    return base

def rel_path(p):
    return relpath(normpath(p), get_project_dir()).replace('\\', '/')

def full_path(p):
    return normpath(join(get_project_dir(), p))

def repo_name_to_url(mbedrepo):
    from utils.config import cfg
    repo_url_pattern = "http://mbed.org/users/%s/code/%s/"
    if not mbedrepo.startswith("http"): # actual URL
        if not cfg.get("username"):
            error("Username not specified, cannot build URL.")
            error("Use 'mbed set --global username=<name>' to set username.")
            return False
        mbedrepo = repo_url_pattern % (cfg.get("username"), mbedrepo)
    if not mbedrepo.endswith('/'):
        mbedrepo = mbedrepo + '/'
    return mbedrepo

def is_url_live(url):
    return urllib.urlopen(url).getcode() == 200

def get_hg_tip_revision(d = None):
    crtdir = os.getcwd()
    d = d or crtdir
    os.chdir(d)
    res = silent_exec(['hg', 'log', '-r', 'tip']).replace('\r', '').replace(' ', '').replace('\t', '')
    res = res.split('\n')[0]
    if res.find("changeset:") != 0:
        error("Internal error in get_hg_tip_revision")
        os._exit(1)
    res = res[len("changeset:"):].split(':')[1]
    os.chdir(crtdir)
    return res

