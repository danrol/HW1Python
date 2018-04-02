"""
Routines for defining a unified interface across multiple backends.
"""

from ..utils.py3 import anystring
from builtins import range, zip

import time
from ..utils import funcargparse, general, log, net
import contextlib


### Generic backend interface ###

class IDeviceBackend(object):
    """
    An abstract class for a device communication backend.
    
    Connection is automatically opened on creation.
    
    Args:
        conn: Connection parameters (depend on the backend).
        timeout (float): Default timeout (in seconds).
        term_write (str): Line terminator for writing operations.
        term_read (str): Line terminator for reading operations.
    """
    Error=RuntimeError
    """Base class for the errors raised by the backend operations""" 
    
    def __init__(self, conn, timeout=None, term_write=None, term_read=None):
        object.__init__(self)
        self.conn=conn
        self.term_write=term_write
        self.term_read=term_read
    
    def open(self):
        """Open the connection."""
        pass
    def close(self):
        """Close the connection."""
        pass
    
    def lock(self, timeout=None):
        """Lock the access to the device from other threads/processes (isn't necessarily implemented)."""
        pass
    def unlock(self):
        """Unlock the access to the device from other threads/processes (isn't necessarily implemented)."""
        pass
    def locking(self, timeout=None):
        """Context manager for lock & unlock."""
        return general.DummyResource()
    
    def cooldown(self):
        """Cooldown between the operations (usually, some short time delay)."""
        pass
    
    def set_timeout(self, timeout):
        """Set operations timeout (in seconds)."""
        pass
    def get_timeout(self):
        """Get operations timeout (in seconds)."""
        return None
    
    @contextlib.contextmanager
    def using_timeout(self, timeout=None):
        """Context manager for usage of a different timeout inside a block."""
        if timeout is not None:
            to=self.get_timeout()
            self.set_timeout(timeout)
        try:
            yield
        finally:
            if timeout is not None:
                self.set_timeout(to)
    
            
        
    def readline(self, remove_term=True, timeout=None, skip_empty=True):
        """
        Read a single line from the device.
        
        Args:
            remove_term (bool): If ``True``, remove terminal characters from the result.
            timeout: Operation timeout. If ``None``, use the default device timeout.
            skip_empty (bool): If ``True``, ignore empty lines (works only for ``remove_term==True``).
        """
        raise NotImplementedError("IDeviceBackend.readline")
    def readlines(self, lines_num, remove_term=True, timeout=None, skip_empty=True):
        """
        Read multiple lines from the device.
        
        Parameters are the same as in :func:`readline`.
        """
        return [self.readline(remove_term=remove_term,timeout=timeout,skip_empty=skip_empty) for _ in range(lines_num)]
    def read(self, size=None):
        """
        Read data from the device.
        
        If `size` is not None, read `size` bytes (the standard timeout applies); otherwise, read all available data (return immediately).
        """
        raise NotImplementedError("IDeviceBackend.read")
    def flush_read(self):
        """Flush the device output (read all the available data; return the number of bytes read)."""
        return len(self.read())
    def write(self, data, flush=True, read_echo=False, read_echo_delay=0, read_echo_lines=1):
        """
        Write data to the device.
        
        If ``flush==True``, flush the write buffer.
        If ``read_echo==True``, wait for `read_echo_delay` seconds and then perform :func:`readline` (`read_echo_lines` times).
        """
        raise NotImplementedError("IDeviceBackend.write")
    def ask(self, query, delay=0., read_all=False):
        """
        Perform a write followed by a read, with `delay` in between.
        
        If ``read_all==True``, read all the available data; otherwise, read a single line.
        """
        self.write(query)
        if delay:
            time.sleep(delay)
        if read_all:
            return self.read()
        else:
            return self.readline()



### Helper functions ###

def remove_longest_term(msg, terms):
    """
    Remove the longest terminator among `terms` from the end of the message.
    """
    tcs=0
    for t in terms:
        if msg.endswith(t):
            tcs=max(tcs,len(t))
    return msg[:-tcs]
    


### Specific backends ###

_backends={}

class IBackendOpenError(RuntimeError):
    pass

