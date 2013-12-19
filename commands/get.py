from commands.command import Command
from utils.config import cfg
from utils.helpers import info

class CmdGet(Command):
    def __init__(self):
        Command.__init__(self, "get")

    def get_help(self):
        return "get [<key>] ... [<key>] - gets the value of the given keys (or lists full configuration if key not given)"

    def __call__(self, args):
        if args:
            for a in args:
                v = cfg.get(a)
                if not v:
                    info("'%s' is not set" % a)
                else:
                    info("%s = %s" % (a, v))
        else:
            for k in cfg:
                info("%s = %s" % (k, cfg.get(k)))
        return True
