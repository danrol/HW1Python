"""
Classes for dealing with the :class:`~core.utils.dictionary.Dictionary` entries with special conversion rules when saved or loaded.
Used to redefine how ceratin objects (e.g., tables) are written into files and read from files.
"""


from ..utils import dictionary #@UnresolvedImport
from ..datatable import table as datatable #@UnresolvedImport
from . import location, parse_csv

import numpy as np



def special_load_rules(branch):
    """
    Detect if the branch requires special conversion rules.
    """
    try:
        return "__data_type__" in branch
    except TypeError:
        return False

### General description ###

class IDictionaryEntry(object):
    """
    A generic `Dictionary` entry.
    """
    def __init__(self, data=None):
        object.__init__(self)
        self.set_data(data)
        
    def set_data(self, data=None):
        """
        Set internal data.
        """
        self.data=data
    def get_data(self):
        """
        Get internal data.
        """
        return self.data
    
    def to_dict(self, dict_ptr, loc):
        """
        Convert data to a dictionary branch on saving.
        
        Virtual method, to be defined in subclasses.
        
        Args:
            dict_ptr (~core.utils.dictionary.DictionaryPointer): Pointer to the dictionary location for the entry.
            loc: Location for the data to be saved.
        """
        raise NotImplementedError("IDictionaryEntry.to_dict")
    
    @staticmethod
    def build_entry(data=None, dict_ptr=None, loc=None, **kwargs):
        """
        Create a `DictionaryEntry` object based on the supplied data and arguments.
        
        Args:
            data: Data to be saved.
            dict_ptr (~core.utils.dictionary.DictionaryPointer): Pointer to the dictionary location for the entry.
            loc: Location for the data to be saved.
        """
        if isinstance(data, IDictionaryEntry):
            return data
        if isinstance(data, np.ndarray) or isinstance(data, datatable.DataTable) or data=="table":
            return ITableDictionaryEntry.build_entry(data, dict_ptr, loc, **kwargs)
        return None
    
    @staticmethod
    def from_dict(dict_ptr, loc, **kwargs):
        """
        Convert a dictionary branch to a specific `DictionaryEntry` object.
        
        Args:
            dict_ptr (~core.utils.dictionary.DictionaryPointer): Pointer to the dictionary location for the entry.
            loc: Location for the data to be loaded.
        """
        data_type=dict_ptr["__data_type__"]
        if data_type=="table":
            return ITableDictionaryEntry.from_dict(dict_ptr,loc,**kwargs)
        
def build_entry(data=None, dict_ptr=None, loc=None, **kwargs):
    return IDictionaryEntry.build_entry(data,dict_ptr,loc,**kwargs)
    






###  Table formatters  ###

class ITableDictionaryEntry(IDictionaryEntry):
    """
    A generic table Dictionary entry.
    
    Args:
        data: Table data.
        columns (list): If not ``None``, list of column names (if ``None`` and data is a DataTable object, get column names from that). 
    """
    
    def __init__(self, data=None, columns=None):
        IDictionaryEntry.__init__(self,data)
        self.columns=columns
        
    def _get_columns(self):
        if self.columns is None and isinstance(self.data, datatable.DataTable):
            return self.data.get_column_names()
        else:
            return self.columns
        
    @staticmethod
    def build_entry(data=None, dict_ptr=None, loc=None, table_format="inline", **kwargs):
        """
        Create a DictionaryEntry object based on the supplied data and arguments.
        
        Args:
            data: Data to be saved.
            dict_ptr (~core.utils.dictionary.DictionaryPointer): Pointer to the dictionary location for the entry.
            loc: Location for the data to be saved.
            table_format (str): Method of saving the table. Can be either
                ``'inline'`` (table is saved directly in the dictionary file),
                ``'csv'`` (table is saved in an external CSV file) or
                ``'bin'`` (table is saved in an external binary file).
        """
        if isinstance(table_format,ITableDictionaryEntry):
            table_format.set_data(data)
            return table_format
        if table_format=="inline":
            return InlineTableDictionaryEntry(data,**kwargs)
        elif table_format in {"csv","bin"}:
            if table_format in {"csv"}:
                return ExternalTextTableDictionaryEntry(data,file_format=table_format,**kwargs)
            else:
                return ExternalBinTableDictionaryEntry (data,file_format=table_format,**kwargs)
        else:
            raise ValueError("unrecognized table format: {0}".format(table_format))
    @staticmethod
    def from_dict(dict_ptr, loc, out_type="table", **kwargs):
        """
        Convert a dictionary branch to a specific DictionaryEntry object.
        
        Args:
            dict_ptr (~core.utils.dictionary.DictionaryPointer): Pointer to the dictionary location for the entry.
            loc: Location for the data to be loaded.
            out_type (str): Output format of the data (``'array'`` for numpy arrays or ``'table'`` for :class:`DataTable` objects). 
        """
        table_type=dict_ptr.get("__table_type__",None)
        if table_type is None:
            if "data" in dict_ptr:
                table_type="inline"
            elif "file_path" in dict_ptr:
                table_type="external"
            else:
                raise ValueError("unrecognized table format: {0}".format(dict_ptr))
        if table_type=="inline":
            return InlineTableDictionaryEntry.from_dict(dict_ptr,loc,out_type=out_type,**kwargs)
        else:
            return IExternalTableDictionaryEntry.from_dict(dict_ptr,loc,out_type=out_type,**kwargs)
 