try:
    import visa
    class VisaDeviceBackend(IDeviceBackend):
        """
        NIVisa backend (via pyVISA).
        
        Connection is automatically opened on creation.
        
        Args:
            conn (str): Connection string.
            timeout (float): Default timeout (in seconds).
            term_write (str): Line terminator for writing operations; appended to the data
            term_read (str): Line terminator for reading operations (specifies when :func:`readline` stops).
            do_lock (bool): If ``True``, employ locking operations; otherwise, locking function does nothing.
        """
        _default_operation_cooldown=0.03
        _backend="visa"
        Error=visa.VisaIOError
        """Base class for the errors raised by the backend operations""" 
        class BackendOpenError(visa.VisaIOError,IBackendOpenError):
            """Visa backend opening error"""
            def __init__(self, e):
                IBackendOpenError.__init__(self)
                visa.VisaIOError.__init__(self,*e.args)
        
        if visa.__version__<"1.6": # older pyvisa versions have a slightly different interface
            def _set_timeout(self, timeout):
                self.instr.timeout=timeout
            def _get_timeout(self):
                return self.instr.timeout
            def _open_resource(self, conn):
                if self.term_read is None:
                    term_read='\n'
                if self.term_write is None:
                    term_write='\n'
                if not term_write.endswith(term_read):
                    raise NotImplementedError("PyVisa version <1.6 doesn't support different terminators for reading and writing")
                instr=visa.instrument(conn)
                instr.term_chars=self.term_read
                self.term_write=self.term_write[:len(self.term_write)-len(self.term_read)]
                return instr
            _lock_default=False
            def _lock(self, timeout=None):
                raise NotImplementedError("PyVisa version <1.6 doesn't support locking")
            def _unlock(self):
                raise NotImplementedError("PyVisa version <1.6 doesn't support locking")
            def _lock_context(self, timeout=None):
                raise NotImplementedError("PyVisa version <1.6 doesn't support locking")
        else:
            def _set_timeout(self, timeout):
                self.instr.timeout=timeout*1000. # in newer versions timeout is in ms
            def _get_timeout(self):
                return self.instr.timeout/1000. # in newer versions timeout is in ms
            def _open_resource(self, conn):
                instr=visa.ResourceManager().open_resource(conn)
                instr.read_termination=self.term_read
                instr.write_termination=self.term_write
                self.term_read=self.term_write=""
                return instr
            _lock_default=False ## TODO: figure out GPIB locking issue 
            def _lock(self, timeout=None):
                self.instr.lock(timeout=timeout*1000. if timeout is not None else None)
            def _unlock(self):
                self.instr.unlock()
            def _lock_context(self, timeout=None):
                return self.instr.lock_context(timeout=timeout*1000. if timeout is not None else None)
            
        
        def __init__(self, conn, timeout=10., term_write=None, term_read=None, do_lock=None):
            IDeviceBackend.__init__(self,conn,term_write=term_write,term_read=term_read)
            try:
                self.instr=self._open_resource(self.conn)
                self._operation_cooldown=self._default_operation_cooldown
                self._do_lock=do_lock if do_lock is not None else self._lock_default
                self.cooldown()
                self.set_timeout(timeout)
            except self.Error as e:
                raise self.BackendOpenError(e)
            
        def open(self):
            """Open the connection."""
            self.instr.open()
            self.cooldown()
        def close(self):
            """Close the connection."""
            self.instr.close()
            self.cooldown()

        def lock(self, timeout=None):
            """Lock the access to the device from other threads/processes."""
            if self._do_lock:
                self.lock(timeout=timeout)
        def unlock(self):
            """Unlock the access to the device from other threads/processes."""
            if self._do_lock:
                self.unlock()
        def locking(self, timeout=None):
            """Context manager for lock & unlock."""
            if self._do_lock:
                return self._lock_context(timeout=timeout)
            else:
                return general.DummyResource()
        
        def cooldown(self):
            """
            Cooldown between the operations.
            
            Sleeping for a short time defined by `_operation_cooldown` attribute (30 ms by default).
            Also can be defined class-wide by `_default_operation_cooldown` class attribute.
            """
            if self._operation_cooldown>0:
                time.sleep(self._operation_cooldown)
        
        def set_timeout(self, timeout):
            """Set operations timeout (in seconds)."""
            if timeout is not None:
                self._set_timeout(timeout)
                self.cooldown()
        def get_timeout(self):
            """Get operations timeout (in seconds)."""
            return self._get_timeout()            
        
        def readline(self, remove_term=True, timeout=None, skip_empty=True):
            """
            Read a single line from the device.
            
            Args:
                remove_term (bool): If ``True``, remove terminal characters from the result.
                timeout: Operation timeout. If ``None``, use the default device timeout.
                skip_empty (bool): If ``True``, ignore empty lines (works only for ``remove_term==True``).
            """
            with self.using_timeout(timeout):
                if remove_term:
                    while True:
                        result=self.instr.read()
                        if (not skip_empty) or result:
                            break
                else:
                    result=self.instr.read_raw()
            self.cooldown()
            return result
        def read(self, size=None):
            """
            Read data from the device.
            
            If `size` is not None, read `size` bytes (the standard timeout applies); otherwise, read all available data (return immediately).
            """
            if size is None:
                with self.using_timeout(0):
                    return self.instr.read_raw(size=size)
            result=self.instr.read_raw(size=size)
            self.cooldown()
            return result
        
        def write(self, data, flush=True, read_echo=False, read_echo_delay=0, read_echo_lines=1):
            """
            Write data to the device.
            
            If ``flush==True``, flush the write buffer.
            If ``read_echo==True``, wait for `read_echo_delay` seconds and then perform :func:`readline` (`read_echo_lines` times).
            """
            if self.term_write:
                data=data+self.term_write
            self.instr.write(data)
            self.cooldown()
            if read_echo_delay>0.:
                time.sleep(read_echo_delay)
            if read_echo:
                for _ in range(read_echo_lines):
                    self.readline()
                    self.cooldown()

        def __repr__(self):
            return "VisaDeviceBackend("+self.instr.__repr__()+")"
                
                
    _backends["visa"]=VisaDeviceBackend
