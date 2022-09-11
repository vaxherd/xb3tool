#!/usr/bin/python3
#
# Generate a minimap image for a Xenoblade 3 map.
#
# Requires PIL (the Python Imaging Library).

import argparse
from collections import namedtuple
import os
import struct
import sys

import PIL.Image


########################################################################
# Utility functions

def u32(data, offset): return struct.unpack('<I', data[offset:offset+4])[0]
def asciiz(data, offset, size):
    return (struct.unpack(f'{size}s', data[offset:offset+size])[0]
            .split(b'\0', 1)[0].decode('ascii'))


########################################################################
# Image data parsing

BC7Mode = namedtuple('BC7Mode', 'ns pb rb isb cb ab epb spb ib ib2')
BC7_M = (# ns pb rb isb cb ab epb spb ib ib2
    BC7Mode(3, 4, 0,  0, 4, 0,  1,  0, 3,  0),
    BC7Mode(2, 6, 0,  0, 6, 0,  0,  1, 3,  0),
    BC7Mode(3, 6, 0,  0, 5, 0,  0,  0, 2,  0),
    BC7Mode(2, 6, 0,  0, 7, 0,  1,  0, 2,  0),
    BC7Mode(1, 0, 2,  1, 5, 6,  0,  0, 2,  3),
    BC7Mode(1, 0, 2,  0, 7, 8,  0,  0, 2,  2),
    BC7Mode(1, 0, 0,  0, 7, 7,  1,  0, 4,  0),
    BC7Mode(2, 6, 0,  0, 5, 5,  1,  0, 2,  0))
BC7_P1 = ((0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0), )
BC7_P2 = ((0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1),
          (0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1),
          (0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1),
          (0,0,0,1,0,0,1,1,0,0,1,1,0,1,1,1),
          (0,0,0,0,0,0,0,1,0,0,0,1,0,0,1,1),
          (0,0,1,1,0,1,1,1,0,1,1,1,1,1,1,1),
          (0,0,0,1,0,0,1,1,0,1,1,1,1,1,1,1),
          (0,0,0,0,0,0,0,1,0,0,1,1,0,1,1,1),
          (0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,1),
          (0,0,1,1,0,1,1,1,1,1,1,1,1,1,1,1),
          (0,0,0,0,0,0,0,1,0,1,1,1,1,1,1,1),
          (0,0,0,0,0,0,0,0,0,0,0,1,0,1,1,1),
          (0,0,0,1,0,1,1,1,1,1,1,1,1,1,1,1),
          (0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1),
          (0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1),
          (0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1),
          (0,0,0,0,1,0,0,0,1,1,1,0,1,1,1,1),
          (0,1,1,1,0,0,0,1,0,0,0,0,0,0,0,0),
          (0,0,0,0,0,0,0,0,1,0,0,0,1,1,1,0),
          (0,1,1,1,0,0,1,1,0,0,0,1,0,0,0,0),
          (0,0,1,1,0,0,0,1,0,0,0,0,0,0,0,0),
          (0,0,0,0,1,0,0,0,1,1,0,0,1,1,1,0),
          (0,0,0,0,0,0,0,0,1,0,0,0,1,1,0,0),
          (0,1,1,1,0,0,1,1,0,0,1,1,0,0,0,1),
          (0,0,1,1,0,0,0,1,0,0,0,1,0,0,0,0),
          (0,0,0,0,1,0,0,0,1,0,0,0,1,1,0,0),
          (0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0),
          (0,0,1,1,0,1,1,0,0,1,1,0,1,1,0,0),
          (0,0,0,1,0,1,1,1,1,1,1,0,1,0,0,0),
          (0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0),
          (0,1,1,1,0,0,0,1,1,0,0,0,1,1,1,0),
          (0,0,1,1,1,0,0,1,1,0,0,1,1,1,0,0),
          (0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1),
          (0,0,0,0,1,1,1,1,0,0,0,0,1,1,1,1),
          (0,1,0,1,1,0,1,0,0,1,0,1,1,0,1,0),
          (0,0,1,1,0,0,1,1,1,1,0,0,1,1,0,0),
          (0,0,1,1,1,1,0,0,0,0,1,1,1,1,0,0),
          (0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0),
          (0,1,1,0,1,0,0,1,0,1,1,0,1,0,0,1),
          (0,1,0,1,1,0,1,0,1,0,1,0,0,1,0,1),
          (0,1,1,1,0,0,1,1,1,1,0,0,1,1,1,0),
          (0,0,0,1,0,0,1,1,1,1,0,0,1,0,0,0),
          (0,0,1,1,0,0,1,0,0,1,0,0,1,1,0,0),
          (0,0,1,1,1,0,1,1,1,1,0,1,1,1,0,0),
          (0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0),
          (0,0,1,1,1,1,0,0,1,1,0,0,0,0,1,1),
          (0,1,1,0,0,1,1,0,1,0,0,1,1,0,0,1),
          (0,0,0,0,0,1,1,0,0,1,1,0,0,0,0,0),
          (0,1,0,0,1,1,1,0,0,1,0,0,0,0,0,0),
          (0,0,1,0,0,1,1,1,0,0,1,0,0,0,0,0),
          (0,0,0,0,0,0,1,0,0,1,1,1,0,0,1,0),
          (0,0,0,0,0,1,0,0,1,1,1,0,0,1,0,0),
          (0,1,1,0,1,1,0,0,1,0,0,1,0,0,1,1),
          (0,0,1,1,0,1,1,0,1,1,0,0,1,0,0,1),
          (0,1,1,0,0,0,1,1,1,0,0,1,1,1,0,0),
          (0,0,1,1,1,0,0,1,1,1,0,0,0,1,1,0),
          (0,1,1,0,1,1,0,0,1,1,0,0,1,0,0,1),
          (0,1,1,0,0,0,1,1,0,0,1,1,1,0,0,1),
          (0,1,1,1,1,1,1,0,1,0,0,0,0,0,0,1),
          (0,0,0,1,1,0,0,0,1,1,1,0,0,1,1,1),
          (0,0,0,0,1,1,1,1,0,0,1,1,0,0,1,1),
          (0,0,1,1,0,0,1,1,1,1,1,1,0,0,0,0),
          (0,0,1,0,0,0,1,0,1,1,1,0,1,1,1,0),
          (0,1,0,0,0,1,0,0,0,1,1,1,0,1,1,1))
