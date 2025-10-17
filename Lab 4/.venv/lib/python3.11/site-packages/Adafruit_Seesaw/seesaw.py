# Copyright (c) 2017 Adafruit Industries
# Author: Dean Miller
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging
from Adafruit_bitfield import Adafruit_bitfield
import time

SEESAW_STATUS_BASE = 0x00
SEESAW_GPIO_BASE = 0x01
SEESAW_SERCOM0_BASE = 0x02

SEESAW_TIMER_BASE = 0x08
SEESAW_ADC_BASE = 0x09
SEESAW_DAC_BASE = 0x0A
SEESAW_INTERRUPT_BASE = 0x0B
SEESAW_DAP_BASE = 0x0C
SEESAW_EEPROM_BASE = 0x0D
SEESAW_NEOPIXEL_BASE = 0x0E

SEESAW_GPIO_DIRSET_BULK = 0x02
SEESAW_GPIO_DIRCLR_BULK = 0x03
SEESAW_GPIO_BULK = 0x04
SEESAW_GPIO_BULK_SET = 0x05
SEESAW_GPIO_BULK_CLR = 0x06
SEESAW_GPIO_BULK_TOGGLE = 0x07
SEESAW_GPIO_INTENSET = 0x08
SEESAW_GPIO_INTENCLR = 0x09
SEESAW_GPIO_INTFLAG = 0x0A
SEESAW_GPIO_PULLENSET = 0x0B
SEESAW_GPIO_PULLENCLR = 0x0C

SEESAW_STATUS_HW_ID = 0x01
SEESAW_STATUS_VERSION = 0x02
SEESAW_STATUS_OPTIONS = 0x03
SEESAW_STATUS_SWRST = 0x7F

SEESAW_TIMER_STATUS = 0x00
SEESAW_TIMER_PWM = 0x01

SEESAW_ADC_STATUS = 0x00
SEESAW_ADC_INTEN = 0x02
SEESAW_ADC_INTENCLR = 0x03
SEESAW_ADC_WINMODE = 0x04
SEESAW_ADC_WINTHRESH = 0x05
SEESAW_ADC_CHANNEL_OFFSET = 0x07

SEESAW_SERCOM_STATUS = 0x00
SEESAW_SERCOM_INTEN = 0x02
SEESAW_SERCOM_INTENCLR = 0x03
SEESAW_SERCOM_BAUD = 0x04
SEESAW_SERCOM_DATA = 0x05

SEESAW_NEOPIXEL_STATUS = 0x00
SEESAW_NEOPIXEL_PIN = 0x01
SEESAW_NEOPIXEL_SPEED = 0x02
SEESAW_NEOPIXEL_BUF_LENGTH = 0x03
SEESAW_NEOPIXEL_BUF = 0x04
SEESAW_NEOPIXEL_SHOW = 0x05

ADC_INPUT_0_PIN = 0x02
ADC_INPUT_1_PIN  = 0x03
ADC_INPUT_2_PIN = 0x04
ADC_INPUT_3_PIN = 0x05

PWM_0_PIN = 0x04
PWM_1_PIN = 0x05
PWM_2_PIN = 0x06
PWM_3_PIN = 0x07

