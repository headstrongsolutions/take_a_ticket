from machine import Pin, SPI
import time
import epaper2in13
import framebuf
from writer import Writer
import days_font_10
import days_font_83

class NotionalDisplay(framebuf.FrameBuffer):
    def __init__(self, width, height, buffer):
        self.width = width
        self.height = height
        self.buffer = buffer
        self.mode = framebuf.MONO_VLSB
        super().__init__(self.buffer, self.width, self.height, self.mode)

black = 0x00
white = 0xff

epd = epaper2in13.EPD_2in13_V3_Landscape()

epd.fill(white)
epd.Clear()
epd.init()

class DisplayManager:
    def __init__(self):
        self.my_display = NotionalDisplay(250, 112, epd.buffer)
        self.wri_75 = Writer(self.my_display, days_font_83)
        self.wri_10 = Writer(self.my_display, days_font_10)

    def update(self, serving_number):
        self.my_display.fill(0xff)
        
        Writer.set_textpos(self.my_display, 9, 50) 
        self.wri_10.printstring('Currently Serving:', True)
        
        Writer.set_textpos(self.my_display, 22, 7)
        self.wri_75.printstring(f'{serving_number:03}', True)
        
        Writer.set_textpos(self.my_display, 102, 20)
        self.wri_10.printstring('Press button for a new ticket', True)
        
        epd.display(epd.buffer)