except ImportError:
    pass
    


try:
    import serial

    class SerialDeviceBackend(IDeviceBackend):
        """
        Serial backend (via pySerial).
        
        Connection is automatically opened on creation.
        
        Args:
            conn: Connection parameters. Can be either a string (for a port),
                or a list/tuple ``(port, baudrate, bytesize, parity, stopbits, xonxoff, rtscts, dsrdtr)`` supplied to the serial connection
                (default is ``('COM1',19200,8,'N',1,0,0,0)``),
                or a dict with the same paramters. 
            timeout (float): Default timeout (in seconds).
            term_write (str): Line terminator for writing operations; appended to the data
            term_read (str): List of possible single-char terminator for reading operations (specifies when :func:`readline` stops).
            connect_on_operation (bool): If ``True``, the connection is normally closed, and is opened only on the operations
                (normally two processes can't be simultaneously connected to the same device). 
            open_retry_times (int): Number of times the connection is attempted before giving up.
            no_dtr (bool): If ``True``, turn off DTR status line before opening (e.g., turns off reset-on-connection for Arduino controllers).
        """
        _default_operation_cooldown=0.0
        _backend="serial"
        Error=serial.SerialException
        """Base class for the errors raised by the backend operations"""
        class BackendOpenError(serial.SerialException,IBackendOpenError):
            """Serial backend opening error"""
            def __init__(self, e):
                IBackendOpenError.__init__(self)
                serial.SerialException.__init__(self,*e.args)
        
        _conn_params=["port","baudrate","bytesize","parity","stopbits","xonxoff","rtscts","dsrdtr"]
        _default_conn=["COM1",19200,8,"N",1,0,0,0]
    
        @classmethod
        def _conn_to_dict(cls, conn):
            if isinstance(conn, dict):
                return conn
            if isinstance(conn, (tuple,list)):
                return dict(zip(cls._conn_params,conn))
            return {"port":conn}
        @classmethod
        def combine_serial_conn(cls, conn1, conn2):
            conn=cls._conn_to_dict(conn2).copy()
            conn.update(cls._conn_to_dict(conn1))
            return conn

        def __init__(self, conn, timeout=10., term_write=None, term_read=None, connect_on_operation=False, open_retry_times=3, no_dtr=False):
            conn_dict=self.combine_serial_conn(conn,self._default_conn)
            if term_write is None:
                term_write="\r\n"
            if term_read is None:
                term_read="\n"
            if isinstance(term_read,anystring):
                term_read=[term_read]
            IDeviceBackend.__init__(self,conn_dict.copy(),term_write=term_write,term_read=term_read)
            port=conn_dict.pop("port")
            try:
                self.instr=serial.serial_for_url(port,do_not_open=True,**conn_dict)
                if no_dtr:
                    try:
                        self.instr.setDTR(0)
                    except self.Error:
                        log.default_log.debug("Cannot set DTR for an unconnected device",origin="backends/serial",level="misc")
                if not connect_on_operation:
                    self.instr.open()
                self._operation_cooldown=self._default_operation_cooldown
                self._connect_on_operation=connect_on_operation
                self._opened_stack=0
                self._open_retry_times=open_retry_times
                self.cooldown()
                self.set_timeout(timeout)
            except self.Error as e:
                raise self.BackendOpenError(e)
            
        def _do_open(self):
            general.retry_wait(self.instr.open, self._open_retry_times, 0.3)
        def _do_close(self):
            #general.retry_wait(self.instr.flush, self._open_retry_times, 0.3)
            general.retry_wait(self.instr.close, self._open_retry_times, 0.3)
        def open(self):
            """Open the connection."""
            if not self._connect_on_operation:
                self._do_open()
        def close(self):
            """Close the connection."""
            if not self._connect_on_operation:
                self._do_close()
        def _op_open(self):
            if self._connect_on_operation:
                if not self._opened_stack:
                    self._do_open()
                self._opened_stack=self._opened_stack+1
        def _op_close(self):
            if self._connect_on_operation:
                self._opened_stack=self._opened_stack-1
                if not self._opened_stack:
                    self._do_close()
        @contextlib.contextmanager
        def single_op(self):
            """
            Context manager for a single operation.
            
            If ``connect_on_operation==True`` during creation, wrapping several command in `single_op`
            prevents the connection from being closed and reopened between the operations (only opened in the beginning and closed in the end).
            """
            self._op_open()
            try:
                yield
            finally:
                self._op_close()
            
        
        def cooldown(self):
            """
            Cooldown between the operations.
            
            Sleeping for a short time defined by `_operation_cooldown` attribute (no cooldown by default).
            Also defined class-wide by `_default_operation_cooldown` class attribute.
            """
            if self._operation_cooldown>0:
                time.sleep(self._operation_cooldown)
            
        def set_timeout(self, timeout):
            """Set operations timeout (in seconds)."""
            if timeout is not None:
                self.instr.timeout=timeout
                self.cooldown()
        def get_timeout(self):
            """Get operations timeout (in seconds)."""
            return self.instr.timeout
        
        
        def _read_terms(self, terms="", timeout=None, error_on_timeout=True):
            result=""
            singlechar_terms=all(len(t)==1 for t in terms)
            with self.single_op():
                with self.using_timeout(timeout):
                    while True:
                        c=self.instr.read(1 if terms else 8)
                        result=result+c
                        if c=="":
                            if error_on_timeout and terms:
                                raise self.Error()
                            return result
                        if singlechar_terms:
                            if c in terms:
                                return result
                        else:
                            for t in terms:
                                if result.endswith(t):
                                    return result
        def readline(self, remove_term=True, timeout=None, skip_empty=True, error_on_timeout=True):
            """
            Read a single line from the device.
            
            Args:
                remove_term (bool): If ``True``, remove terminal characters from the result.
                timeout: Operation timeout. If ``None``, use the default device timeout.
                skip_empty (bool): If ``True``, ignore empty lines (works only for ``remove_term==True``).
                error_on_timeout (bool): If ``False``, return an incomplete line instead of raising the error on timeout.
            """
            while True:
                result=self._read_terms(self.term_read or "",timeout=timeout,error_on_timeout=error_on_timeout)
                self.cooldown()
                if remove_term and self.term_read:
                    result=remove_longest_term(result,self.term_read)
                if not (skip_empty and remove_term and (not result)):
                    break
            return result
        def read(self, size=None, error_on_timeout=True):
            """
            Read data from the device.
            
            If `size` is not None, read `size` bytes (usual timeout applies); otherwise, read all available data (return immediately).
            """
            with self.single_op():
                if size is None:
                    result=self._read_terms(timeout=0,error_on_timeout=error_on_timeout)
                else:
                    result=self.instr.read(size=size)
                    if len(result)!=size:
                        raise self.Error()
                self.cooldown()
                return result
        def read_multichar_term(self, term, remove_term=True, timeout=None, error_on_timeout=True):
            """
            Read a single line with multiple possible terminators.
            
            Args:
                term: Either a string (single multi-char terminator) or a list of strings (multiple terminators).
                remove_term (bool): If ``True``, remove terminal characters from the result.
                timeout: Operation timeout. If ``None``, use the default device timeout.
                error_on_timeout (bool): If ``False``, return an incomplete line instead of raising the error on timeout.
            """
            if isinstance(term,anystring):
                term=[term]
            result=self._read_terms(term,timeout=timeout,error_on_timeout=error_on_timeout)
            self.cooldown()
            if remove_term and term:
                result=remove_longest_term(result,term)
            return result
        def write(self, data, flush=True, read_echo=False, read_echo_delay=0, read_echo_lines=1):
            """
            Write data to the device.
            
            If ``flush==True``, flush the write buffer.
            If ``read_echo==True``, wait for `read_echo_delay` seconds and then perform :func:`readline` (`read_echo_lines` times).
            """
            with self.single_op():
                if self.term_write:
                    data=data+self.term_write
                self.instr.write(data)
                self.cooldown()
                if flush:
                    self.instr.flush()
                    self.cooldown()
                if read_echo_delay>0.:
                    time.sleep(read_echo_delay)
                if read_echo:
                    for _ in range(read_echo_lines):
                        self.readline()
                        self.cooldown()

        def __repr__(self):
            return "SerialDeviceBackend("+self.instr.__repr__()+")"
        
        
    _backends["serial"]=SerialDeviceBackend