BC7_P3 = ((0,0,1,1,0,0,1,1,0,2,2,1,2,2,2,2),
          (0,0,0,1,0,0,1,1,2,2,1,1,2,2,2,1),
          (0,0,0,0,2,0,0,1,2,2,1,1,2,2,1,1),
          (0,2,2,2,0,0,2,2,0,0,1,1,0,1,1,1),
          (0,0,0,0,0,0,0,0,1,1,2,2,1,1,2,2),
          (0,0,1,1,0,0,1,1,0,0,2,2,0,0,2,2),
          (0,0,2,2,0,0,2,2,1,1,1,1,1,1,1,1),
          (0,0,1,1,0,0,1,1,2,2,1,1,2,2,1,1),
          (0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2),
          (0,0,0,0,1,1,1,1,1,1,1,1,2,2,2,2),
          (0,0,0,0,1,1,1,1,2,2,2,2,2,2,2,2),
          (0,0,1,2,0,0,1,2,0,0,1,2,0,0,1,2),
          (0,1,1,2,0,1,1,2,0,1,1,2,0,1,1,2),
          (0,1,2,2,0,1,2,2,0,1,2,2,0,1,2,2),
          (0,0,1,1,0,1,1,2,1,1,2,2,1,2,2,2),
          (0,0,1,1,2,0,0,1,2,2,0,0,2,2,2,0),
          (0,0,0,1,0,0,1,1,0,1,1,2,1,1,2,2),
          (0,1,1,1,0,0,1,1,2,0,0,1,2,2,0,0),
          (0,0,0,0,1,1,2,2,1,1,2,2,1,1,2,2),
          (0,0,2,2,0,0,2,2,0,0,2,2,1,1,1,1),
          (0,1,1,1,0,1,1,1,0,2,2,2,0,2,2,2),
          (0,0,0,1,0,0,0,1,2,2,2,1,2,2,2,1),
          (0,0,0,0,0,0,1,1,0,1,2,2,0,1,2,2),
          (0,0,0,0,1,1,0,0,2,2,1,0,2,2,1,0),
          (0,1,2,2,0,1,2,2,0,0,1,1,0,0,0,0),
          (0,0,1,2,0,0,1,2,1,1,2,2,2,2,2,2),
          (0,1,1,0,1,2,2,1,1,2,2,1,0,1,1,0),
          (0,0,0,0,0,1,1,0,1,2,2,1,1,2,2,1),
          (0,0,2,2,1,1,0,2,1,1,0,2,0,0,2,2),
          (0,1,1,0,0,1,1,0,2,0,0,2,2,2,2,2),
          (0,0,1,1,0,1,2,2,0,1,2,2,0,0,1,1),
          (0,0,0,0,2,0,0,0,2,2,1,1,2,2,2,1),
          (0,0,0,0,0,0,0,2,1,1,2,2,1,2,2,2),
          (0,2,2,2,0,0,2,2,0,0,1,2,0,0,1,1),
          (0,0,1,1,0,0,1,2,0,0,2,2,0,2,2,2),
          (0,1,2,0,0,1,2,0,0,1,2,0,0,1,2,0),
          (0,0,0,0,1,1,1,1,2,2,2,2,0,0,0,0),
          (0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0),
          (0,1,2,0,2,0,1,2,1,2,0,1,0,1,2,0),
          (0,0,1,1,2,2,0,0,1,1,2,2,0,0,1,1),
          (0,0,1,1,1,1,2,2,2,2,0,0,0,0,1,1),
          (0,1,0,1,0,1,0,1,2,2,2,2,2,2,2,2),
          (0,0,0,0,0,0,0,0,2,1,2,1,2,1,2,1),
          (0,0,2,2,1,1,2,2,0,0,2,2,1,1,2,2),
          (0,0,2,2,0,0,1,1,0,0,2,2,0,0,1,1),
          (0,2,2,0,1,2,2,1,0,2,2,0,1,2,2,1),
          (0,1,0,1,2,2,2,2,2,2,2,2,0,1,0,1),
          (0,0,0,0,2,1,2,1,2,1,2,1,2,1,2,1),
          (0,1,0,1,0,1,0,1,0,1,0,1,2,2,2,2),
          (0,2,2,2,0,1,1,1,0,2,2,2,0,1,1,1),
          (0,0,0,2,1,1,1,2,0,0,0,2,1,1,1,2),
          (0,0,0,0,2,1,1,2,2,1,1,2,2,1,1,2),
          (0,2,2,2,0,1,1,1,0,1,1,1,0,2,2,2),
          (0,0,0,2,1,1,1,2,1,1,1,2,0,0,0,2),
          (0,1,1,0,0,1,1,0,0,1,1,0,2,2,2,2),
          (0,0,0,0,0,0,0,0,2,1,1,2,2,1,1,2),
          (0,1,1,0,0,1,1,0,2,2,2,2,2,2,2,2),
          (0,0,2,2,0,0,1,1,0,0,1,1,0,0,2,2),
          (0,0,2,2,1,1,2,2,1,1,2,2,0,0,2,2),
          (0,0,0,0,0,0,0,0,0,0,0,0,2,1,1,2),
          (0,0,0,2,0,0,0,1,0,0,0,2,0,0,0,1),
          (0,2,2,2,1,2,2,2,0,2,2,2,1,2,2,2),
          (0,1,0,1,2,2,2,2,2,2,2,2,2,2,2,2),
          (0,1,1,1,2,0,1,1,2,2,0,1,2,2,2,0))
