# from io import open

import time
import os.path
from ..utils import string, files as file_utils


class LogFile(object):
    """
    Expanding file.
    
    Args:
        path (str): Path to the destination file.
        default_fmt (list): If not ``None``, it's a defult value of `fmt` for :func:`write_dataline` method. 
    """
    def __init__(self, path, default_fmt=None):
        object.__init__(self)
        self.path=path
        self.sep="\t"
        self.default_fmt=default_fmt
        
    def _get_path(self, line, header, timestamp):
        return self.path
    def _get_timestamp_line(self, timestamp):
        return "{:.3f}".format(timestamp)
    
    def _write_line(self, path, line, header=""):
        if os.path.exists(path):
            with open(path,"a") as f:
                f.seek(0,2)
                f.write("\n"+line)
        else:
            file_utils.ensure_dir(os.path.split(path)[0])
            with open(path,"a") as f:
                if header:
                    f.write(header+"\n")
                f.write(line)
                
    def write_line(self, line, header="", add_timestamp=True):
        """
        Write a single line into the file.
        
        Create the file if it doesn't exist.
        
        Args:
            line (str): Data line to be added.
            header (str): If non-empty, add it to the beginning of the file on creation.
            add_timestamp (bool): If ``True``, add the UNIX timestamp in the beginning of the line.
        """
        timestamp=time.time()
        if add_timestamp:
            line=self._get_timestamp_line(timestamp)+self.sep+line
        path=self._get_path(line,header,timestamp)
        self._write_line(path,line,header)
    def write_dataline(self, data, columns=None, fmt=None, add_timestamp=True):
        """
        Write a single data line into the file. 
        
        Create the file if it doesn't exist.
        
        Args:
            data (list): Data row to be added.
            columns (list): If not ``None``, it's a list of column names to be added as a header on creation.
            fmt (str): If not ``None``, it's a list of format strings for the line entries.
            add_timestamp (bool): If ``True``, add the UNIX timestamp in the beginning of the line.\
        """
        if columns:
            if len(columns)!=len(data):
                raise ValueError("columns dimensions don't agree with data dimensions")
            if add_timestamp:
                columns=["Timestamp"]+columns
            header="# "+self.sep.join(columns)
        else:
            header=""
        fmt=fmt or self.default_fmt
        if fmt is None:
            fmt=[None]*len(data)
        data=[string.to_string(v,location="entry") if f is None else ("{:"+f+"}").format(v) for f,v in zip(fmt,data)]
        line=self.sep.join(data)
        self.write_line(line,header,add_timestamp=add_timestamp)