except ImportError:
    pass




try:
    import ft232

    class FT232DeviceBackend(IDeviceBackend):
        """
        FT232 backend (via pyft232).
        
        Connection is automatically opened on creation.
        
        Args:
            conn: Connection parameters. Can be either a string (for a port),
                or a list/tuple ``(port, baudrate, bytesize, parity, stopbits, xonxoff, rtscts, dsrdtr)`` supplied to the serial connection
                (default is ``('COM1',19200,8,'N',1,0,0,0)``),
                or a dict with the same paramters. 
            timeout (float): Default timeout (in seconds).
            term_write (str): Line terminator for writing operations; appended to the data
            term_read (str): List of possible single-char terminator for reading operations (specifies when :func:`readline` stops).
            connect_on_operation (bool): If ``True``, the connection is normally closed, and is opened only on the operations
                (normally two processes can't be simultaneously connected to the same device). 
            open_retry_times (int): Number of times the connection is attempted before giving up.
            no_dtr (bool): If ``True``, turn off DTR status line before opening (e.g., turns off reset-on-connection for Arduino controllers).
        """
        _default_operation_cooldown=0.0
        _backend="ft232"
        Error=ft232.Ft232Exception
        """Base class for the errors raised by the backend operations"""
        class BackendOpenError(ft232.Ft232Exception,IBackendOpenError):
            """FT232 backend opening error"""
            def __init__(self, e):
                IBackendOpenError.__init__(self)
                ft232.Ft232Exception.__init__(self,*e.args)
        
        _conn_params=["port","baudrate","bytesize","parity","stopbits","xonxoff","rtscts"]
        _default_conn=[None,9600,8,"N",1,0,0]
    
        @classmethod
        def _conn_to_dict(cls, conn):
            if isinstance(conn, dict):
                return conn
            if isinstance(conn, (tuple,list)):
                return dict(zip(cls._conn_params,conn))
            return {"port":conn}
        @classmethod
        def combine_serial_conn(cls, conn1, conn2):
            conn=cls._conn_to_dict(conn2).copy()
            conn.update(cls._conn_to_dict(conn1))
            return conn

        def __init__(self, conn, timeout=10., term_write=None, term_read=None, open_retry_times=3):
            conn_dict=self.combine_serial_conn(conn,self._default_conn)
            if term_write is None:
                term_write="\r\n"
            if term_read is None:
                term_read="\n"
            if isinstance(term_read,anystring):
                term_read=[term_read]
            IDeviceBackend.__init__(self,conn_dict.copy(),term_write=term_write,term_read=term_read)
            port=conn_dict.pop("port")
            try:
                self.instr=ft232.Ft232(port,**conn_dict)
                self._operation_cooldown=self._default_operation_cooldown
                self._opened_stack=0
                self._open_retry_times=open_retry_times
                self.cooldown()
                self.set_timeout(timeout)
            except self.Error as e:
                raise self.BackendOpenError(e)
            
        def _do_open(self):
            general.retry_wait(self.instr.open, self._open_retry_times, 0.3)
        def _do_close(self):
            #general.retry_wait(self.instr.flush, self._open_retry_times, 0.3)
            general.retry_wait(self.instr.close, self._open_retry_times, 0.3)
        def open(self):
            """Open the connection."""
            self._do_open()
        def close(self):
            """Close the connection."""
            self._do_close()
        @contextlib.contextmanager
        def single_op(self):
            """
            Context manager for a single operation.
            
            Does nothing.
            """
            yield
            
        
        def cooldown(self):
            """
            Cooldown between the operations.
            
            Sleeping for a short time defined by `_operation_cooldown` attribute (no cooldown by default).
            Also defined class-wide by `_default_operation_cooldown` class attribute.
            """
            if self._operation_cooldown>0:
                time.sleep(self._operation_cooldown)
            
        def set_timeout(self, timeout):
            """Set operations timeout (in seconds)."""
            if timeout is not None:
                if timeout<1E-3:
                    timeout=1E-3 # 0 is infinite timeout
                self.instr.timeout=timeout
                self.cooldown()
        def get_timeout(self):
            """Get operations timeout (in seconds)."""
            return self.instr.timeout
        
        
        def _read_terms(self, terms="", timeout=None, error_on_timeout=True):
            result=""
            singlechar_terms=all(len(t)==1 for t in terms)
            with self.single_op():
                with self.using_timeout(timeout):
                    while True:
                        c=self.instr.read(1 if terms else 8)
                        result=result+c
                        if c=="":
                            if error_on_timeout and terms:
                                raise self.Error(4)
                            return result
                        if singlechar_terms:
                            if c in terms:
                                return result
                        else:
                            for t in terms:
                                if result.endswith(t):
                                    return result
        def readline(self, remove_term=True, timeout=None, skip_empty=True, error_on_timeout=True):
            """
            Read a single line from the device.
            
            Args:
                remove_term (bool): If ``True``, remove terminal characters from the result.
                timeout: Operation timeout. If ``None``, use the default device timeout.
                skip_empty (bool): If ``True``, ignore empty lines (works only for ``remove_term==True``).
                error_on_timeout (bool): If ``False``, return an incomplete line instead of raising the error on timeout.
            """
            while True:
                result=self._read_terms(self.term_read or "",timeout=timeout,error_on_timeout=error_on_timeout)
                self.cooldown()
                if remove_term and self.term_read:
                    result=remove_longest_term(result,self.term_read)
                if not (skip_empty and remove_term and (not result)):
                    break
            return result
        def read(self, size=None, error_on_timeout=True):
            """
            Read data from the device.
            
            If `size` is not None, read `size` bytes (usual timeout applies); otherwise, read all available data (return immediately).
            """
            with self.single_op():
                if size is None:
                    result=self._read_terms(timeout=0,error_on_timeout=error_on_timeout)
                else:
                    result=self.instr.read(size=size)
                    if len(result)!=size:
                        raise self.Error(4)
                self.cooldown()
                return result
        def read_multichar_term(self, term, remove_term=True, timeout=None, error_on_timeout=True):
            """
            Read a single line with multiple possible terminators.
            
            Args:
                term: Either a string (single multi-char terminator) or a list of strings (multiple terminators).
                remove_term (bool): If ``True``, remove terminal characters from the result.
                timeout: Operation timeout. If ``None``, use the default device timeout.
                error_on_timeout (bool): If ``False``, return an incomplete line instead of raising the error on timeout.
            """
            if isinstance(term,anystring):
                term=[term]
            result=self._read_terms(term,timeout=timeout,error_on_timeout=error_on_timeout)
            self.cooldown()
            if remove_term and term:
                result=remove_longest_term(result,term)
            return result
        def write(self, data, flush=True, read_echo=False, read_echo_delay=0, read_echo_lines=1):
            """
            Write data to the device.
            
            If ``flush==True``, flush the write buffer.
            If ``read_echo==True``, wait for `read_echo_delay` seconds and then perform :func:`readline` (`read_echo_lines` times).
            """
            with self.single_op():
                if self.term_write:
                    data=data+self.term_write
                self.instr.write(data)
                self.cooldown()
                if flush:
                    self.instr.flush()
                    self.cooldown()
                if read_echo_delay>0.:
                    time.sleep(read_echo_delay)
                if read_echo:
                    for _ in range(read_echo_lines):
                        self.readline()
                        self.cooldown()

        def __repr__(self):
            return "FT232DeviceBackend("+self.instr.__repr__()+")"
        
        
    _backends["ft232"]=FT232DeviceBackend