BC7_P = (None, BC7_P1, BC7_P2, BC7_P3)
BC7_A2 = (15,15,15,15,15,15,15,15,
          15,15,15,15,15,15,15,15,
          15, 2, 8, 2, 2, 8, 8,15,
          2, 8, 2, 2, 8, 8, 2, 2,
          15,15, 6, 8, 2, 8,15,15,
          2, 8, 2, 2, 2,15,15, 6,
          6, 2, 6, 8,15,15, 2, 2,
          15,15,15,15,15, 2, 2,15)
BC7_A3A = ( 3, 3,15,15, 8, 3,15,15,
            8, 8, 6, 6, 6, 5, 3, 3,
            3, 3, 8,15, 3, 3, 6,10,
            5, 8, 8, 6, 8, 5,15,15,
            8,15, 3, 5, 6,10, 8,15,
           15, 3,15, 5,15,15,15,15,
            3,15, 5, 5, 5, 8, 5,10,
            5,10, 8,13,15,12, 3, 3)
BC7_A3B = (15, 8, 8, 3,15,15, 3, 8,
           15,15,15,15,15,15,15, 8,
           15, 8,15, 3,15, 8,15, 8,
           3,15, 6,10,15,15,10, 8,
           15, 3,15,10,10, 8, 9,10,
           6,15, 8,15, 3, 6, 6, 8,
           15, 3,15,15,15,15,15,15,
           15,15,15,15, 3,15,15, 8)
