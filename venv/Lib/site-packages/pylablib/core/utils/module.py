"""
Library for dealing with python module properties.
"""

from imp import reload

import pkg_resources
import sys
import os.path
from . import general, files as file_utils

def get_package_version(pkg):
    """
    Get the version of the package.
    
    If the package version is unavalable, return ``None``.
    """
    try:
        return pkg_resources.get_distribution(pkg).version
    except pkg_resources.DistributionNotFound:
        return None

def _tryint(v):
    try:
        return int(v)
    except ValueError:
        return v
def cmp_package_version(pkg, ver):
    """
    Compare current package version to `ver`.
    
    Return ``'<'`` if current version is older (smaller), ``'>'`` if it's younger (larger) or ``'='`` if it's the same.
    If the package version is unavalable, return ``None``.
    """
    cver=get_package_version(pkg)
    if cver is None:
        return None
    ver=[_tryint(v.strip()) for v in ver.split(".")]
    cver=[_tryint(v.strip()) for v in cver.split(".")]
    if cver>ver:
        return ">"
    if cver<ver:
        return "<"
    return "="
            


def expand_relative_path(module_name, rel_path):
    """
    Turn a relative module path into an absolue one.
    
    `module_name` is the absolute name of the reference module, `rel_path` is the path relative to this module.
    """
    module_path=module_name.split(".")
    if not rel_path.startswith("."):
        return rel_path
    else:
        while rel_path.startswith("."):
            rel_path=rel_path[1:]
            module_path=module_path[:-1]
        return ".".join(module_path)+"."+rel_path


def get_loaded_package_modules(pkg_name):
    """
    Get all modules in the package `pkg_name`.
    
    Returns a dict ``{name: module}``.
    """
    prefix=pkg_name+"."
    return dict([(name,module) for name,module in sys.modules.items() if (name.startswith(prefix) or name==pkg_name) and module is not None])

def get_reload_order(modules):
    """
    Find reload order for modules which respects dependencies (a module is loaded before its dependants).
    
    `modules` is a dict ``{name: module}``.
    
    The module dependencies (i.e., the modules which the current module depends on) are described in the variable ``_depends_local`` defined at its toplevel
    (missing variable means no dependencies).
    """
    deps={}
    for name,module in modules.items():
        try:
            deps[name]=[expand_relative_path(name,dep) for dep in module._depends_local]
        except AttributeError:
            pass
        for ch_name in modules:
            if ch_name!=name and ch_name.startswith(name+"."):
                deps.setdefault(name,[]).append(ch_name)
    for name in deps:
        deps[name]=list(set(deps[name]))
    order=general.topological_order(deps)
    order=[name for name in modules if not name in order]+order
    return order
def reload_package_modules(pkg_name, ignore_errors=False):
    """
    Reload package `pkg_name`, while respecting dependencies of its submodules.
    
    If ``ignore_errors=True``, ignore :exc:`ImportError` exceptions during the reloading process.
    """
    modules=get_loaded_package_modules(pkg_name)
    order=get_reload_order(modules)
    for name in order:
        try:
            reload(modules[name])
        except ImportError:
            if not ignore_errors:
                raise
            
            
def get_library_path():
    """
    Get a filesystem path for the pyLabLib library (the one containing current the module).
    """
    module_path=sys.modules[__name__].__file__
    module_path=file_utils.normalize_path(module_path)
    return os.path.join(*file_utils.fullsplit(module_path)[:-3])
    