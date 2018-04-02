from builtins import range

import numpy as np
import scipy.interpolate

from . import waveforms
from ..utils import funcargparse


def _data_range(data):
    return (np.min(data),np.max(data))

def interpolate1D(x, y, kind="linear", axis=-1, copy=True, bounds_error=True, fill_values=np.nan, assume_sorted=False):
#     if fill_values=="bounds":
#         fill_values=y[0],y[-1]
#         bounds_error=False
#     if (not bounds_error) and funcargparse.is_sequence(fill_values,"array"):
#         fill_left,fill_right=tuple(fill_values[:2])
#         interpolate_raw=scipy.interpolate.interp1d(x,y,kind=kind,axis=axis,copy=copy,bounds_error=bounds_error,assume_sorted=assume_sorted)
#         def interpolate(d):
#             min_x,max_x=_data_range(interpolate_raw.x)
#             left_over=(d<min_x)
#             right_over=(d>max_x)
#             res=interpolate_raw(d)
#             try:
#                 res[left_over]=fill_left
#                 res[right_over]=fill_right
#             except TypeError:
#                 if d<min_x:
#                     res=fill_left
#                 elif d>max_x:
#                     res=fill_right
#             if np.isscalar(d):
#                 res=np.asscalar(res)
#             return res
#     else:
#         interpolate_raw=scipy.interpolate.interp1d(x,y,kind=kind,axis=axis,copy=copy,bounds_error=bounds_error,assume_sorted=assume_sorted)
#         def interpolate(d):
#             res=interpolate_raw(d)
#             if np.isscalar(d):
#                 res=np.asscalar(res)
#             return res
#     return interpolate
    """
    1D interpolation.
    
    Simply a wrapper around :func:`scipy.interpolate.interp1d`. 
    """
    if fill_values=="bounds":
        fill_values=y[x.argmin()],y[x.argmax()]
        bounds_error=False
    if funcargparse.is_sequence(fill_values,"array"):
        fill_values=tuple(fill_values[:2])
    return scipy.interpolate.interp1d(x,y,kind=kind,axis=axis,copy=copy,bounds_error=bounds_error,fill_value=fill_values,assume_sorted=assume_sorted)
        

def regular_grid_from_scatter(data, x_points, y_points, x_range=None, y_range=None, method="nearest"):
    """
    Turn irregular scatter-points data into a regular 2D grid function.
    
    Args:
        data: 3-column array [(x,y,z)], where ``z`` is a function of ``x`` and ``y``.
        x_points/y_points: Grid values for x/y axes.
        x_range/y_range: If not ``None``, a tuple specifying the desired range of the data (all points in `data` outside the range are excluded).
        method: Interpolation method (see :func:`scipy.interpolate.griddata` for options).
        
    Returns:
        A nested tuple ``(data, (x_grid, y_grid))``, where all entries are 2D arrays (either with data or with gridpoint locations).
    """
    if x_range is not None:
        data=waveforms.cut_to_range(data,x_range,0)
    else:
        x_range=_data_range(data[:,0])
    if y_range is not None:
        data=waveforms.cut_to_range(data,y_range,1)
    else:
        y_range=_data_range(data[:,1])
    x_grid=np.linspace(x_range[0],x_range[1],x_points)
    y_grid=np.linspace(y_range[0],y_range[1],y_points)
    xi,yi=np.meshgrid(x_grid,y_grid)
    interp_data=scipy.interpolate.griddata((data[:,0],data[:,1]),data[:,2],(xi,yi),method=method)
    return interp_data,(x_grid,y_grid)


def interpolate2D(data, x, y, method="linear"):
    """
    Interpolate data in 2D.
    
    Simply a wrapper around :func:`scipy.interpolate.griddata`.
    
    Args:
        data: 3-column array [(x,y,z)], where ``z`` is a function of ``x`` and ``y``.
        x/y: Arrays of x and y coordinates for the points at which to find the values.
        method: Interpolation method.
    """
    interp_data=scipy.interpolate.griddata((data[:,0],data[:,1]),data[:,2],(x,y),method=method)
    return interp_data

def interpolateND(data, xs, method="linear"):
    """
    Interpolate data in N dimensions.
    
    Simply a wrapper around :func:`scipy.interpolate.griddata`.
    
    Args:
        data: ``(N+1)``-column array ``[(x_1,..,x_N,y)]``, where ``y`` is a function of ``x_1, ... ,x_N``.
        xs: ``N``-tuple of arrays of coordinates for the points at which to find the values.
        method: Interpolation method.
    """
    coords=tuple([data[:,n] for n in range(data.shape[1]-1)])
    interp_data=scipy.interpolate.griddata(coords,data[:,-1],xs,method=method)
    return interp_data