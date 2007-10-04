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
		(year, month, day, hour, minute, second, tz) = ((x & 15) * 10 + (x >> 4) for x in read_bytes(self._file, 7))
		if year == month == day == hour == minute == second == tz == 0:
			return None
		if year < 1980:
			year += 2000
		if tz & 128:
			-(tz & ~128)
		tz = FixedOffsetTz(tz * 15)
		return datetime(year, month, day, hour, minute, second, tzinfo = tz)

	def read_address(self, variant = False):
		nbytes = read_byte(self._file)
		if variant:
			nbytes = 1 + (nbytes + 1) // 2
		if nbytes == 0:
			raise CorruptedSmi('Invalid adress length')
		tp = read_byte(self._file)
		value = ''.join('%1x%1x' % ((x & 15), x >> 4) for x in read_bytes(self._file, nbytes - 1)).rstrip('f')
		return Number(tp, value)

class Number(object):

	def __init__(self, type, value):
		if type not in (0x00, 0x81, 0x91):
			raise CorruptedSmi('Invalid adress type (0x%02x)' % type)
		self.value = value
	
	def __str__(self):
		return '<tel:%s>' % self.value

# vim:ts=4 sw=4 noet
