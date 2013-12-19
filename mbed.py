from utils.helpers import error, find_mbed_dir, is_mbed_dir
import sys, os
from utils import set_project_dir

from commands.set import CmdSet
from commands.get import CmdGet
from commands.clone import CmdClone
from commands.compile import CmdCompile
from commands.list import CmdList

################################################################################
# Local functions

def help_and_exit(cmds):
    error("Syntax: mbed <command> [arguments]")
    error("Valid commands:")
    for c in cmds:
        error("    " + c.get_help() + "")
    os._exit(1)

def run(args):
    cmds = [CmdSet(), CmdGet()]
    if is_mbed_dir():
        cmds = cmds + [CmdCompile(), CmdList()]
    else:
        cmds = cmds = [CmdClone()]
    if len(args) == 0:
        error("No command given.")
        help_and_exit(cmds)
    cmd_map = dict([(c.get_name(), c) for c in cmds])
    cmd = args[0].lower()
    if not cmd in cmd_map:
        error("Invalid command '%s'." % args[0])
        help_and_exit(cmds)
    res = cmd_map[cmd](args[1:])
    if res == None:
        error("Invalid command syntax")
        error(cmd_map[cmd].get_help())
    elif res == False:
        os._exit(1)

################################################################################
# Entry point

if __name__ == "__main__":
    base = find_mbed_dir()
    if base:
        set_project_dir(base)
        sys.path.append(base)
    run(sys.argv[1:])
