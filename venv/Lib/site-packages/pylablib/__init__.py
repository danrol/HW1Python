import os
import os.path
from .core.utils import module as module_utils  #@UnresolvedImport

_load_path=os.path.abspath(os.curdir)

def reload_all(from_load_path=True):
    """
    Reload all loaded modules.
    """
    if from_load_path:
        cur_dir=os.path.abspath(os.curdir)
        os.chdir(_load_path)
        try:
            module_utils.reload_package_modules(__name__)
        finally:
            os.chdir(cur_dir)
    else:
        module_utils.reload_package_modules(__name__)