class Seesaw(object):

	INPUT = 0x00
	OUTPUT = 0x01
	INPUT_PULLUP = 0x02

	def __init__(self, addr=0x49, i2c=None, **kwargs):
		# Create I2C device.
		if i2c is None:
			import Adafruit_GPIO.I2C as I2C
			i2c = I2C
		self._bus = i2c.get_i2c_device(addr, **kwargs)._bus
		self.addr = addr

		self._sercom_status = Adafruit_bitfield([('ERROR', 1), ('DATA_RDY', 1)])
		self._sercom_inten = Adafruit_bitfield([('ERROR', 1), ('DATA_RDY', 1)])
		self.begin()

	def begin(self):
		self.sw_reset()
		time.sleep(.500)

		c = self.read8(SEESAW_STATUS_BASE, SEESAW_STATUS_HW_ID)

		if c != 0x55:
			print(c)
			raise RuntimeError("Seesaw hardware ID returned is not correct! Please check your wiring.")

	def sw_reset(self):

		self.write8(SEESAW_STATUS_BASE, SEESAW_STATUS_SWRST, 0xFF)

	def get_options(self):

		buf = self.read(SEESAW_STATUS_BASE, SEESAW_STATUS_OPTIONS, 4)
		ret = (buf[0] << 24) | (buf[1] << 16) | (buf[2] << 8) | buf[3]
		return ret

	def get_version(self):

		buf = self.read(SEESAW_STATUS_BASE, SEESAW_STATUS_VERSION, 4)
		ret = (buf[0] << 24) | (buf[1] << 16) | (buf[2] << 8) | buf[3]
		return ret

	def pin_mode(self, pin,  mode):

		self.pin_mode_bulk(1 << pin, mode)


	def digital_write(self, pin,  value):

		self.digital_write_bulk(1 << pin, value)


	def digital_read(self, pin):

		return self.digital_read_bulk((1 << pin)) != 0


	def digital_read_bulk(self, pins):

		buf = self.read(SEESAW_GPIO_BASE, SEESAW_GPIO_BULK, 4)
		ret = ( (buf[0] & 0xF) << 24) | (buf[1] << 16) | (buf[2] << 8) | buf[3] #TODO: weird overflow error, fix
		return ret & pins


	def set_GPIO_interrupts(self, pins, enabled):

		cmd =  bytearray([(pins >> 24) & 0xFF, (pins >> 16) & 0xFF, (pins >> 8) & 0xFF, pins & 0xFF])
		if enabled:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_INTENSET, cmd)
		else:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_INTENCLR, cmd)


	def analog_read(self, pin):

		if pin == ADC_INPUT_0_PIN:
			p = 0
		elif pin == ADC_INPUT_1_PIN:
			p = 1
		elif pin == ADC_INPUT_2_PIN: 
			p = 2
		elif pin == ADC_INPUT_3_PIN: 
			p = 3
		else:
			return 0

		buf = self.read(SEESAW_ADC_BASE, SEESAW_ADC_CHANNEL_OFFSET + p, 2)
		ret = buf[0] << 8 | buf[1]
		time.sleep(.001)
		return ret


	def pin_mode_bulk(self, pins, mode):

		cmd =  bytearray([(pins >> 24) & 0xFF, (pins >> 16) & 0xFF, (pins >> 8) & 0xFF, pins & 0xFF ])

		if mode == self.OUTPUT:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_DIRSET_BULK, cmd)
			
		elif mode == self.INPUT:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_DIRCLR_BULK, cmd)
			
		elif mode == self.INPUT_PULLUP:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_DIRCLR_BULK, cmd)
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_PULLENSET, cmd)
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_BULK_SET, cmd)
			

	def digital_write_bulk(self, pins, value):

		cmd =  bytearray([(pins >> 24) & 0xFF, (pins >> 16) & 0xFF, (pins >> 8) & 0xFF, pins & 0xFF])
		if value:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_BULK_SET, cmd)
		else:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_BULK_CLR, cmd)


	def analog_write(self, pin, value):

		p = -1
		if pin == PWM_0_PIN:
			p = 0 
		elif pin == PWM_1_PIN:
			p = 1 
		elif pin == PWM_2_PIN:
			p = 2 
		elif pin == PWM_3_PIN:
			p = 3

		if p > -1:
			cmd = bytearray([p, value])
			self.write(SEESAW_TIMER_BASE, SEESAW_TIMER_PWM, cmd)

	def enable_sercom_data_rdy_interrupt(self, sercom):

		self._sercom_inten.DATA_RDY = 1
		self.write8(SEESAW_SERCOM0_BASE + sercom, SEESAW_SERCOM_INTEN, _sercom_inten.get())


	def disable_sercom_data_rdy_interrupt(self, sercom):

		_sercom_inten.DATA_RDY = 0
		self.write8(SEESAW_SERCOM0_BASE + sercom, SEESAW_SERCOM_INTEN, _sercom_inten.get())


	def read_sercom_data(self, sercom):

		return self.read8(SEESAW_SERCOM0_BASE + sercom, SEESAW_SERCOM_DATA)


	def set_i2c_addr(self, addr):

		self.eeprom_write8(SEESAW_EEPROM_I2C_ADDR, addr)
		time.sleep(.250)
		self.begin(addr) #restart w/ the new addr


	def get_i2c_addr(self,):

		return self.read8(SEESAW_EEPROM_BASE, SEESAW_EEPROM_I2C_ADDR)


	def eeprom_write8(self, addr,  val):
		self.eeprom_write(addr, bytearray([val]))


	def eeprom_write(self, addr,  buf):

		self.write(SEESAW_EEPROM_BASE, addr, buf)


	def eeprom_read8(self, addr):

		return self.read8(SEESAW_EEPROM_BASE, addr)


	def uart_set_baud(self, baud):

		cmd = bytearray([(baud >> 24) & 0xFF, (baud >> 16) & 0xFF, (baud >> 8) & 0xFF, baud & 0xFF])
		self.write(SEESAW_SERCOM0_BASE, SEESAW_SERCOM_BAUD, cmd)


	def write8(self, regHigh, regLow, value):

		self.write(regHigh, regLow, bytearray([value]))


	def read8(self, regHigh, regLow):

		ret = self.read(regHigh, regLow, 1)

		return ret[0]


	def read(self, regHigh,  regLow, length, delay=.001):
		self.write(regHigh, regLow)

		time.sleep(delay)

		ret = self._bus._device.read(length)
		return [ord(x) for x in ret]


	def write(self, regHigh,  regLow, buf = None):
		c = bytearray([regHigh, regLow])
		if not buf == None:
			c = c + buf

		self._bus._select_device(self.addr)
		self._bus._device.write(c)