BC7_I2 = (0, 21, 43, 64)
BC7_I3 = (0, 9, 18, 27, 37, 46, 55, 64)
BC7_I4 = (0, 4, 9, 13, 17, 21, 26, 30, 34, 38, 43, 47, 51, 55, 60, 64)
BC7_INTERP = (None, None, BC7_I2, BC7_I3, BC7_I4)

def log2i(x):
    x -= 1
    x |= x>>1
    x |= x>>2
    x |= x>>4
    x |= x>>8
    x |= x>>16
    x += 1
    n = 0
    while (x & 1) == 0:
        n += 1
        x >>= 1
    return n

def deswizzle(x, y, xb, yb, width, bpp):
    x_cnt = 1 if bpp==4 else 0
    y_cnt = 1
    x_used = 0
    y_used = 0
    addr = 0
    while x_used < (3 if bpp==4 else 2) and x_used + x_cnt < xb:
        x_mask = (1 << x_cnt) - 1
        y_mask = (1 << y_cnt) - 1
        addr |= (x & x_mask) << (x_used + y_used)
        addr |= (y & y_mask) << (x_used + y_used + x_cnt)
        x >>= x_cnt
        y >>= y_cnt
        x_used += x_cnt
        y_used += y_cnt
        x_cnt = xb - x_used
        if x_cnt < 0: x_cnt = 0
        if x_cnt > 1: x_cnt = 1
        y_cnt *= 2
        if y_cnt > yb - y_used: y_cnt = yb - y_used
        if y_cnt < 0: y_cnt = 0
    addr |= (x + y * (width >> x_used)) << (x_used + y_used)
    return addr

class Bits128(object):
    """Simple 128-bit accumulator.  Helper class for decode_bc7()."""
    def __init__(self, data, offset):
        self._lo, self._hi = struct.unpack('<QQ', data[offset:offset+16])
    def get(self, n):
        if n == 0: return 0
        val = self._lo & ((1<<n)-1)
        self._lo = (self._lo>>n | self._hi<<(64-n))
        self._hi >>= n
        return val

