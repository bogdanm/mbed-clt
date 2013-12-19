from utils.helpers import is_mbed_dir, error
from commands.command import Command
from optparse import OptionParser
from utils.config import cfg
from os.path import join
import os

class CmdCompile(Command):
    def __init__(self):
        Command.__init__(self, "compile")

    def get_help(self):
        return """compile [-m MCU] [-t ARM] [-c] [-v] [-b build_dir] - compile the project for the given MCU and toolchain
        -c: clean before building
        -v: be verbose (show commands while building)
        -b: use the given build directory ('.build' by default)"""

    def __call__(self, args):
        if not is_mbed_dir():
            error("Run this command from a mbed project directory.")
            return False
        try:
            from workspace_tools.build_api import build_project
            from workspace_tools.targets import TARGET_MAP, TARGET_NAMES
            from workspace_tools.toolchains import TOOLCHAINS
        except:
            error("Unable to initialize build system.")
            error("Check that 'mbed-tools' is installed.")
            return False
        p = OptionParser()
        p.add_option("-m", "--mcu", dest="mcu")
        p.add_option("-t", "--toolchain", dest="toolchain")
        p.add_option("-c", "--clean", action="store_true", dest="clean", default=False)
        p.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False)
        p.add_option("-b", "--build", dest="build_dir")
        (options, args) = p.parse_args(args)
        if args:
            return None
        mcu = options.mcu or cfg.get("mcu")
        toolchain = options.toolchain or cfg.get("toolchain")
        if not mcu:
            error("MCU not specified, aborting.")
            return False
        if not toolchain:
            error("Toolchain not specified, aborting.")
            return False
        if not mcu in TARGET_NAMES:
            error("Invalid MCU '%s', valid choices: %s" % (mcu, ','.join(TARGET_NAMES)))
            return False
        if not toolchain in TOOLCHAINS:
            error("Invalid toolchain '%s', valid choices: %s" % (toolchain, ','.join(TOOLCHAINS)))
            return False
        target = TARGET_MAP[mcu]
        if not toolchain in target.supported_toolchains:
            error("Toolchain '%s' is not supported for target '%s'." % (toolchain, mcu))
            error("Supported toolchains: %s" % ' '.join(target.supported_toolchains))
            return False
        build_dir = options.build_dir or cfg.get("build_dir") or join(os.getcwd(), ".build")
        if options.build_dir and not cfg.get("build_dir"):
            cfg.set("build_dir", abspath(options.build_dir))
        build_dir = join(build_dir, "%s_%s" % (mcu, toolchain))
        try:
            build_project(os.getcwd(), build_dir, target, toolchain, [], [], linker_script=None, clean=options.clean, verbose=options.verbose)
        except KeyboardInterrupt, e:
            info("\n[CTRL+c] exit")
        except Exception as e:
            error("Unable to build project, please fix the errors.")
            error(str(e))
            return False
        return True

