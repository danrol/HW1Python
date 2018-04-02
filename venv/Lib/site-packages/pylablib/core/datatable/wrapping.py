"""
Utilites for uniform treatment of DataTable and numpy array objects for functions which can deal with them both.
"""

from . import column
from . import table as datatable
from . import table_storage
from ..utils import iterator as iterator_utils #@UnresolvedImport

import numpy as np


class IGenWrapper(object):
    """
    The interface for a wrapper that gives a uniform access to basic methods of wrapped objects'.
    """
    def __init__(self, container):
        object.__init__(self)
        self.cont=container
    def __getitem__(self, idx):
        return self.cont[idx]
    def __setitem__(self, idx, val):
        self.cont[idx]=val
    def __iter__(self):
        return self.cont.__iter__()
    def get_type(self):
        """Get a string representing the wrapped object type"""
        raise NotImplementedError("IGenWrapper.get_type")
    def copy(self, wrapped=True):
        """Copy the object. If ``wrapped==True``, return a new wrapper contating the object copy; otherwise, just return the copy."""
        raise NotImplementedError("IGenWrapper.copy")
    def ndim(self):
        return self.cont.ndim
    def shape(self):
        return self.cont.shape
    
    
class I1DWrapper(IGenWrapper):
    """
    A wrapper containing a 1D object (a 1D numpy array or a `IDataColumn` object).

    Provides a uniform access to basic methods of a wrapped object.
    """
    def __init__(self, container):
        IGenWrapper.__init__(self, container)
        self.r=self.Accessor(self)
        self.t=self.Accessor(self)
    class Accessor(object):
        """
        An accessor: creates a simple unform interface to treat the wrapped object element-wise (get/set/iterate over elements).

        Generated automatically for each table on creation, doesn't need to be created explicitly.
        """
        def __init__(self, wrapper):
            object.__init__(self)
            self._wrapper=wrapper
        def __iter__(self):
            return self._wrapper.__iter__()
        def __getitem__(self, idx):
            return self._wrapper.subcolumn(idx,wrapped=False)
        def __setitem__(self, idx, val):
            self._wrapper[idx]=val
    def subcolumn(self, idx, wrapped=True):
        """
        Return a subcolumn at index `idx`.

        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        raise NotImplementedError("I1DWrapper.subtable")
    @staticmethod
    def from_array(array, force_copy=False, force_numpy=True, try_optimizing=False, wrapped=True):
        """
        Build a new object of the type corresponding to the wrapper from the supplied `array` (a 1D numpy array or a list).

        If ``force_copy==True``, make a copy of supplied array.
        For a :class:`Column1DWrapper`, if `column` is a list and ``force_numpy==True``, turn it into a numpy array and return :class:`ArrayDataColumn`
        (by default lists are wrapped into :class:`ListDataColumn`).
        For a :class:`Column1DWrapper`, if ``try_optimizing==True``, check if the column can be turned into a :class:`LinearDataColumn`.
        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        raise NotImplementedError("I1DWrapper.from_array")
    @classmethod
    def from_columns(cls, columns, column_names=None, wrapped=True):
        """
        Build a new object of the type corresponding to the wrapper from the supplied `columns` (a list of columns; only length-1 lists is supported).

        `column_names` parameter is ignored.
        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        if len(columns)!=1:
            raise ValueError("Array1DWrapper only supports single columns, got {} columns".format(len(columns)))
        return cls.from_array(columns[0])
    def array_replaced(self, array, force_copy=False, force_numpy=True, try_optimizing=False, wrapped=True):
        """
        Return a copy of the column with the data replaced by `array`.

        All of the parameters are the same as in :func:`from_array`.
        """
        return self.from_array(array, force_copy=force_copy, force_numpy=force_numpy, try_optimizing=try_optimizing, wrapped=wrapped)
    def get_type(self):
        """Get a string representing the wrapped object type"""
        raise NotImplementedError("I1DWrapper.get_type")
    def copy(self, wrapped=True):
        """Copy the object. If ``wrapped==True``, return a new wrapper contating the object copy; otherwise, just return the copy."""
        raise NotImplementedError("I1DWrapper.copy")
    def ndim(self):
        return 1
    
class Array1DWrapper(I1DWrapper):
    """
    A wrapper for a 1D numpy array.

    Provides a uniform access to basic methods of a wrapped object.
    """
    def __init__(self, container):
        container=np.asarray(container)
        if container.ndim!=1:
            raise ValueError("Array1DWrapper only supports 1D arrays, got {}D array".format(container.ndim))
        I1DWrapper.__init__(self, container)
    
    def get_deleted(self, idx, wrapped=True):
        """
        Return a copy of the column with the data at index `idx` deleted.

        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        new_cont=np.delete(self.cont, idx, axis=0)
        return Array1DWrapper(new_cont) if wrapped else new_cont
    def __delitem__(self, idx):
        self.cont=self.get_deleted(idx,wrapped=False)
    def get_inserted(self, idx, val, wrapped=True):
        """
        Return a copy of the column with the data `val` added at index `idx`.
        
        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        new_cont=np.insert(self.cont, idx, val, axis=0)
        return Array1DWrapper(new_cont) if wrapped else new_cont
    def insert(self, idx, val):
        """Add data `val` to index `idx`."""
        self.cont=self.get_inserted(idx,val,wrapped=False)
    def get_appended(self, val, wrapped=True):
        """
        Return a copy of the column with the data `val` appended at the end.
        
        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        new_cont=np.append(self.cont, val, axis=0)
        return Array1DWrapper(new_cont) if wrapped else new_cont
    def append(self, val):
        """Append data `val` to the end."""
        self.cont=self.get_appended(val,wrapped=False)
    def subcolumn(self, idx, wrapped=True):
        """
        Return a subcolumn at index `idx`.

        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        return Array1DWrapper(self.cont[idx]) if wrapped else self.cont[idx]
    @staticmethod
    def from_array(array, force_copy=False, force_numpy=True, try_optimizing=False, wrapped=True):
        """
        Build a new object of the type corresponding to the wrapper from the supplied `array` (a 1D numpy array or a list).

        If ``force_copy==True``, make a copy of supplied array.
        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        `force_numpy` and `try_optimizing` parameters are ignored.
        """
        new_cont=np.array(array) if force_copy else np.asarray(array)
        return Array1DWrapper(new_cont) if wrapped else new_cont
    def get_type(self):
        """Get a string representing the wrapped object type"""
        return "1d.array"
    def copy(self, wrapped=True):
        """Copy the object. If ``wrapped==True``, return a new wrapper contating the object copy; otherwise, just return the copy."""
        new_cont=self.cont.copy()
        return Array1DWrapper(new_cont) if wrapped else new_cont
    

class Column1DWrapper(I1DWrapper):
    """
    A wrapper for an :class:`IDataColumn` object.

    Provides a uniform access to basic methods of a wrapped object.
    """
    def __init__(self, container):
        if not isinstance(container, column.IDataColumn):
            container=column.as_column(container,force_copy=False)
        I1DWrapper.__init__(self, container)
    
    def get_deleted(self, idx, wrapped=True):
        """
        Return a copy of the column with the data at index `idx` deleted.

        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        new_cont=self.cont.copy()
        del self.cont[idx]
        return Column1DWrapper(new_cont) if wrapped else new_cont
    def __delitem__(self, idx):
        del self.cont[idx]
    def get_inserted(self, idx, val, wrapped=True):
        """
        Return a copy of the column with the data `val` added at index `idx`.
        
        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        new_cont=self.cont.copy()
        new_cont.insert(val,idx)
        return Column1DWrapper(new_cont) if wrapped else new_cont
    def insert(self, idx, val):
        """Add data `val` to index `idx`."""
        self.cont.insert(idx,val)
    def get_appended(self, val, wrapped=True):
        """
        Return a copy of the column with the data `val` appended at the end.
        
        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        new_cont=self.cont.copy()
        new_cont.append(val)
        return Column1DWrapper(new_cont) if wrapped else new_cont
    def append(self, val):
        """Append data `val` to the end."""
        self.cont.append(val)
    def subcolumn(self, idx, wrapped=True):
        """
        Return a subcolumn at index `idx`.

        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        return Column1DWrapper(self.cont.subcolumn(idx)) if wrapped else self.cont.subcolumn(idx)
    @staticmethod
    def from_array(array, force_copy=False, force_numpy=True, try_optimizing=False, wrapped=True):
        """
        Build a new object of the type corresponding to the wrapper from the supplied `array` (a 1D numpy array or a list).

        If ``force_copy==True``, make a copy of supplied array.
        If `column` is a list and ``force_numpy==True``, turn it into a numpy array and return :class:`ArrayDataColumn`
        (by default lists are wrapped into :class:`ListDataColumn`).
        If ``try_optimizing==True``, check if the column can be turned into a :class:`LinearDataColumn`.
        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        new_cont=column.as_column(array,force_numpy=force_numpy,force_copy=force_copy,try_linear=try_optimizing)
        return Column1DWrapper(new_cont) if wrapped else new_cont
    def get_type(self):
        """Get a string representing the wrapped object type"""
        return "1d.column"
    def copy(self, wrapped=True):
        """Copy the object. If ``wrapped==True``, return a new wrapper contating the object copy; otherwise, just return the copy."""
        new_cont=self.cont.copy()
        return Column1DWrapper(new_cont) if wrapped else new_cont
    
    
    
    
    
    
    