except ImportError:
    pass




class NetworkDeviceBackend(IDeviceBackend):
    """
    Serial backend (via pySerial).
    
    Connection is automatically opened on creation.
    
    Args:
        conn: Connection parameters. Can be either a string (for a port),
            or a list/tuple ``(port, baudrate, bytesize, parity, stopbits, xonxoff, rtscts, dsrdtr)`` supplied to the serial connection
            (default is ``('COM1',19200,8,'N',1,0,0,0)``),
            or a dict with the same paramters. 
        timeout (float): Default timeout (in seconds).
        term_write (str): Line terminator for writing operations; appended to the data
        term_read (str): List of possible single-char terminator for reading operations (specifies when :func:`readline` stops).
        open_retry_times (int): Number of times the connection is attempted before giving up.
        
    Note:
        If `term_read` is a string, its behavior is different from the VISA backend:
        instead of being a multi-char terminator it is assumed to be a set of single-char terminators.
        If multi-char terminator is required, `term_read` should be a single-element list instead of a string.
    """
    _default_operation_cooldown=0.0
    _backend="network"
    Error=net.socket.error
    """Base class for the errors raised by the backend operations"""
    class BackendOpenError(net.socket.error,IBackendOpenError):
        """Network backend opening error"""
        def __init__(self, e):
            IBackendOpenError.__init__(self)
            net.socket.error.__init__(self,*e.args)

    def __init__(self, conn, timeout=10., term_write=None, term_read=None):
        if term_write is None:
            term_write="\r\n"
        if term_read is None:
            term_read="\r\n"
        if isinstance(term_read,anystring):
            term_read=[term_read]
        IDeviceBackend.__init__(self,conn,term_write=term_write,term_read=term_read)
        try:
            self.open()
            self._operation_cooldown=self._default_operation_cooldown
            self.cooldown()
            self.set_timeout(timeout)
        except self.Error as e:
            raise self.BackendOpenError(e)
    
    @staticmethod
    def _get_addr_port(conn):
        conn=conn.split(":")
        if len(conn)!=2:
            raise ValueError("invalid device address: {}".format(conn))
        return conn[0],int(conn[1])
    def open(self):
        """Open the connection."""
        self.socket=net.ClientSocket(send_method="fixedlen",recv_method="fixedlen")
        self.socket.connect(self._get_addr_port(self.conn))
    def close(self):
        """Close the connection."""
        self.socket.close()
        
    def cooldown(self):
        """
        Cooldown between the operations.
        
        Sleeping for a short time defined by `_operation_cooldown` attribute (no cooldown by default).
        Also defined class-wide by `_default_operation_cooldown` class attribute.
        """
        if self._operation_cooldown>0:
            time.sleep(self._operation_cooldown)
        
    def set_timeout(self, timeout):
        """Set operations timeout (in seconds)."""
        self.socket.set_timeout(timeout)
    def get_timeout(self):
        """Get operations timeout (in seconds)."""
        return self.socket.get_timeout()
    
    
    def readline(self, remove_term=True, timeout=None, skip_empty=True, error_on_timeout=True):
        """
        Read a single line from the device.
        
        Args:
            remove_term (bool): If ``True``, remove terminal characters from the result.
            timeout: Operation timeout. If ``None``, use the default device timeout.
            skip_empty (bool): If ``True``, ignore empty lines (works only for ``remove_term==True``).
            error_on_timeout (bool): If ``False``, return an incomplete line instead of raising the error on timeout.
        """
        while True:
            try:
                with self.using_timeout(timeout):
                    result=self.socket.recv_delimiter(self.term_read,strict=True)
            except net.SocketTimeout:
                if error_on_timeout:
                    raise
            self.cooldown()
            if remove_term and self.term_read:
                result=remove_longest_term(result,self.term_read)
            if not (skip_empty and remove_term and (not result)):
                break
        return result
    def read(self, size=None, error_on_timeout=True):
        """
        Read data from the device.
        
        If `size` is not None, read `size` bytes (usual timeout applies); otherwise, read all available data (return immediately).
        """
        if size is None:
            try:
                data=b""
                with self.using_timeout(0):
                    while True:
                        new_data=self.socket.recv_fixedlen(1024)
                        if not new_data:
                            break
                        data=data+new_data
            except net.SocketTimeout:
                pass
        else:
            try:
                data=self.socket.recv_fixedlen(size)
            except net.SocketTimeout:
                if error_on_timeout:
                    raise
        return data
    def read_multichar_term(self, term, remove_term=True, timeout=None, error_on_timeout=True):
        """
        Read a single line with multiple possible terminators.
        
        Args:
            term: Either a string (single multi-char terminator) or a list of strings (multiple terminators).
            remove_term (bool): If ``True``, remove terminal characters from the result.
            timeout: Operation timeout. If ``None``, use the default device timeout.
            error_on_timeout (bool): If ``False``, return an incomplete line instead of raising the error on timeout.
        """
        if isinstance(term,anystring):
                term=[term]
        result=self.socket.recv_delimiter(term,strict=True)
        self.cooldown()
        if remove_term and term:
            result=remove_longest_term(result,term)
        return result
    def write(self, data, flush=True, read_echo=False, read_echo_delay=0, read_echo_lines=1):
        """
        Write data to the device.
        
        If ``read_echo==True``, wait for `read_echo_delay` seconds and then perform :func:`readline` (`read_echo_lines` times).
        `flush` parameter is ignored.
        """
        self.socket.send_delimiter(data,self.term_write)
        self.instr.write(data)
        self.cooldown()
        if read_echo_delay>0.:
            time.sleep(read_echo_delay)
        if read_echo:
            for _ in range(read_echo_lines):
                self.readline()
                self.cooldown()

    def __repr__(self):
        return "NetworkDeviceBackend("+self.instr.__repr__()+")"
    
    