class InlineTableDictionaryEntry(ITableDictionaryEntry):
    """
    An inlined table Dictionary entry.
    
    Args:
        data: Table data.
        columns (list): If not ``None``, a list of column names (if ``None`` and data is a DataTable object, get column names from that). 
    """
    def __init__(self, data=None, columns=None, **kwargs):
        ITableDictionaryEntry.__init__(self,data,columns)
    def to_dict(self, dict_ptr, loc):
        """
        Convert the data to a dictionary branch and write the table to the file.
        """
        table=self.data
        if table is None:
            raise ValueError("can't build entry for empty table")
        columns=self._get_columns()
        d=dictionary.Dictionary()
        d["__data_type__"]="table"
        d["__table_type__"]="inline"
        if columns is not None:
            d["columns"]=columns
        d["data"]=table
        return d
    @staticmethod
    def from_dict(dict_ptr, loc, out_type="table", **kwargs):
        """
        Build an :class:`InlineTableDictionaryEntry` object from the dictionary and read the inlined data.
        
        Args:
            dict_ptr (~core.utils.dictionary.DictionaryPointer): Pointer to the dictionary location for the entry.
            loc: Location for the data to be loaded.
            out_type (str): Output format of the data (``'array'`` for numpy arrays or ``'table'`` for :class:`DataTable` objects).
        """
        columns=dict_ptr.get("columns",None)
        data=dict_ptr.get("data",None)
        if data is None:
            raise ValueError("can't load {0} with format {1}".format(dict_ptr,"inline"))
        if len(data)==0:
            data=parse_csv.columns_to_table([],columns=columns,out_type=out_type)
        if out_type=="table":
            if columns:
                data.set_column_names(columns)
        else:
            if columns and len(columns)!=data.shape[1]:
                raise ValueError("columns number doesn't agree with the table size")
            data=np.asarray(data)
        return InlineTableDictionaryEntry(data,columns)

class IExternalTableDictionaryEntry(ITableDictionaryEntry):
    def __init__(self, data, file_format, name, columns, force_name=False, **kwargs):
        from . import savefile
        data,file_format=savefile.get_output_format(data,file_format,**kwargs)
        ITableDictionaryEntry.__init__(self,data,columns)
        self.file_format=file_format
        self.name=location.LocationName.from_object(name)
        self.force_name=force_name
    def _get_name(self, dict_ptr, loc):
        name=self.name
        if name.get_path()=="":
            name=location.LocationName(dict_ptr.get_path()[-1],name.ext)
        if not self.force_name:
            name=loc.generate_new_name(name,idx=None)
        return name
    @staticmethod
    def from_dict(dict_ptr, loc, out_type="table", **vargs):
        file_type=dict_ptr.get("file_type",None)
        if not (file_type in {"bin","csv"}): # TODO:  add autodetect
            raise ValueError("can't load {0} with format {1}".format(dict_ptr,"external"))
        if file_type=="csv":
            return ExternalTextTableDictionaryEntry.from_dict(dict_ptr,loc,out_type=out_type,**vargs)
        else:
            return ExternalBinTableDictionaryEntry.from_dict (dict_ptr,loc,out_type=out_type,**vargs)
