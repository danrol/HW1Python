from builtins import bytes as new_bytes

textstring=(basestring,) if (str is bytes) else (str,)
bytestring=(str,new_bytes) if (str is bytes) else (bytes,)
anystring=(str, unicode) if (str is bytes) else (str,bytes)