class I2DWrapper(IGenWrapper):
    """
    A wrapper containing a 2D object (a 2D numpy array or a :class:`DataTable` object).

    Provides a uniform access to basic methods of a wrapped object.
    """
    def __init__(self, container, r=None, c=None, t=None):
        IGenWrapper.__init__(self, container)
        self.r=r
        self.c=c
        self.t=t
    @staticmethod
    def from_columns(columns, column_names=None, wrapped=True):
        """
        Build a new object of the type corresponding to the wrapper from the supplied `columns` (a list of columns).

        `column_names` supplies names of the columns (only relevant for :class:`Table2DWrapper`).
        If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
        """
        raise NotImplementedError("I2DWrapper.from_columns")
    def columns_replaced(self, columns, wrapped=True):
        """
        Return copy of the object with the data replaced by `columns`.
        
        If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
        """
        return self.from_columns(columns, self.c.get_names(), wrapped=wrapped)
    @staticmethod
    def from_array(array, column_names=None, force_copy=False, wrapped=True):
        """
        Build a new object of the type corresponding to the wrapper from the supplied `array` (a list of rows or a 2D numpy array).

        `column_names` supplies names of the columns (only relevant for :class:`Table2DWrapper`).
        If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
        """
        raise NotImplementedError("I2DWrapper.from_array")
    def array_replaced(self, array, force_copy=False, wrapped=True):
        """
        Return a copy of the column with the data replaced by `array`.

        All of the parameters are the same as in :func:`from_array`.
        """
        return self.from_array(array, self.c.get_names(), force_copy=force_copy, wrapped=wrapped)
    def get_type(self):
        """Get a string representing the wrapped object type"""
        raise NotImplementedError("I2DWrapper.get_type")
    def copy(self, wrapped=True):
        """Copy the object. If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table."""
        raise NotImplementedError("I2DWrapper.copy")
    def column(self, idx, wrapped=True):
        """
        Get a column at index `idx`.

        Return a 1D numpy array for a 2D numpy array object, and an :class:`IDataColumn` object for a :class:`DataTable`.
        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        raise NotImplementedError("I2DWrapper.column")
    def subtable(self, idx, wrapped=True):
        """
        Return a subtable at index `idx`.
        
        If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
        """
        raise NotImplementedError("I2DWrapper.subtable")
    def ndim(self):
        return 2
    
    
    
class Array2DWrapper(I2DWrapper):
    """
    A wrapper for a 2D numpy array.

    Provides a uniform access to basic methods of a wrapped object.
    """
    def __init__(self, container):
        container=np.asarray(container)
        if container.ndim!=2:
            raise ValueError("Array2DWrapper only supports 2D arrays, got {}D array".format(container.ndim))
        I2DWrapper.__init__(self, container, 
                self.RowAccessor(self,container), self.ColumnAccessor(self,container), self.TableAccessor(container))
    
    def set_container(self,cont):
        self.cont=cont
        self.r._storage=cont
        self.c._storage=cont
        self.t._storage=cont
    class RowAccessor(object):
        """
        A row accessor: creates a simple unform interface to treat the wrapped object row-wise (append/insert/delete/iterate over rows).

        Generated automatically for each table on creation, doesn't need to be created explicitly.
        """
        def __init__(self, wrapper, storage):
            object.__init__(self)
            self._wrapper=wrapper
            self._storage=storage
        def __iter__(self):
            return iterator_utils.AccessIterator(self._storage, lambda obj, idx: obj[idx])
        def __getitem__(self, idx):
            return self._storage[idx]
        def __setitem__(self, idx, val):
            self._storage[idx]=val
        def get_deleted(self, idx, wrapped=True):
            """
            Return a new table with the rows at `idx` deleted.

            If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
            """
            new_cont=np.delete(self._storage, idx, axis=0)
            return Array2DWrapper(new_cont) if wrapped else new_cont
        def __delitem__(self, idx):
            self._wrapper.set_container(self.get_deleted(idx,wrapped=False))
        def get_inserted(self, idx, val, wrapped=True):
            """
            Return a new table with new rows given by `val` inserted at `idx`.

            If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
            """
            new_cont=np.insert(self._storage, idx, val, axis=0)
            return Array2DWrapper(new_cont) if wrapped else new_cont
        def insert(self, idx, val):
            """
            Insert new rows given by `val` at index `idx`.
            """
            self._wrapper.set_container(self.get_inserted(idx,val,wrapped=False))
        def get_appended(self, val, wrapped=True):
            """
            Return a new table with new rows given by `val` appended to the end of the table.

            If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
            """
            new_cont=np.append(self._storage, val, axis=0)
            return Array2DWrapper(new_cont) if wrapped else new_cont
        def append(self, val):
            """Insert new rows given by `val` to the end of the table."""
            self._wrapper.set_container(self.get_appended(val,wrapped=False))
    
    class ColumnAccessor(object):
        """
        A column accessor: creates a simple unform interface to treat the wrapped object column-wise (append/insert/delete/iterate over columns).

        Generated automatically for each table on creation, doesn't need to be created explicitly.
        """
        def __init__(self, wrapper, storage):
            object.__init__(self)
            self._wrapper=wrapper
            self._storage=storage
        def __iter__(self):
            return iterator_utils.AccessIterator(self._storage, lambda obj, idx: obj[:,idx])
        def __getitem__(self, idx):
            return self._storage[:,idx]
        def __setitem__(self, idx, val):
            self._storage[:,idx]=val
        def get_deleted(self, idx, wrapped=True):
            """
            Return a new table with the columns at `idx` deleted.

            If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
            """
            new_cont=np.delete(self._storage, idx, axis=1)
            return Array2DWrapper(new_cont) if wrapped else new_cont
        def __delitem__(self, idx):
            self._wrapper.set_container(self.get_deleted(idx,wrapped=False))
        def get_inserted(self, idx, val, wrapped=True):
            """
            Return a new table with new columns given by `val` inserted at `idx`.

            If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
            """
            new_cont=np.insert(self._storage, idx, val, axis=1)
            return Array2DWrapper(new_cont) if wrapped else new_cont
        def insert(self, idx, val):
            """
            Insert new columns given by `val` at index `idx`.
            """
            self._wrapper.set_container(self.get_inserted(idx,val,wrapped=False))
        def get_appended(self, val, wrapped=True):
            """
            Return a new table with new columns given by `val` appended to the end of the table.

            If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
            """
            new_cont=np.append(self._storage, val, axis=1)
            return Array2DWrapper(new_cont) if wrapped else new_cont
        def append(self, val):
            """Insert new columns given by `val` to the end of the table."""
            self._wrapper.set_container(self.get_appended(val,wrapped=False))
        def set_names(self, names):
            """Set column names (does nothing)."""
            pass
        def get_names(self):
            """Get column names (all names are ``None``)."""
            return [None]*self._storage.shape[1]
    
    class TableAccessor(object):
        """
        A table accessor: acessing the table data through this interface returns an object of the appropriate type
        (numpy array for numpy wrapped object, and :class:`DataTable` for :class:`DataTable` wrapped object).

        Generated automatically for each table on creation, doesn't need to be created explicitly.
        """
        def __init__(self, storage):
            object.__init__(self)
            self._storage=storage
        def __iter__(self):
            return iterator_utils.AccessIterator(self)
        def __getitem__(self, idx):
            return self._storage[idx]
        def __setitem__(self, idx, val):
            self._storage[idx]=val
    
    def subtable(self, idx, wrapped=True):
        """
        Return a subtable at index `idx` of the appropriate tybe (2D numpy array).
        
        If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
        """
        return Array2DWrapper(self.cont[idx]) if wrapped else self.cont[idx]
    def column(self, idx, wrapped=True):
        """
        Get a column at index `idx` as a 1D numpy array.

        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        return Array1DWrapper(self.cont[:,idx]) if wrapped else self.cont[:,idx]
    @staticmethod
    def from_columns(columns, column_names=None, wrapped=True):
        """
        Build a new object of the type corresponding to the wrapper from the supplied `columns` (a list of columns).

        If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
        `column_names` parameter is ignored.
        """
        new_cont=np.column_stack(columns)
        return Array2DWrapper(new_cont) if wrapped else new_cont
    @staticmethod
    def from_array(array, column_names=None, force_copy=False, wrapped=True):
        """
        Build a new object of the type corresponding to the wrapper from the supplied `array` (a list of rows or a 2D numpy array).

        If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
        `column_names` parameter is ignored.
        """
        new_cont=np.array(array) if force_copy else np.asarray(array)
        return Array2DWrapper(new_cont) if wrapped else new_cont
    def get_type(self):
        """Get a string representing the wrapped object type"""
        return "2d.array"
    def copy(self, wrapped=True):
        """Copy the object. If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table."""
        new_cont=self.cont.copy()
        return Array2DWrapper(new_cont) if wrapped else new_cont
    

