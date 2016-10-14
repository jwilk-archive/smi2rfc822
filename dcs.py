# encoding=UTF-8

# Copyright © 2004-2016 Jakub Wilk <jwilk@jwilk.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from common import read_byte, Reader
import re

__all__ = ('DataCodingScheme',)

class DataCodingScheme(Reader):
    dcs_map = {}

    @staticmethod
    def register(*subclasses):
        for subclass in subclasses:
            DataCodingScheme.dcs_map[subclass.code] = subclass

    def __new__(cls, file):
        byte = read_byte(file)
        if byte & (1 << 7 | 1 << 6 | 1 << 5):
            raise NotImplementedError('Unsupported Data Coding Scheme (0x%02d)' % byte)
        code = (byte >> 2) & 3
        try:
            klass = DataCodingScheme.dcs_map[code]
        except KeyError:
            raise NotImplementedError('Unsupported Data Coding Scheme (0x%02d)' % byte)
        return object.__new__(klass, file)

class Scheme7(DataCodingScheme):
    code = 0
    _mapping = {
        '\x1b\x0a': u'\u000c',
        '\x1b\x14': u'\u005e',
        '\x1b\x28': u'\u007b',
        '\x1b\x29': u'\u007d',
        '\x1b\x2f': u'\u005c',
        '\x1b\x3c': u'\u005b',
        '\x1b\x3d': u'\u007e',
        '\x1b\x3e': u'\u005d',
        '\x1b\x40': u'\u007c',
        '\x1b\x65': u'\u20ac',
        '\x00': u'\u0040',
        '\x01': u'\u00a3',
        '\x02': u'\u0024',
        '\x03': u'\u00a5',
        '\x04': u'\u00e8',
        '\x05': u'\u00e9',
        '\x06': u'\u00f9',
        '\x07': u'\u00ec',
        '\x08': u'\u00f2',
        '\x09': u'\u00c7',
        '\x0b': u'\u00d8',
        '\x0c': u'\u00f8',
        '\x0e': u'\u00c5',
        '\x0f': u'\u00e5',
        '\x10': u'\u0394',
        '\x11': u'\u005f',
        '\x12': u'\u03a6',
        '\x13': u'\u0393',
        '\x14': u'\u039b',
        '\x15': u'\u03a9',
        '\x16': u'\u03a0',
        '\x17': u'\u03a8',
        '\x18': u'\u03a3',
        '\x19': u'\u0398',
        '\x1a': u'\u039e',
        '\x1c': u'\u00c6',
        '\x1d': u'\u00e6',
        '\x1e': u'\u00df',
        '\x1f': u'\u00c9',
        '\x24': u'\u00a4',
        '\x40': u'\u00a1',
        '\x5b': u'\u00c4',
        '\x5c': u'\u00d6',
        '\x5d': u'\u00d1',
        '\x5e': u'\u00dc',
        '\x5f': u'\u00a7',
        '\x60': u'\u00bf',
        '\x7b': u'\u00e4',
        '\x7c': u'\u00f6',
        '\x7d': u'\u00f1',
        '\x7e': u'\u00fc',
        '\x7f': u'\u00e0',
    }

    def read(self):
        nseptets = self.next()
        nbytes = (nseptets * 7 + 7) // 8
        output = []
        while nbytes > 0:
            quantum = self.next(min(7, nbytes))
            value = 0
            for x in reversed(quantum):
                value <<= 8
                value |= x
            for i in xrange(8):
                output += chr(value & 0x7f),
                value >>= 7
            nbytes -= len(quantum)
        del output[nseptets:]
        s = ''.join(output)
        def repl(m):
            t = m.group(0)
            try:
                return self._mapping[t]
            except KeyError:
                return t.decode('ISO-8859-1')
        return re.sub('\x1b.|.', repl, s)

class Scheme8(DataCodingScheme):
    code = 1
    def read(self):
        nbytes = self.next()
        return self._file.read(nbytes).decode('ISO-8859-1')

class Scheme16(DataCodingScheme):
    code = 2
    def read(self):
        nbytes = self.next()
        return self._file.read(nbytes).decode('UTF-16BE')

DataCodingScheme.register(Scheme7, Scheme8, Scheme16)

# vim:ts=4 sts=4 sw=4 et
