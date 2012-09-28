# Copyright 2012 Daniel Berlin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import smbus

# For the PCA 953X and 955X series, the 8 GPIO chips have these port numbers
# The 16 GPIO chips have the first port for each type at double these numbers
# IE The first config port is 6
INPUT_PORT = 0
OUTPUT_PORT = 1
POLARITY_PORT = 2
CONFIG_PORT = 3
    
class PCA95XX(object):

    def __init__(self, busnum, address, num_gpios):
        assert num_gpios >= 0 and num_gpios <= 16, "Number of GPIOs must be between 0 and 16"
        self.bus = smbus.SMBus(busnum);
        self.address = address
        self.num_gpios = num_gpios
        if num_gpios <= 8:
            self.direction = self.bus.read_byte_date(address, CONFIG_PORT)
	    self.outputvalue = self.bus.read_byte_data(address, OUTPUT_PORT)
        elif num_gpios > 8 and num_gpios <= 16:
            self.direction = self.bus.read_word_data(address, CONFIG_PORT << 1)
	    self.outputvalue = self.bus.read_word_data(address, OUTPUT_PORT << 1)
        
    def _changebit(self, bitmap, bit, value):
        assert value == 1 or value == 0, "Value is %s must be 1 or 0" % value
        if value == 0:
            return bitmap & ~(1 << bit)
        elif value == 1:
            return bitmap | (1 << bit)

    def _readandchangepin(self, port, pin, value, currvalue = None):
        assert pin >= 0 and pin < self.num_gpios, "Pin number %s is invalid, only 0-%s are valid" % (pin, self.num_gpios)
        assert self.direction & (1 << pin) == 0, "Pin %s not set to output" % pin
	if not currvalue:
          if self.num_gpios <= 8:
             currvalue = self.bus.read_byte_data(self.address, port)
          elif self.num_gpios > 8 and self.num_gpios <= 16:
             currvalue = self.bus.read_word_data(self.address, port << 1)
        newvalue = self._changebit(currvalue, pin, value)
        if self.num_gpios <= 8:
            self.bus.write_byte_data(self.address, port, newvalue)
        else:
            self.bus.write_word_data(self.address, port << 1, newvalue)
        return newvalue

    def polarity(self, pin, value):
        return self._readandchangepin(POLARITY_PORT, pin, value)

    # Set pin to either input or output mode
    def config(self, pin, mode):
        assert pin >= 0 and pin < self.num_gpios, "Pin number %s is invalid, only 0-%s are valid" % (pin, self.num_gpios)
        newdirection = self._changebit(self.direction, pin, mode)
        if self.num_gpios <= 8:
            self.bus.write_byte_data(self.address, CONFIG_PORT, newdirection)
        elif self.num_gpios > 8 and self.num_gpios <= 16:
            self.bus.write_word_data(self.address, CONFIG_PORT << 1, newdirection)
        self.direction = newdirection
        return self.direction

    def output(self, pin, value):
        assert pin >= 0 and pin < self.num_gpios, "Pin number %s is invalid, only 0-%s are valid" % (pin, self.num_gpios)
        assert self.direction & (1 << pin) == 0, "Pin %s not set to output" % pin
	self.outputvalue = self._readandchangepin(OUTPUT_PORT, pin, value, self.outputvalue)
	return self.outputvalue
        
    def input(self, pin):
        assert pin >= 0 and pin < self.num_gpios, "Pin number %s is invalid, only 0-%s are valid" % (pin, self.num_gpios)
        assert self.direction & (1 << pin) != 0, "Pin %s not set to input" % pin
        if self.num_gpios <= 8:
            value = self.bus.read_byte_data(self.address, INPUT_PORT)
        elif self.num_gpios > 8 and self.num_gpios <= 16:
            value = self.bus.read_word_data(self.address, INPUT_PORT << 1)
        return value & (1 << pin)

        

# RPi.GPIO compatible interface for PCA95XX

class PCA95XX_GPIO(object):
    OUT = 0
    IN = 1
    BCM = 0
    BOARD = 0
    def __init__(self, busnum, address, num_gpios):
        self.chip = PCA95XX(busnum, address, num_gpios)
    def setmode(self, mode):
        # do nothing
        pass
    def setup(self, pin, mode):
        self.chip.config(pin, mode)
    def input(self, pin):
        return self.chip.input(pin)
    def output(self, pin, value):
        self.chip.output(pin, value)
        
