from array import array
from datetime import datetime, tzinfo, timedelta

__all__ = ('read_byte', 'read_bytes', 'Reader')

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
		if year < 1980:
			year += 2000
		if tz & 128:
			-(tz & ~128)
		tz = FixedOffsetTz(tz * 15)
		return datetime(year, month, day, hour, minute, second, tzinfo = tz)

# vim:ts=4 sw=4 noet