def bc7_block(bits, mode):
    """Decode a single BC7 block to RGBA8888 pixel data."""
    part_index = bits.get(mode.pb)
    partition = BC7_P[mode.ns][part_index]
    rotation = bits.get(mode.rb)
    index_sel = bits.get(mode.isb)

    color = [[[0,0,0] for j in range(2)] for i in range(3)]
    alpha = [[0,0] for i in range(3)]
    for component in range(3):
        for i in range(mode.ns):
            for endpoint in range(2):
                color[i][endpoint][component] = bits.get(mode.cb)
    if mode.ab > 0:
        for i in range(mode.ns):
            for endpoint in range(2):
                alpha[i][endpoint] = bits.get(mode.ab)
    else:
        for i in range(mode.ns):
            for endpoint in range(2):
                alpha[i][endpoint] = 255

    assert not (mode.epb != 0 and mode.spb != 0)
    if mode.epb != 0:
        for i in range(mode.ns):
            for endpoint in range(2):
                p = bits.get(1)
                for component in range(3):
                    color[i][endpoint][component] <<= 1
                    color[i][endpoint][component] |= p
                if mode.ab > 0:
                    alpha[i][endpoint] <<= 1
                    alpha[i][endpoint] |= p
    elif mode.spb != 0:
        # See https://github.com/KhronosGroup/OpenGL-Registry/issues/310
        #p0 = bits.get(1)
        #p1 = bits.get(1)
        for i in range(mode.ns):
            p = bits.get(1)
            for endpoint in range(2):
                #p = p0 if endpoint==0 else p1
                for component in range(3):
                    color[i][endpoint][component] <<= 1
                    color[i][endpoint][component] |= p
                if mode.ab > 0:
                    alpha[i][endpoint] <<= 1
                    alpha[i][endpoint] |= p

    cb = mode.cb + mode.epb + mode.spb
    ab = mode.ab + mode.epb + mode.spb
    for i in range(mode.ns):
        for endpoint in range(2):
            for component in range(3):
                color[i][endpoint][component] = \
                    (color[i][endpoint][component] << (8-cb)
                     | color[i][endpoint][component] >> (2*cb-8))
            if mode.ab > 0:
                alpha[i][endpoint] = (alpha[i][endpoint] << (8-ab)
                                      | alpha[i][endpoint] >> (2*ab-8))

    index = [[0,0,0,0] for i in range(4)]
    index2 = [[0,0,0,0] for i in range(4)]
    for y in range(4):
        for x in range(4):
            i = y*4+x
            s = partition[i]
            if s == 0:
                anchor = 0
            elif s == 1:
                if mode.ns == 2:
                    anchor = BC7_A2[part_index]
                else:
                    assert mode.ns == 3
                    anchor = BC7_A3A[part_index]
            else:
                assert s == 2
                anchor = BC7_A3B[part_index]
            ib = mode.ib
            if i == anchor:
                ib -= 1
            index[y][x] = bits.get(ib)
    if mode.ib2 > 0:
        for y in range(4):
            for x in range(4):
                i = y*4+x
                s = partition[i]
                if s == 0:
                    anchor = 0
                elif s == 1:
                    if mode.ns == 2:
                        anchor = BC7_A2[part_index]
                    else:
                        assert mode.ns == 3
                        anchor = BC7_A3A[part_index]
                else:
                    assert s == 2
                    anchor = BC7_A3B[part_index]
                ib2 = mode.ib2
                if i == anchor:
                    ib2 -= 1
                index2[y][x] = bits.get(ib2)

    block = bytearray(4*4*4)
    block_out = 0
    for yy in range(4):
        i = yy*4
        for xx in range(4):
            s = partition[i+xx]
            color_index = index2[yy][xx] if index_sel else index[yy][xx]
            alpha_index = (index2[yy][xx] if mode.ib2 and not index_sel
                           else index[yy][xx])
            c0 = color[s][0]
            c1 = color[s][1]
            a0 = alpha[s][0]
            a1 = alpha[s][1]
            cib = mode.ib2 if index_sel else mode.ib
            aib = (mode.ib2 if mode.isb and not index_sel else mode.ib)
            kc = BC7_INTERP[cib][color_index]
            ka = BC7_INTERP[aib][alpha_index]
            r = (c0[0]*(64-kc) + c1[0]*kc + 32) >> 6
            g = (c0[1]*(64-kc) + c1[1]*kc + 32) >> 6
            b = (c0[2]*(64-kc) + c1[2]*kc + 32) >> 6
            a = (a0   *(64-ka) + a1   *ka + 32) >> 6
            if rotation == 1:
                a, r = r, a
            elif rotation == 2:
                a, g = g, a
            elif rotation == 3:
                a, b = b, a
            block[block_out+0] = r
            block[block_out+1] = g
            block[block_out+2] = b
            block[block_out+3] = a
            block_out += 4

    return block

