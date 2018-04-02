"""
File parsing errors.
"""


class Error(Exception):
    """
    Error baseclass.
    """
    pass

class WrongRowSize(Error):
    """
    Wrong row size error.
    
    Args:
        message (str): Error message.
        expected (int): Expected row size.
        found (int): Actual row size.
    """
    def __init__(self, message, expected, found):
        self.message=message
        self.expected=expected
        self.found=found
    def __str__(self):
        return str(self.message)+": expected "+str(self.expected)+" entries, found "+str(self.found)+" entries"

class WrongColumnSize(Error):
    """
    Wrong columns size error.
    
    Args:
        message (str): Error message.
        expected (int): Expected columns size.
        found (int): Actual columns size.
    """
    def __init__(self, message, expected, found):
        self.message=message
        self.expected=expected
        self.found=found
    def __str__(self):
        return str(self.message)+": expected "+str(self.expected)+" entries, found "+str(self.found)+" entries"

class WrongFileFormat(Error):
    """
    Wrong file format error.
    
    Args:
        message (str): Error message.
        file_format (str): Expected file format.
    """
    def __init__(self, message, file_format=""):
        self.message=message
        self.file_format=file_format
    def __str__(self):
        if self.file_format:
            return "file structure doesn't correspond to format '{0}': {1}".format(self.file_format,self.message)
        else:
            return "file structure doesn't correspond to expected format: {0}".format(self.message)

class InsufficientBinaryFileDescription(Error):
    """
    Incufficient binary file description error.
    """
    def __init__(self):
        pass
    def __str__(self):
        return "insufficient binary file description"