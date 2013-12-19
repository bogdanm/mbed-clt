_mbed_project_dir = None

def set_project_dir(d):
    global _mbed_project_dir
    _mbed_project_dir = d

def get_project_dir():
    return _mbed_project_dir
