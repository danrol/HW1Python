"""
Script for compiling iir_transform.pyc

Compile the library by executing 'python iir_transform_setup.py build' from the command line. The compiled .pyc file is located at ./build/lib.*/
Requires the appropritate C++ compiler (e.g., VC for python 2.7, or MS Build Tools for VS 2017)
"""

if __name__=="__main__":
    from distutils.core import setup, Extension
    from distutils.sysconfig import get_python_lib
    import os.path
    import sys

    import platform
    arch=platform.architecture()[0]
    ver="{}{}".format(sys.version_info.major,sys.version_info.minor)
    if arch=="32bit":
        module_name='iir_transform_py{}_32'.format(ver)
    elif arch=="64bit":
        module_name='iir_transform_py{}_64'.format(ver)
    else:
        raise ImportError("Unexpected system architecture: {0}".format(arch))

    numpy_dir=os.path.join(get_python_lib(),'numpy')
    numpy_include_dir=os.path.join(numpy_dir,'core','include','numpy')
    numpy_lib_dir=os.path.join(numpy_dir,'core','lib')

    module = Extension(module_name,
                        sources = ['iir_transform_py{}.c'.format(ver)],
                        include_dirs=[numpy_include_dir],
                        library_dirs=[numpy_lib_dir])

    setup(name = 'IIR transform',
        description = 'Digital filters package.',
        ext_modules = [module])