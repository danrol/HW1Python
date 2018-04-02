"""
Universal function fitting interface.
"""

from __future__ import division
from ..utils.py3 import textstring

from ..utils import general as general_utils #@UnresolvedImport
from ..utils import funcargparse #@UnresolvedImport
from ..dataproc import callable #@UnresolvedImport
import numpy as np
import scipy.optimize


class Fitter(object):
    """
    Fitter object.
    
    Can handle variety of different functions, complex arguments or return values, array arguments.
    
    Args:
        func(Callable): Fit function. Can be anything callable (function, method, object with ``__call__`` method, etc.).
        xarg_name(str or list): Name (or multiple names) for x arguments. These arguments are passed to `func` (as named arguments) when calling for fitting.
            Can be a string (single argument) or a list (arbitrary number of arguments, including zero).
        fit_paramters (dict): Dictionary ``{name: value}`` of parameters to be fitted (`value` is the starting value for the fitting procedure).
            If `value` is ``None``, try and get the default value from the `func`.
        fixed_paramters (dict): Dictionary ``{name: value}`` of parameters to be fixed during the fitting procedure.
            If `value` is ``None``, try and get the default value from the `func`.
    """
    def __init__(self, func, xarg_name=None, fit_parameters=None, fixed_parameters=None):
        object.__init__(self)
        self.func=callable.to_callable(func)
        self.set_xarg_name(xarg_name or [])
        self.set_fixed_parameters(fixed_parameters)
        self.set_fit_parameters(fit_parameters)
    
    def _prepare_parameters(self, fit_parameters):
        """Normalize fit_parameters"""
        fit_parameters=general_utils.to_pairs_list(fit_parameters)
        parameters={}
        for name,val in fit_parameters:
            if isinstance(val,textstring) and val=="complex":
                val=complex(self.func.get_arg_default(name))
            elif val is None:
                val=self.func.get_arg_default(name)
            parameters[name]=val
        return parameters
    @staticmethod
    def _pack_parameters(value):
        """Pack parameters into an array of floats"""
        if funcargparse.is_sequence(value,"array"):
            return [p for v in value for p in Fitter._pack_parameters(v)]
        if np.iscomplexobj(value):
            return [np.real(value),np.imag(value)]
        try:
            return value.as_float_array() # function is assumed to take no arguments and return a float array
        except AttributeError:
            return [value]
    @staticmethod
    def _build_unpacker_single(packed, template):
        """Build a function that unpackes and array of floats into a parameters array.
        Return 2 values: function and the number of consumed array elements."""
        if funcargparse.is_sequence(template,"array"):
            ufs=[]
            uns=[]
            n=0
            for pv in template:
                uf,un=Fitter._build_unpacker_single(packed[n:],pv)
                ufs.append(uf)
                uns.append(n)
                n+=un
            def unpack(p):
                return [uf(p[un:]) for uf,un in zip(ufs,uns)]
            return unpack,n
        if np.iscomplexobj(template):
            return (lambda p: p[0]+1j*p[1]), 2
        try:
            v,n=template.from_float_array(packed) # function is assumed to take 1 argument (float array) and return 2 values: the unpacked element and the number of consumed floats
            return (lambda p: template.from_float_array(p)[0]),n
        except AttributeError:
            return (lambda p: p[0]), 1
    @staticmethod
    def _build_unpacker(template):
        """Build a function that unpackes and array of floats into a parameters array."""
        packed=Fitter._pack_parameters(template)
        unpacker,n=Fitter._build_unpacker_single(packed,template)
        if n!=len(packed):
            raise RuntimeError("part of the array hasn't been unpacked: processed {} out of {} elements".format(n,len(packed)))
        return unpacker
    
    def set_xarg_name(self, xarg_name):
        """
        Set names of x arguments.
        
        Can be a string (single argument) or a list (arbitrary number of arguments, including zero).
        """
        if isinstance(xarg_name,list) or isinstance(xarg_name,tuple):
            self.xarg_name=xarg_name
            self.single_xarg=False
        else:
            self.xarg_name=[xarg_name]
            self.single_xarg=True
    def use_xarg(self):
        """Return ``True`` if the function requires x arguments."""
        return len(self.xarg_name)>0
    def set_fixed_parameters(self, fixed_parameters):
        """Change fixed parameters."""
        self.fixed_parameters=dict(fixed_parameters or {})
    def update_fixed_parameters(self, fixed_parameters):
        """Update the dictionary of fixed parameters."""
        self.fixed_parameters.update(fixed_parameters)
    def del_fixed_parameters(self, fixed_parameters):
        """Remove fixed parameters."""
        for name in fixed_parameters:
            self.fixed_parameters.pop(name,None)
    def set_fit_parameters(self, fit_parameters):
        """Change fit parameters."""
        self.fit_parameters=self._prepare_parameters(fit_parameters)
    def update_fit_parameters(self, fit_parameters):
        """Update the dictionary of fit parameters."""
        fit_parameters=self._prepare_parameters(fit_parameters)
        self.fit_parameters.update(fit_parameters)
    def del_fit_parameters(self, fit_parameters):
        """Change fit parameters."""
        for name in fit_parameters:
            self.fit_parameters.pop(name,None)
            
    def _get_unaccounted_parameters(self, fixed_parameters, fit_parameters):
        supplied_names=set(self.xarg_name)|set(fixed_parameters)|set(fit_parameters)
        unaccounted_names=set.difference(self.func.get_mandatory_args(),supplied_names)
        return unaccounted_names
    
    def fit(self, x, y, fit_parameters=None, fixed_parameters=None, weight=1., return_stderr=False, return_residual=False, **kwargs):
        """
        Fit the data.
        
        Args:
            x: x arguments. If the function has single x argument, `x` is an array-like object;
                otherwise, `x` is a list of array-like objects (can be ``None`` if there are no x parameters).
            y: Target function values.
            fit_parameters (dict): Overrides the default `fit_parameters` of the fitter.
            fixed_parameters (dict): Overrides the default `fixed_parameters` of the fitter.
            weight: Can be an array-like object that determines the relative weight of y-points.
            return_stderr (bool): If ``True``, append `stderr` to the output.
            return_residual: If not ``False``, append `residual` to the output.
        
        Returns:
            tuple: ``(params, bound_func[, stderr][, residual])``:
                - `params`: a dictionary ``{name: value}`` of the parameters supplied to the function (both fit and fixed).
                - `bound_func`: the fit function with all the parameters bound (i.e., it only requires x parameters).
                - `stderr`: a dictionary ``{name: error}`` of standard deviation for fit parameters to the return parameters.
                    If the fitting routine returns no residuals (usually for a bad or an underconstrained fit), all residuals are set to NaN.
                - `residual`: either a full array of residuals ``func(x,**params)-y`` (if ``return_residual=='full'``) or
                    a mean magnitude of the residuals ``mean(abs(func(x,**params)-y)**2)`` (if ``return_residual==True`` or ``return_residual=='mean'``).
        """
        # Applying order: self.fixed_parameters < self.fit_parameters < fixed_parameters < fit_parameters
        fit_parameters=self._prepare_parameters(fit_parameters)
        filtered_fit_paremeters=general_utils.filter_dict(fixed_parameters,self.fit_parameters,exclude=True) # to ensure self.fit_parameters < fixed_parameters
        fit_parameters=general_utils.merge_dicts(filtered_fit_paremeters,fit_parameters)
        fixed_parameters=general_utils.merge_dicts(self.fixed_parameters,fixed_parameters)
        unaccounted_parameters=self._get_unaccounted_parameters(fixed_parameters,fit_parameters)
        if len(unaccounted_parameters)>0:
            raise ValueError("Some of the function parameters are not supplied: {0}".format(unaccounted_parameters))
        x=x if x is not None else []
        if self.single_xarg:
            x=[np.asarray(x)]
        else:
            x=[np.asarray(e) for e in x]
        y=np.asarray(y)
        p_names=list(fit_parameters.keys())
        bound_func=self.func.bind_namelist(self.xarg_name+p_names,**fixed_parameters)
        props=[fit_parameters[name] for name in p_names]
        init_p=self._pack_parameters(props)
        unpacker=self._build_unpacker(props)
        def fit_func(fit_p):
            up=x+unpacker(fit_p)
            y_diff=(np.asarray(y-np.asarray(bound_func(*up)))*weight).flatten()
            if np.iscomplexobj(y_diff):
                y_diff=np.concatenate((y_diff.real,y_diff.imag))
            return y_diff
        lsqres=scipy.optimize.least_squares(fit_func,init_p,**kwargs)
        res,jac,tot_err=lsqres.x,lsqres.jac,lsqres.fun
        try:
            cov=np.linalg.inv(np.dot(jac.transpose(),jac))*(np.sum(tot_err**2)/(len(tot_err)-len(res)))
        except np.linalg.LinAlgError: # singluar matrix
            cov=None
        res=unpacker(res)
        fit_dict=dict(zip(p_names,res))
        params_dict=fixed_parameters.copy()
        params_dict.update(fit_dict)
        bound_func=self.func.bind(self.xarg_name,**params_dict)
        if cov is None: # TODO: figure out why leastsq can return cov=None
            stderr=dict(zip(p_names,unpacker([np.nan]*len(init_p))))
        else:
            stderr=unpacker(np.diag(cov)**0.5)
            stderr=dict(zip(p_names,stderr))
        return_val=params_dict,bound_func
        if return_stderr:
            return_val=return_val+(stderr,)
        if return_residual:
            if return_residual=="full":
                residual=y-bound_func(*x)
            else:
                residual=(abs(y-bound_func(*x))**2).mean()
            return_val=return_val+(residual,)
        return return_val
    def initial_guess(self, fit_parameters=None, fixed_parameters=None, return_stderr=False, return_residual=False):
        """
        Return the initial guess for the fitting.
        
        Args:
            fit_parameters (dict): Overrides the default `fit_parameters` of the fitter.
            fixed_parameters (dict): Overrides the default `fixed_parameters` of the fitter.
        
        Returns:
            tuple: ``(params, bound_func)``.
            
                - `params`: a dictionary ``{name: value}`` of the parameters supplied to the function (both fit and fixed).
                - `bound_func`: the fit function with all the parameters bound (i.e., it only requires x parameters).
        """
        fit_parameters=self._prepare_parameters(fit_parameters)
        params_dict=general_utils.merge_dicts(self.fit_parameters,fit_parameters,self.fixed_parameters,fixed_parameters)
        bound_func=self.func.bind_namelist(self.xarg_name,**params_dict)
        return_val=params_dict,bound_func
        if return_stderr:
            p_names=list(fit_parameters.keys())
            props=[fit_parameters[name] for name in p_names]
            init_p=self._pack_parameters(props)
            unpacker=self._build_unpacker(props)
            stderr=dict(zip(p_names,unpacker([0]*len(init_p))))
            return_val=return_val+(stderr,)
        if return_residual:
            return_val=return_val+(0,)
        return return_val
    
def huge_error(x, factor=100.):
    if np.iscomplex(x):
        return (1+1j)*factor*abs(x)
    else:
        return abs(x)*factor
    
def get_best_fit(x, y, fits):
    """
    Select the best (lowest residual) fit result.
    
    `x` and `y` are the argument and the value of the bound fit function. `fits` is the list of fit results (tuples returned by :func:`Fitter.fit`).
    """
    errors=[(abs(y-f[1](x))**2).mean() for f in fits]
    min_error_idx=np.argmin(errors)
    return fits[min_error_idx]