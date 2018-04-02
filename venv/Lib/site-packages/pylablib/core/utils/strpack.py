"""
Utilities for packing values into bitstrings.
Small extension of the struct module.
"""

from builtins import range, bytes

import struct
from . import funcargparse


struct_descriptors={("i",1):"b",("i",2):"h",("i",4):"i",("i",8):"q",
                 ("u",1):"B",("u",2):"H",("u",4):"I",("u",8):"Q",
                 ("f",4):"f",("f",8):"d"}

def int2bytes(val, l, bo=">"):
    """
    Convert integer into a list of bytes of length `l`.
    
    `bo` determines byte order: ``'>'`` is big-endian (MSB first), ``'<'`` is little-endian (LSB first).
    """
    funcargparse.check_parameter_range(bo,"bo","<>")
    bs=[(val>>(n*8))&0xFF for n in range(l)]
    return bs if bo=="<" else bs[::-1]
def bytes2int(val, bo=">"):
    """
    Convert a list of bytes into an integer.
    
    `bo` determines byte order: ``'>'`` is big-endian (MSB first), ``'<'`` is little-endian (LSB first).
    """
    funcargparse.check_parameter_range(bo,"bo","<>")
    if bo=="<":
        bo=bo[::-1]
    return sum([(b<<(n*8)) for n,b in enumerate(val)])

def int2bits(val, l, bo=">"):
    """
    Convert integer into a list of bits of length `l`.
    
    `bo` determines byte (and bit) order: ``'>'`` is big-endian (MSB first), ``'<'`` is little-endian (LSB first).
    """
    funcargparse.check_parameter_range(bo,"bo","<>")
    bs=[bool((val>>n)&0x01) for n in range(l)]
    return bs if bo=="<" else bs[::-1]
def bits2int(val, bo=">"):
    """
    Convert a list of bits into an integer.
    
    `bo` determines byte (and bit) order: ``'>'`` is big-endian (MSB first), ``'<'`` is little-endian (LSB first).
    """
    funcargparse.check_parameter_range(bo,"bo","<>")
    if bo=="<":
        bo=bo[::-1]
    return sum([(int(b)<<n) for n,b in enumerate(val)])


def pack_uint(val, l, bo=">"):
    """
    Convert unsigned integer into a bytestring of length `l`.
    
    Return ``bytes`` object in Py3 and ``builtins.bytes`` object in Py2.
    `bo` determines byte order: ``'>'`` is big-endian (MSB first), ``'<'`` is little-endian (LSB first).
    """
    fmt="u",l
    if fmt in struct_descriptors:
        fmt=bo+struct_descriptors[fmt]
        return struct.pack(fmt,val)
    bs=int2bytes(val,l,bo)
    return bytes(bs)
def unpack_uint(msg, bo=">"):
    """
    Convert a bytestring into an unsigned integer.
    
    `bo` determines byte order: ``'>'`` is big-endian (MSB first), ``'<'`` is little-endian (LSB first).
    """
    fmt="u",len(msg)
    if fmt in struct_descriptors:
        fmt=bo+struct_descriptors[fmt]
        return struct.unpack(fmt,msg)[0]
    return bytes2int(bytes(msg),bo)