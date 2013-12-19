from commands.command import Command
from utils.config import cfg
from utils.helpers import gen_private_settings, error, is_mbed_dir

class CmdSet(Command):
    _trigger_keys = ["armcc", "gcc_arm", "gcc_cr", "gcc_cs", "iar"]

    def __init__(self):
        Command.__init__(self, "set")

    def get_help(self):
        return "set [--global] <key=value> [<key=value>] ... - sets one or more configuration keys"

    def __call__(self, args):
        if len(args) == 0:
            return None
        glbl = False
        if args[0].lower() == '--global':
            glbl = True
            args = args[1:]
        if len(args) == 0:
            return None
        if not glbl and not cfg.has_local():
            error("The current directory doesn't contain a mbed project.")
            error("Re-run the command from a mbed project directory or use '--global'.")
            return False
        sets, reconf = {}, False
        for a in args:
            if a.endswith('='):
                sets[a[:-1].lower()] = None
            else:
                l = a.split('=', 1)
                if len(l) != 2:
                    error("Invalid argument '%s'" % a)
                    return False
                sets[l[0].lower()] = l[1]
        for k in sets:
            cfg.set(k, sets[k], glbl)
            if k in self._trigger_keys:
                reconf = True
        if not cfg.sync():
            error("Error writing configuration to disk.")
            return False
        if reconf and is_mbed_dir():
            gen_private_settings()
        return True
