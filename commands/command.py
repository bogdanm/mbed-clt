# Base class for commands

from abc import ABCMeta, abstractmethod
from utils.helpers import find_mbed_dir

class Command(object):
    __metaclass__ = ABCMeta

    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name

    @abstractmethod
    def get_help(self):
        pass

    @abstractmethod
    def __call__(self, args):
        pass