class ExternalTextTableDictionaryEntry(IExternalTableDictionaryEntry):
    """
    An external text table Dictionary entry.
    
    Args:
        data: Table data.
        file_format (str): Output file format.
        name (str): Name template for the external file (default is the last key in the path).
        columns (list): If not ``None``, a list of column names (if ``None`` and data is a DataTable object, get column names from that). 
    """
    def __init__(self, data=None, file_format="csv", name="", columns=None, **kwargs):
        IExternalTableDictionaryEntry.__init__(self,data,file_format,name,columns,**kwargs)
    def to_dict(self, dict_ptr, loc):
        """
        Convert the data to a dictionary branch and save the table to an external file.
        """
        table=self.data
        if table is None:
            raise ValueError("can't build entry for empty table")
        columns=self._get_columns()
        name=self._get_name(dict_ptr,loc)
        d=dictionary.Dictionary()
        d["__data_type__"]="table"
        d["__table_type__"]="external"
        d["file_type"]=self.file_format.format_name
        save_file=location.LocationFile(loc,name)
        self.file_format.write(save_file,table,columns=columns)
        d["file_path"]=save_file.get_path()
        return d
    @staticmethod
    def from_dict(dict_ptr, loc, out_type="table"):
        """
        Build an :class:`ExternalTextTableDictionaryEntry` object from the dictionary and load the external data.
        
        Args:
            dict_ptr (~core.utils.dictionary.DictionaryPointer): Pointer to the dictionary location for the entry.
            loc: Location for the data to be loaded.
            out_type (str): Output format of the data (``'array'`` for numpy arrays or ``'table'`` for :class:`DataTable` objects).
        """
        from . import loadfile
        file_path=dict_ptr["file_path"]
        file_type=dict_ptr.get("file_type","csv")
        load_file=location.LocationFile(loc,file_path)
        data=loadfile.IInputFileFormat.read_file(load_file,file_format=file_type,out_type=out_type).data
        return ExternalTextTableDictionaryEntry(data,name=load_file.name)
class ExternalBinTableDictionaryEntry(IExternalTableDictionaryEntry):
    """
    An external binary table Dictionary entry.
    
    Args:
        data: Table data.
        file_format (str): Output file format.
        name (str): Name template for the external file (default is the last key in the path).
        columns (list): If not ``None``, a list of column names (if ``None`` and data is a DataTable object, get column names from that). 
    """
    def __init__(self, data=None, file_format="bin", name="", columns=None, **kwargs):
        IExternalTableDictionaryEntry.__init__(self,data,file_format,name,columns, **kwargs)
    def to_dict(self, dict_ptr, loc):
        """
        Convert the data to a dictionary branch and save the table to an external file.
        """
        table=self.data
        if table is None:
            raise ValueError("can't build entry for empty table")
        columns=self._get_columns()
        name=self._get_name(dict_ptr,loc)
        d=dictionary.Dictionary()
        d["__data_type__"]="table"
        d["__table_type__"]="external"
        d["file_type"]=self.file_format.format_name
        if columns is not None:
            d["columns"]=columns
        save_file=location.LocationFile(loc,name)
        self.file_format.write(save_file,table)
        d.merge_branch(self.file_format.get_preamble(save_file,table),"preamble")
        d["file_path"]=save_file.get_path()
        return d
    @staticmethod
    def from_dict(dict_ptr, loc, out_type="table", **vargs):
        """
        Build an :class:`ExternalBinTableDictionaryEntry` object from the dictionary and load the external data.
        
        Args:
            dict_ptr (~core.utils.dictionary.DictionaryPointer): Pointer to the dictionary location for the entry.
            loc: Location for the data to be loaded.
            out_type (str): Output format of the data (``'array'`` for numpy arrays or ``'table'`` for :class:`DataTable` objects).
        """
        from . import loadfile
        file_path=dict_ptr["file_path"]
        file_type=dict_ptr.get("file_type","bin")
        preamble=dict_ptr.get("preamble",None)
        columns=dict_ptr.get("columns",None)
        load_file=location.LocationFile(loc,file_path)
        data=loadfile.IInputFileFormat.read_file(load_file,file_format=file_type,preamble=preamble,columns=columns).data
        return ExternalBinTableDictionaryEntry(data,name=load_file.name)