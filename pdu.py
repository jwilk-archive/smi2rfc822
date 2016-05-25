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

from common import Reader, read_byte
from dcs import DataCodingScheme

__all__ = ('Unit',)

class Unit(Reader):

	pdu_map = {}

	@staticmethod
	def register(*subclasses):
		for subclass in subclasses:
			Unit.pdu_map[subclass.code] = subclass

	def __new__(cls, file):
		first_byte = read_byte(file)
		self = object.__new__(Unit.pdu_map[first_byte & 3], file)
		self._first_byte = first_byte
		return self

	def __init__(self, file):
		Reader.__init__(self, file)

	def read_pid(self):
		return self.next()

	def read_dcs(self):
		return DataCodingScheme(self._file)

	def update_first_byte(self):
		first_byte = self._first_byte
		del self._first_byte
		self.have_reply_path = bool((first_byte >> 7) & 1)
		self.have_udhi = bool((first_byte >> 6) & 1)
		self.status_report_requested = bool((first_byte >> 5) & 1)

	def __str__(self):
		return '\n'.join(
		[
			'X-Have-Reply-Path: %s' % self.have_reply_path,
			'X-Status-Report-Requested: %s' % self.status_report_requested
		])

class _Submit(Unit):

	code = 0

	def __init__(self, file):
		Unit.__init__(self, file)
		self.update_first_byte()
		self.sender = self.read_address(variant = True)
		self.pid = self.read_pid()
		self.dcs = self.read_dcs()
		self.date = self.read_date()
		self.message = self.dcs.read()

	def update_first_byte(self):
		first_byte = self._first_byte
		Unit.update_first_byte(self)
		self.have_more_messages_to_send = bool((first_byte >> 2) & 1)

	def __str__(self):
		return Unit.__str__(self) + '\n' + '\n'.join(
		[
			'From: %s' % self.sender,
			'Date: %s' % self.date,
			'Content-Type: text/plain; charset=UTF-8',
			'\n%s' % self.message.encode('UTF-8')
		])

class _Deliver(Unit):

	class VerifyFormat(Reader):
		pass

	class NoVerifyFormat(VerifyFormat):
		def read(self):
			pass

	class RelativeVerifyFormat(VerifyFormat):
		def read(self):
			from datetime import timedelta
			byte = self.next()
			if byte <= 143:
				return timedelta(minutes = (byte + 1) * 5)
			elif byte <= 167:
				return timedelta(hours = 12, minutes = (byte - 143) * 30)
			elif byte <= 196:
				return timedelta(days = byte - 166)
			else:
				return timedelta(weeks = byte - 192)

	class EnhancedVerifyFormat(VerifyFormat):
		def read(self):
			self.next(7)
			return NotImplemented

	class AbsoluteVerifyFormat(VerifyFormat):
		def read(self):
			self.next(7)
			return NotImplemented

	code = 1
	verify_format_map = \
	{
		0: NoVerifyFormat,
		1: EnhancedVerifyFormat,
		2: RelativeVerifyFormat,
		3: AbsoluteVerifyFormat
	}

	def __init__(self, file):
		Unit.__init__(self, file)
		self.update_first_byte()
		self.reference_no = self.read_reference()
		self.recipient = self.read_address(variant = True)
		self.pid = self.read_pid()
		self.dcs = self.read_dcs()
		self.validity_period = self.read_validity_period()
		self.message = self.dcs.read()

	def read_reference(self):
		return self.next()

	def read_validity_period(self):
		return self.validity_period_format.read()

	def update_first_byte(self):
		first_byte = self._first_byte
		Unit.update_first_byte(self)
		self.validity_period_format = self.verify_format_map[(first_byte >> 3) & 3](self._file)
		self.reject_duplicates = bool((first_byte >> 2) & 1)

	def __str__(self):
		return Unit.__str__(self) + '\n' + '\n'.join(
		[
			'To: %s' % self.recipient,
			'X-Validity-Period: %s' % self.validity_period,
			'Content-Type: text/plain; charset=UTF-8',
			'\n%s' % self.message.encode('UTF-8')
		])


Unit.register(_Deliver, _Submit)

# vim:ts=4 sts=4 sw=4 noet
