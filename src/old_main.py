# Code in this file will run on startup.
# This is where you instantiate the various things
# and then have the infinite running while loop
# in Thonny/VSCode, you will likely need to 'stop' python
# to be able to do anything..

# e.g.
from machine import Pin, SPI
import time
import epaper2in13
import framebuf

from writer import Writer
import days_font_10
import days_font_83

import test_printer

class NotionalDisplay(framebuf.FrameBuffer):
    def __init__(self, width, height, buffer):
        self.width = width
        self.height = height
        self.buffer = buffer
        self.mode = framebuf.MONO_VLSB
        super().__init__(self.buffer, self.width, self.height, self.mode)

    def show(self):
        ...

black = 0x00
white = 0xff

epd = epaper2in13.EPD_2in13_V3_Landscape()

epd.fill(white)
epd.Clear()
epd.init()

my_display = NotionalDisplay(250, 112, epd.buffer)
wri_75 = Writer(my_display, days_font_83)
wri_11 = Writer(my_display, days_font_10)

Writer.set_textpos(my_display, 9, 50)
wri_11.printstring('         Currently Serving:', True)
Writer.set_textpos(my_display, 22, 7)
wri_75.printstring('333', True)
Writer.set_textpos(my_display, 102, 20)
wri_11.printstring('      Press button for a new ticket', True)


epd.display(epd.buffer)


