# encoding=UTF-8

# Copyright © 2004, 2006, 2007, 2014 Jakub Wilk <jwilk@jwilk.net>
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

from array import array
from datetime import datetime, tzinfo, timedelta

__all__ = ('read_byte', 'read_bytes', 'Reader', 'CorruptedSmi', 'Number')

class CorruptedSmi(Exception):
	pass

def read_bytes(file, n):
	return array('B', file.read(n))

def read_byte(file):
	return read_bytes(file, 1)[0]

class FixedOffsetTz(tzinfo):
	"""Fixed offset in minutes east from UTC."""

	ZERO = timedelta(0)

	def __init__(self, offset):
		self.__offset = timedelta(minutes = offset)

	def utcoffset(self, dt):
		return self.__offset

	def dst(self, dt):
		return self.ZERO

class Reader(object):

	def __init__(self, file):
		self._file = file

	def read_date(self):
		(year, month, day, hour, minute, second, tz) = ((x & 15) * 10 + (x >> 4) for x in self.next(7))
		if year == month == day == hour == minute == second == tz == 0:
			return None
		if year < 1980:
			year += 2000
		if tz & 128:
			-(tz & ~128)
		tz = FixedOffsetTz(tz * 15)
		return datetime(year, month, day, hour, minute, second, tzinfo = tz)

	def read_address(self, variant = False):
		nbytes = self.next()
		if variant:
			nbytes = 1 + (nbytes + 1) // 2
		if nbytes == 0:
			return None
			# XXX raise CorruptedSmi('Invalid address length')
		tp = self.next()
		value = ''.join('%1x%1x' % ((x & 15), x >> 4) for x in self.next(nbytes - 1)).rstrip('f')
		return Number(tp, value)

	def next(self, nbytes = None):
		if nbytes is None:
			return read_byte(self._file)
		else:
			return read_bytes(self._file, nbytes)

class Number(object):

	def __init__(self, type, value):
		if type not in (0x00, 0x81, 0x91):
			raise CorruptedSmi('Invalid address type (0x%02x)' % type)
		self.value = value

	def __str__(self):
		return '<tel:%s>' % self.value

# vim:ts=4 sts=4 sw=4 noet