class Table2DWrapper(I2DWrapper):
    """
    A wrapper for a :class:`DataTable` object.

    Provides a uniform access to basic methods of a wrapped object.
    """
    def __init__(self, container):
        if not isinstance(container, datatable.DataTable):
            container=datatable.DataTable(container,force_copy=False)
        if container.ndim!=2:
            raise ValueError("Table2DWrapper only supports 2D arrays, got {}D array".format(container.ndim))
        I2DWrapper.__init__(self, container,
                    self.RowAccessor(self,container), self.ColumnAccessor(self,container), self.TableAccessor(container))
    
    class RowAccessor(object):
        """
        A row accessor: creates a simple unform interface to treat the wrapped object row-wise (append/insert/delete/iterate over rows).

        Generated automatically for each table on creation, doesn't need to be created explicitly.
        """
        def __init__(self, wrapper, storage):
            object.__init__(self)
            self._wrapper=wrapper
            self._storage=storage
        def __iter__(self):
            return self._storage.ra.__iter__()
        def __getitem__(self, idx):
            return self._storage.ra[idx]
        def __setitem__(self, idx, val):
            self._storage.r[idx]=val
        def get_deleted(self, idx, wrapped=True):
            """
            Return a new table with the rows at `idx` deleted.

            If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
            """
            new_cont=self._storage.copy()
            del new_cont.r[idx]
            return Table2DWrapper(new_cont) if wrapped else new_cont
        def __delitem__(self, idx):
            del self._storage.r[idx]
        def get_inserted(self, idx, val, wrapped=True):
            """
            Return a new table with new rows given by `val` inserted at `idx`.

            If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
            """
            new_cont=self._storage.copy()
            new_cont.r.insert(idx,val)
            return Table2DWrapper(new_cont) if wrapped else new_cont
        def insert(self, idx, val):
            """
            Insert new rows given by `val` at index `idx`.
            """
            self._storage.r.insert(idx,val)
        def get_appended(self, val, wrapped=True):
            """
            Return a new table with new rows given by `val` appended to the end of the table.

            If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
            """
            new_cont=self._storage.copy()
            new_cont.r.append(val)
            return Table2DWrapper(new_cont) if wrapped else new_cont
        def append(self, val):
            """Insert new rows given by `val` to the end of the table."""
            self._storage.r.append(val)
            
    class ColumnAccessor(object):
        """
        A column accessor: creates a simple unform interface to treat the wrapped object column-wise (append/insert/delete/iterate over columns).

        Generated automatically for each table on creation, doesn't need to be created explicitly.
        """
        def __init__(self, wrapper, storage):
            object.__init__(self)
            self._wrapper=wrapper
            self._storage=storage
        def __iter__(self):
            return self._storage.c.__iter__()
        def __getitem__(self, idx):
            return self._storage.c[idx]
        def __setitem__(self, idx, val):
            self._storage.c[idx]=val
        def get_deleted(self, idx, wrapped=True):
            """
            Return a new table with the columns at `idx` deleted.

            If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
            """
            new_cont=self._storage.copy(copy_columns=False)
            del new_cont.c[idx]
            return Table2DWrapper(new_cont) if wrapped else new_cont
        def __delitem__(self, idx):
            del self._storage.c[idx]
        def get_inserted(self, idx, val, wrapped=True):
            """
            Return a new table with new columns given by `val` inserted at `idx`.

            If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
            """
            new_cont=self._storage.copy(copy_columns=False)
            new_cont.c.insert(idx,val)
            return Table2DWrapper(new_cont) if wrapped else new_cont
        def insert(self, idx, val):
            """Insert new columns given by `val` at index `idx`."""
            self._storage.c.insert(idx,val)
        def get_appended(self, val, wrapped=True):
            """
            Return a new table with new columns given by `val` appended to the end of the table.

            If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
            """
            new_cont=self._storage.copy(copy_columns=False)
            new_cont.c.append(val)
            return Table2DWrapper(new_cont) if wrapped else new_cont
        def append(self, val):
            """Insert new columns given by `val` to the end of the table."""
            self._storage.c.append(val)
        def set_names(self, names):
            """Set column names."""
            self._storage.set_column_names(names)
        def get_names(self):
            """Get column names."""
            return self._storage.get_column_names()
    
    class TableAccessor(object):
        """
        A table accessor: acessing the table data through this interface returns an object of the appropriate type
        (numpy array for numpy wrapped object, and :class:`DataTable` for :class:`DataTable` wrapped object).

        Generated automatically for each table on creation, doesn't need to be created explicitly.
        """
        def __init__(self, storage):
            object.__init__(self)
            self._storage=storage
        def __iter__(self):
            return self._storage.t.__iter__()
        def __getitem__(self, idx):
            return self._storage.t[idx]
        def __setitem__(self, idx, val):
            self._storage.t[idx]=val
    
    def subtable(self, idx, wrapped=True):
        """
        Return a subtable at index `idx` of the appropriate tybe (:class:`DataTable`).
        
        If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
        """
        return Table2DWrapper(self.cont.t[idx]) if wrapped else self.cont.t[idx]
    def column(self, idx, wrapped=True):
        """
        Get a column at index `idx` as an :class:`IDataColumn` object.

        If ``wrapped==True``, return a new wrapper contating the column; otherwise, just return the column.
        """
        return Column1DWrapper(self.cont.c[idx]) if wrapped else self.cont.c[idx]
    @staticmethod
    def from_columns(columns, column_names=None, wrapped=True):
        """
        Build a new object of the type corresponding to the wrapper from the supplied `columns` (a list of columns).

        `column_names` supplies names of the columns (only relevant for :class:`Table2DWrapper`).
        If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
        """
        new_cont=datatable.DataTable(columns,column_names)
        return Table2DWrapper(new_cont) if wrapped else new_cont
    @staticmethod
    def from_array(array, column_names=None, force_copy=False, wrapped=True):
        """
        Build a new object of the type corresponding to the wrapper from the supplied `array` (a list of rows or a 2D numpy array).

        `column_names` supplies names of the columns (only relevant for :class:`Table2DWrapper`).
        If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table.
        """
        new_cont=datatable.DataTable(array,column_names,force_copy=force_copy)
        return Table2DWrapper(new_cont) if wrapped else new_cont
    def get_type(self):
        """Get a string representing the wrapped object type"""
        return "2d.table"
    def copy(self, wrapped=True):
        """Copy the object. If ``wrapped==True``, return a new wrapper contating the table; otherwise, just return the table."""
        new_cont=self.cont.copy()
        return Table2DWrapper(new_cont) if wrapped else new_cont
    





def wrap1d(container):
    """
    Wrap a 1D container (a 1D numpy array or an :class:`IDataColumn`) into an appropriate wrapper.
    """
    if isinstance(container, column.IDataColumn):
        return Column1DWrapper(container)
    return Array1DWrapper(container)
def wrap2d(container):
    """
    Wrap a 2D container (a 2D numpy array or a :class:`DataTable`) into an appropriate wrapper.
    """
    if isinstance(container, datatable.DataTable):
        return Table2DWrapper(container)
    return Array2DWrapper(container)
def wrap(container):
    """
    Wrap container (a numpy array, an :class:`IDataColumn` or a :class:`DataTable`) into an appropriate wrapper.
    """
    if isinstance(container,IGenWrapper):
        return container
    ndim=len(table_storage.get_shape(container))
    if ndim==1:
        return wrap1d(container)
    elif ndim==2:
        return wrap2d(container)
    else:
        raise ValueError("wrap only supports 1D and 2D arrays, got {}D".format(ndim))