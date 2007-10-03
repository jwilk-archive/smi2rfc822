from common import read_byte, read_bytes, Reader

__all__ = ('DataCodingScheme',)

class DataCodingScheme(Reader):
	dcs_map = {}

	@staticmethod
	def register(*subclasses):
		for subclass in subclasses:
			DataCodingScheme.dcs_map[subclass.code] = subclass
	
	def __new__(cls, file):
		code = read_byte(file)
		return object.__new__(DataCodingScheme.dcs_map[code], file)

class Scheme7(DataCodingScheme):
	code = 0
	_mapping = {}

	def read(self):
		nseptets = read_byte(self._file)
		nbytes = (nseptets * 7 + 7) // 8
		output = []
		while nbytes > 0:
			quantum = read_bytes(self._file, min(7, nbytes))
			value = 0
			for x in reversed(quantum):
				value <<= 8
				value |= x
			for i in xrange(8):
				output += chr(value & 0x7f),
				value >>= 7
			nbytes -= len(quantum)
		del output[nseptets:]
		return ''.join(output)

class Scheme8(DataCodingScheme):
	code = 1
	def read(self):
		nbytes = read_byte(self._file)
		return self._file.read(nbytes).decode('ISO-8859-1')

class Scheme16(DataCodingScheme):
	code = 2
	def read(self):
		nbytes = read_byte(self._file) * 2
		return self._file.read(nbytes).decode('UCS-2')

DataCodingScheme.register(Scheme7, Scheme8, Scheme16)

# vim:ts=4 sw=4 noet