def decode_bc7(data, width, height):
    """Decode BC7 image data to RGBA8888 pixel data.

    Parameters:
        data: Image data.
        width: Image width, in pixels.
        height: Image height, in pixels.

    Returns:
        Decoded image data, as a linear array of RGBA8888 pixels.
    """
    assert isinstance(data, bytes)
    assert width > 0
    assert height > 0
    block_w = max((width+3)//4, 4)
    block_h = max((height+3)//4, 8)
    log_w = log2i(block_w)
    log_h = log2i(block_h)
    if ((block_h & (block_h-1)) != 0
            and block_h <= (1 << (log_h-1)) * 4 // 3):
        log_h -= 1
    swiz_w = (block_w+3)//4*4  # 64-byte alignment

    outbuf = bytearray(4*width*height)
    out = 0
    for y in range(0, height, 4):
        row_out = out
        for x in range(0, width, 4):
            block_out = row_out
            bits = Bits128(data,
                           deswizzle(x//4, y//4, log_w, log_h, swiz_w, 8) * 16)
            mode = 0
            while mode < 8 and bits.get(1) == 0:
                mode += 1
            if mode == 8:
                block = b'\0'*(4*4*4)
            else:
                block = bc7_block(bits, BC7_M[mode])
            block_in = 0
            for yy in range(4):
                block_out = row_out + yy*(4*width)
                for xx in range(4):
                    if x+xx < width and y+yy < height:
                        outbuf[block_out:block_out+4] = block[block_in:block_in+4]
                    block_in += 4
                    block_out += 4
            row_out += 4*4
        # end for x
        out += 4*(4*width)
    # end for y

    return outbuf


class Wilay(object):
    """Class wrapping a *.wilay texture file."""

    def __init__(self, path):
        """Initialize a Wilay instance.

        Parameters:
            path: Pathname of segment info file.

        Raises:
            OSError: Raised if the file cannot be read.
            ValueError: Raised if a parsing error is encountered.
        """
        self._path = path
        with open(self._path, 'rb') as f:
            self._parse(f.read())

    @property
    def width(self):
        """The width of the base level of this texture."""
        return self._width

    @property
    def height(self):
        """The height of the base level of this texture."""
        return self._height

    @property
    def image(self):
        """The base level texture image as a linear byte array of RGBA8888 pixels."""
        return self._image

    def _parse(self, data):
        """Parse a *.wilay file."""
        if len(data) < 40:
            raise ValueError(f'{self._path}: File is too short')
        if data[0:4] != b'LAHD':
            raise ValueError(f'{self._path}: Invalid header magic')
        texlist_ofs = u32(data, 36)
        if len(data) < texlist_ofs+8:
            raise ValueError(f'{self._path}: File is too short')
        texentry_ofs = texlist_ofs + u32(data, texlist_ofs)
        num_textures = u32(data, texlist_ofs+4)
        if num_textures != 1:
            raise ValueError(f'{self._path}: Multiple textures not supported')
        if len(data) < texentry_ofs+12:
            raise ValueError(f'{self._path}: File is too short')
        tex_offset = texlist_ofs + u32(data, texentry_ofs+4)
        tex_size = u32(data, texentry_ofs+8)
        if len(data) < tex_offset + tex_size:
            raise ValueError(f'{self._path}: File is too short')
        tex_info = tex_offset + tex_size - 56
        if data[tex_info+52:tex_info+56] != b'LBIM':
            raise ValueError(f'{self._path}: Invalid texture magic at 0x{tex_info+52:X}')
        self._width, self._height, depth, _, format, levels = \
            struct.unpack('<IIIIII', data[tex_info+24:tex_info+48])
        if depth != 1:
            raise ValueError(f'{self._path}: Unsupported texture depth {depth}')
        if format != 77:
            raise ValueError(f'{self._path}: Unsupported pixel format {format}')
        # PIL includes a (much!) faster BC7 decoder, but the decoder is broken
        # as of PIL 9.2.0 (blocks are unswizzled to the wrong locations).
        #i = PIL.Image.frombytes('RGBA', (self._width, self._height),
        #                        data[tex_offset:tex_info], 'bcn', 7)
        #self._image = i.tobytes()
        self._image = decode_bc7(data[tex_offset:tex_info],
                                 self._width, self._height)


########################################################################
# Minimap data parsing


class SegInfo(object):
    """Class wrapping a minimap segment info (*.seg) data file."""

    def __init__(self, path, seg_base_path, verbose):
        """Initialize a MapInfo instance.

        Parameters:
            path: Pathname of segment info file.
            seg_base_path: Base pathname for segment images.
            verbose: Verbosity level for parse status messages.

        Raises:
            OSError: Raised if the file cannot be read.
            ValueError: Raised if a parsing error is encountered.
        """
        self._path = path
        self._seg_base_path = seg_base_path
        self._verbose = verbose
        with open(self._path, 'rb') as f:
            self._parse(f.read(), verbose)

    @property
    def seg_width(self):
        """The width of a single minimap segment, in pixels."""
        return self._seg_width

    @property
    def seg_height(self):
        """The height of a single minimap segment, in pixels."""
        return self._seg_height

    @property
    def num_columns(self):
        """The column count (width in segments) of the minimap."""
        return self._num_columns

    @property
    def num_rows(self):
        """The row count (height in segments) of the minimap."""
        return self._num_rows

    def seg_image(self, x, y):
        """Return the image for the given segment as a linear byte array
        of RGBA8888 pixels."""
        if x < 0 or y < 0 or x >= self._num_columns or y >= self._num_rows:
            raise ValueError(f'Invalid segment position: {x},{y}')
        if self._seg_present[y][x]:
            seg_path = self._seg_path(x, y)
            if self._verbose:
                print(seg_path)
            seg_texture = Wilay(seg_path)
            if seg_texture.width != self._seg_width \
                    or seg_texture.height != self._seg_height:
                print(f'{self._path}: Segment image {seg_path} is the wrong size ({seg_texture.width}x{seg_texture.height}, should be {self._seg_width}x{self._seg_height})',
                      file=sys.stderr)
                return b'\xFF' * (4 * self._seg_width * self._seg_height)
            else:
                return seg_texture.image
        else:
            return b'\0' * (4 * self._seg_width * self._seg_height)

    def _parse(self, data, verbose):
        """Parse a *.seg file."""
        if len(data) < 32:
            raise ValueError(f'{self._path}: File is too short')
        (self._seg_width, self._seg_height, self._num_columns,
         self._num_rows) = struct.unpack('<IIII', data[0:16])
        if self._seg_width == 0 or self._seg_height == 0:
            raise ValueError(f'{self._path}: Invalid segment size {self._seg_width}x{self._seg_height}')
        if data[20:32] != b'\0'*12:
            raise ValueError(f'{self._path}: Unexpected data at 0x14')
        if len(data) < 32 + self._num_columns * self._num_rows:
            raise ValueError(f'{self._path}: File is too short')
        self._seg_present = tuple(data[32+i*self._num_columns : 32+(i+1)*self._num_columns]
                                  for i in range(self._num_rows))
        if verbose:
            print(f'    Segment size: {self._seg_width}x{self._seg_height}')
            print(f'    Minimap size: {self._num_columns}x{self._num_rows}')
            if verbose >= 2:
                print('      Segment map:')
                for y in range(self._num_rows):
                    print('        '
                          + ''.join('1' if self._seg_present[y][x] else '0'
                                    for x in range(self._num_columns)))
        # The file may have multiple segment lists, each starting with the
        # same 32-byte header (aligned to a multiple of 4 bytes), listing
        # replacement segments to reflect map changes (such as when the
        # bridge in the middle of Aetia spawns in chapter 7).  We don't
        # currently support those.

    def _seg_path(self, x, y):
        """Return the pathname of the given segment image file."""
        return self._seg_base_path + f'{x:02d}{y:02d}.wilay'


class MapInfo(object):
    """Class wrapping a minimap info (*.mi) data file."""

    # Structure for data of a single minimap layer.
    MapLayer = namedtuple('MapLayer', 'segmaps xmin ymin zmin xmax ymax zmax')

    def __init__(self, path, verbose):
        """Initialize a MapInfo instance.

        Parameters:
            path: Pathname of minimap info file.
            verbose: Verbosity level for parse status messages.

        Raises:
            OSError: Raised if the file cannot be read.
            ValueError: Raised if a parsing error is encountered.
        """
        self._path = path
        with open(self._path, 'rb') as f:
            self._parse(f.read(), verbose)

    @property
    def num_layers(self):
        """The number of layers in this minimap."""
        return self._num_layers

    def image(self, layer, scale):
        """Return the minimap image for the given layer.

        Parameters:
            layer: Layer index.
            scale: Scale factor to use when rendering, or 0 to use the
                largest scale factor (smallest image) available.

        Return value:
            Image data (a PIL.Image instance).
        """
        if layer < 0 or layer >= self._num_layers:
            raise ValueError(f'Invalid layer index: {layer}')
        if scale < 0 or scale > len(self._layers[layer].segmaps):
            raise ValueError(f'Scale factor {scale} is unavailable')
        seg = self._layers[layer].segmaps[scale-1]
        seg_rowsize = 4 * seg.seg_width
        rowsize = seg_rowsize * seg.num_columns
        data = bytearray(rowsize * seg.seg_height * seg.num_rows)
        seg_ofs = 0
        for y in range(seg.num_rows):
            for x in range(seg.num_columns):
                seg_data = seg.seg_image(x, y)
                row_ofs = seg_ofs + x*seg_rowsize
                for yy in range(seg.seg_height):
                    data[row_ofs : row_ofs+seg_rowsize] = \
                        seg_data[yy*seg_rowsize : (yy+1)*seg_rowsize]
                    row_ofs += rowsize
            seg_ofs += seg.seg_height * rowsize
        return PIL.Image.frombytes('RGBA', (seg.seg_width * seg.num_columns,
                                            seg.seg_height * seg.num_rows),
                                   bytes(data), 'raw', 'RGBA', 0, 1)

    def _parse(self, data, verbose):
        """Parse a *.mi file."""
        if len(data) < 8:
            raise ValueError(f'{self._path}: File is too short')
        if data[0:4] != b'mi  ':
            raise ValueError(f'{self._path}: Invalid header magic')
        self._num_layers = u32(data, 4)
        if len(data) != 8 + 72*self._num_layers:
            raise ValueError(f'{self._path}: File is wrong size')
        self._layers = [None] * self._num_layers
        if verbose:
            print(f'{self._path}: {self._num_layers} layers')

        segdir = os.path.dirname(self._path)
        for i in range(self._num_layers):
            ofs = 8 + 72*i
            name = asciiz(data, ofs, 16)
            (xmin, ymin, zmin, xmax, ymax, zmax) = \
                struct.unpack('<6f', data[ofs+32:ofs+56])
            if data[ofs+56:ofs+72] != b'\0'*16:
                raise ValueError(f'{self._path}: Unexpected data at 0x{ofs+56:X}')
            if verbose:
                print(f'  Layer {i}:')
                print(f'    Coord. range: {xmin:g},{ymin:g},{zmin:g} - {xmax:g},{ymax:g},{zmax:g}')
            segmaps = []
            for scale in (1,2,3):
                if scale != 1:
                    segname = f'{name}_s{scale}'
                else:
                    segname = name
                seg_info_path = os.path.join(segdir, f'{segname}_map.seg')
                seg_image_path = os.path.join(os.path.dirname(segdir),
                                              f'image/{segname}_map_')
                if scale == 1 or os.path.exists(seg_info_path):
                    if verbose:
                        print(f'    Scale {scale}:')
                    segmaps.append(
                        SegInfo(seg_info_path, seg_image_path, verbose))
            self._layers[i] = MapInfo.MapLayer(segmaps, xmin, ymin, zmin,
                                               xmax, ymax, zmax)


########################################################################
# Program entry point

def main(argv):
    """Program entry point."""
    parser = argparse.ArgumentParser(
        description='Generate a minimap image for a Xenoblade 3 map.')
    parser.add_argument('-v', '--verbose', action='count',
                        help='Output status messages during parsing.')
    parser.add_argument('-s', '--scale', type=int,
                        help=('Map scale to render (1 = highest resolution, 2 = 1/2 scale, 3 = 1/4 scale). Defaults to the highest scale (smallest image) available for the selected map and layer.'))
    parser.add_argument('datadir', metavar='DATADIR',
                        help='Pathname of directory containing Xenoblade 3 data.')
    parser.add_argument('map_id', metavar='MAP-ID',
                        help='Map ID (such as "ma01a").')
    parser.add_argument('layer', metavar='LAYER', type=int,
                        help='Map layer index (0 = main area map).')
    parser.add_argument('output', metavar='OUTPUT',
                        help=('Pathname for output PNG file.\n'
                              'If "-", the PNG data is written to standard output.\n'
                              '(Note that -v will also write to standard output.)'))
    args = parser.parse_args()
    verbose = args.verbose if args.verbose is not None else 0
    scale = args.scale if args.scale is not None else 0

    if not os.path.exists(os.path.join(args.datadir, 'menu')):
        raise Exception(f'Xenoblade 3 data not found at {args.datadir}')

    mi = MapInfo(os.path.join(args.datadir, f'menu/minimap/{args.map_id}.mi'),
                 verbose)
    image = mi.image(args.layer, scale)
    image.save(sys.stdout.buffer if args.output == '-' else args.output,
               format='png')
# end def


if __name__ == '__main__':
    main(sys.argv)