_backends["network"]=NetworkDeviceBackend
    
    
    
    


    
def new_backend(conn, timeout=None, backend="visa", **kwargs):
    """
    Build new backend with the supplied parameters.
    
    Args:
        conn: Connection parameters (depend on the backend).
        timeout (float): Default timeout (in seconds).
        backend (str): Backend type. Available backends are ``'visa'`` and ``'serial'``. 
    """
    if isinstance(conn,IDeviceBackend):
        return conn
    funcargparse.check_parameter_range(backend,"backend",_backends)
    return _backends[backend](conn,timeout=timeout,**kwargs)






### Interface for a generic device class ###

class IBackendWrapper(object):
    """
    A base class for an instrument.
    
    Contains some useful functions for dealing with device settings.
    
    Args:
        instr: Backend (assumed to be already opened).
    """
    def __init__(self, instr):
        object.__init__(self)
        self.instr=instr
        self._settings_nodes={}
        self._settings_nodes_order=[]
        
    def open(self):
        """Open the backend."""
        return self.instr.open()
    def close(self):
        """Close the backend."""
        return self.instr.close()
    def __enter__(self):
        return self
    def __exit__(self, *args, **vargs):
        self.close()
        return False
    
    def lock(self, timeout=None):
        """Lock the access to the device from other threads/processes (isn't necessarily implemented)."""
        return self.instr.lock(timeout=timeout)
    def unlock(self):
        """Unlock the access to the device from other threads/processes (isn't necessarily implemented)."""
        return self.instr.unlock()
    def locking(self, timeout=None):
        """Context manager for lock & unlock."""
        return self.instr.locking(timeout=timeout)
    
    
    def _add_settings_node(self, path, getter=None, setter=None):
        """
        Adds a settings parameter
        
        `getter`/`setter` are methods for getting/setting this parameter.
        Can be ``None``, meaning that this parameter is ingored when executing :func:`get_settings`/:func:`apply_settings`.
        """
        self._settings_nodes[path]=(getter,setter)
        self._settings_nodes_order.append(path)
    def get_settings(self):
        """Get dict ``{name: value}`` containing all the device settings."""
        settings={}
        for k in self._settings_nodes_order:
            g,_=self._settings_nodes[k]
            if g:
                settings[k]=g()
        return settings
    def apply_settings(self, settings):
        """
        Apply the settings.
        
        `settings` is the dict ``{name: value}`` of the device available settings.
        Non-applicable settings are ignored.
        """
        for k in self._settings_nodes_order:
            _,s=self._settings_nodes[k]
            if s and (k in settings):
                s(settings[k])
    def __getitem__(self, key):
        """Get the value of a settings parameter."""
        if key in self._settings_nodes:
            g=self._settings_nodes[key][0]
            if g:
                return g()
            raise ValueError("no getter for value '{}'".format(key))
        raise KeyError("no property '{}'".format(key))
    def __setitem__(self, key, value):
        """Set the value of a settings parameter."""
        if key in self._settings_nodes:
            s=self._settings_nodes[key][1]
            if s:
                return s(value)
            raise ValueError("no setter for value '{}'".format(key))
        raise KeyError("no property '{}'".format(key))