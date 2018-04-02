"""
Interface module for iir_transform_py*_*.pyd

Import the correct version of the package (based on the python version and bitness) and makes a wrapping function to deal with complex values.

If the correct library version is absent, one can either compile an approprite version (see iir_transform_setup.py and iir_transform_py*_*.c)
or set ``use_fallback=True`` to use the fallback python implementation of this function (works much slower, but is platform-independent).
"""

from builtins import range

from ..datatable import wrapping #@UnresolvedImport

import platform
import numpy as np
import sys

use_fallback=False

arch=platform.architecture()[0]
ver="{}{}".format(sys.version_info.major,sys.version_info.minor)

try:
    if arch not in {"32bit","64bit"}:
        raise ImportError("Unexpected system architecture: {0}".format(arch))
    if ver not in {"27","36"}:
        raise ImportError("Unexpected python version: {0}".format(ver))
    if ver=="27":
        if arch=="32bit":
            from .iir_transform_py27_32 import iir_apply
        else:
            from .iir_transform_py27_64 import iir_apply
    elif ver=="36":
        if arch=="32bit":
            from .iir_transform_py36_32 import iir_apply
        else:
            from .iir_transform_py36_64 import iir_apply
except (ImportError):
    if use_fallback: # re-create the function in Python; much slower than the precompiled one
        def iir_apply(trace, xcoeff, ycoeff):
            """
            Apply digital, (possibly) recursive filter with coefficients `xcoeff` and `ycoeff`.

            Result is filtered signal `y` with ``y[n]=sum_j x[n-j]*xcoeff[j] + sum_k y[n-k-1]*ycoeff[k]`` .
            All input arrays should be one-dimensional and real.
            """
            if (np.ndim(trace)!=1) or (np.ndim(xcoeff)!=1) or (np.ndim(ycoeff)!=1):
                raise ValueError("only 1D arrays are allowed")
            new_trace=np.zeros(len(trace))
            if len(xcoeff)==0:
                return new_trace
            tstart=max(len(xcoeff)-1,len(ycoeff))
            new_trace[:tstart]=trace[:tstart]
            for i in range(tstart,len(trace)):
                for xi,xc in enumerate(xcoeff):
                    new_trace[i]+=trace[i-xi]*xc
                for yi,yc in enumerate(ycoeff):
                    new_trace[i]+=new_trace[i-yi-1]*yc
            return new_trace
    else:
        raise


def iir_apply_complex(trace, xcoeff, ycoeff):
    """
    Wrapper for :func:`iir_apply` function that accounts for the trace being possibly complex (coefficients still have to be real)
    and for datatable types.
    """
    wrap=wrapping.wrap(trace)
    trace=np.asarray(trace)
    if np.iscomplexobj(trace):
        return wrap.array_replaced(iir_apply(trace.real,xcoeff,ycoeff)+1j*iir_apply(trace.imag,xcoeff,ycoeff),wrapped=False)
    else:
        return wrap.array_replaced(iir_apply(trace,xcoeff,ycoeff),wrapped=False)