#!/usr/bin/env python
# coding: utf-8

from machine import UART, Pin
from struct import unpack
from time import sleep

#===========================================================#
# RASPBERRY PI (tested with Raspbian Jan 2012):
# - Ensure that ttyAMA0 is not used for serial console access:
# edit /boot/cmdline.txt (remove all name-value pairs containing
# ttyAMA0) and comment out last line in /etc/inittab.
# - Fix user permissions with "sudo usermod -a -G dialout pi"
# - Reboot
# - Ensure that the SERIALPORT setting is correct below
#
# BEAGLE BONE:
# Mux settings (Ängström 2012.05, also work on ubuntu 12.04):
# echo 1 > /sys/kernel/debug/omap_mux/spi0_sclk
# echo 1 > /sys/kernel/debug/omap_mux/spi0_d0
#===========================================================#

class BitmapHeader:
    SIZE_IN_BYTES = 14

    def __init__(self, bytes):
        if len(bytes) != 14:
            raise ValueError

        if bytes[0:2] != b'BM':
            raise ValueError

        self.file_size = int.from_bytes(bytes[2:6], 'little')
        self.data_offset = int.from_bytes(bytes[-4:], 'little')


class BitmapHeaderInfo:
    SIZE_IN_BYTES = 40

    def __init__(self, bytes):
        if len(bytes) != 40:
            raise ValueError
        if int.from_bytes(bytes[12:14], 'little') != 1:
            raise ValueError # planes
        if int.from_bytes(bytes[14:16], 'little') != 1:
            raise ValueError # bit-depth
        if int.from_bytes(bytes[16:20], 'little') != 0:
            raise ValueError # compression
        if int.from_bytes(bytes[32:36], 'little') > 1:
            raise ValueError # we accept at most 1 color
        if int.from_bytes(bytes[36:40], 'little') > 1:
            raise ValueError # we accept at most 1 significant color

        self.width = int.from_bytes(bytes[4:8], 'little')
        self.height = int.from_bytes(bytes[8:12], 'little')

        self.width_in_bytes = int((self.width+7)/8)
        padding = (4 - int(self.width_in_bytes % 4)) % 4

        self.line_width = self.width_in_bytes + padding
        self.width_padding = (self.width_in_bytes + padding) * 8 - self.width
        self.last_byte_padding = self.width_in_bytes * 8 - self.width

        self.data_size = int.from_bytes(bytes[20:24], 'little')
        self.ppm_x = int.from_bytes(bytes[24:28], 'little')
        self.ppm_y = int.from_bytes(bytes[28:32], 'little')


class ThermalPrinter(object):
    """

        Thermal printing library that controls the "micro panel thermal printer" sold in
        shops like Adafruit and Sparkfun (e.g. http://www.adafruit.com/products/597).
        Mostly ported from Ladyada's Arduino library
        (https://github.com/adafruit/Adafruit-Thermal-Printer-Library) to run on
        BeagleBone and Raspberry Pi.

        Currently handles printing image data and text, but the rest of the
        built-in functionality like underlining and barcodes are trivial
        to port to Python when needed.

        If on BeagleBone or similar device, remember to set the mux settings
        or change the UART you are using. See the beginning of this file for
        default setup.

        Thanks to Matt Richardson for the initial pointers on controlling the
        device via Python.

        @author: Lauri Kainulainen
        
        Subsequent changes:
        I have a RS232 type of these printers and the firmware is subtley different so
        I've needed to comment out some of the initialisation settings as these were
        causing strange characters to print on every __init__       
        I've also added a print BMP routine
        
        @boncester

    """

    # pixels with more color value (average for multiple channels) are counted as white
    # tweak this if your images appear too black or too white
    black_threshold = 48
    # pixels with less alpha than this are counted as white
    alpha_threshold = 127

    printer = None

    _ESC = chr(27)

    # These values (including printDensity and printBreaktime) are taken from
    # lazyatom's Adafruit-Thermal-Library branch and seem to work nicely with bitmap
    # images. Changes here can cause symptoms like images printing out as random text.
    # Play freely, but remember the working values.
    # https://github.com/adafruit/Adafruit-Thermal-Printer-Library/blob/0cc508a9566240e5e5bac0fa28714722875cae69/Thermal.cpp

    # Set "max heating dots", "heating time", "heating interval"
    # n1 = 0-255 Max printing dots, Unit (8dots), Default: 7 (64 dots)
    # n2 = 3-255 Heating time, Unit (10us), Default: 80 (800us)
    # n3 = 0-255 Heating interval, Unit (10us), Default: 2 (20us)
    # The more max heating dots, the more peak current will cost
    # when printing, the faster printing speed. The max heating
    # dots is 8*(n1+1). The more heating time, the more density,
    # but the slower printing speed. If heating time is too short,
    # blank page may occur. The more heating interval, the more
    # clear, but the slower printing speed.

    def __init__(self, heatTime=80, heatInterval=2, heatingDots=7):
        
        self.printer = UART(0, baudrate=9600, stop=1, rx=Pin(1, Pin.IN), tx=Pin(0, Pin.OUT))
        self.printer.write(self._ESC) # ESC - command
        #self.printer.write(chr(64)) # @   - initialize
        #self.printer.write(self._ESC) # ESC - command
        self.printer.write(chr(55)) # 7   - print settings
        self.printer.write(chr(heatingDots))  # Heating dots (20=balance of darkness vs no jams) default = 20
        #self.printer.write(chr(heatTime)) # heatTime Library default = 255 (max)
        self.printer.write(chr(heatInterval)) # Heat interval (500 uS = slower, but darker) default = 250

        # Description of print density from page 23 of the manual:
        # DC2 # n Set printing density
        # Decimal: 18 35 n
        # D4..D0 of n is used to set the printing density. Density is 50% + 5% * n(D4-D0) printing density.
        # D7..D5 of n is used to set the printing break time. Break time is n(D7-D5)*250us.
        printDensity = 15 # 120% (? can go higher, text is darker but fuzzy)
        printBreakTime = 15 # 500 uS
        self.printer.write(chr(18))
        self.printer.write(chr(35))
        #self.printer.write(chr((printDensity << 4) | printBreakTime))

    def offline(self):
        # Take the printer offline. Print commands sent after this will be
        # ignored until 'online' is called.
        self.printer.write(self._ESC)
        self.printer.write(chr(61))
        self.printer.write(chr(0))

    def online(self):
        # Take the printer back online. Subsequent print commands will be obeyed.
        self.printer.write(self._ESC)
        self.printer.write(chr(61))
        self.printer.write(chr(1))

    def sleep(self):
        # Put the printer into a low-energy state immediately.
        self.sleep_after(1)  # Can't be 0, that means 'don't sleep'

    def sleep_after(self, seconds):
        # Put the printer into a low-energy state after the given number
        # of seconds.
        if seconds:
            sleep(seconds)
            self.printer.write(self._ESC)
            self.printer.write(chr(56))
            self.printer.write(chr(seconds))
            self.printer.write(chr(seconds >> 8))

    def wake(self):
        # Wake the printer from a low-energy state.
        self.printer.write(chr(255))
        sleep(0.05)
        self.printer.write(self._ESC)
        self.printer.write(chr(56))
        self.printer.write(chr(0))
        self.printer.write(chr(0))

    def has_paper(self):
        # Check the status of the paper using the printer's self reporting
        # ability. SerialTX _must_ be connected!
        status = -1
        self.printer.write(self._ESC)
        self.printer.write(chr(118))
        self.printer.write(chr(0))
        for i in range(0, 9):
            if self.printer.inWaiting():
                status = unpack('b', self.printer.read())[0]
                break
            sleep(0.01)
        return not bool(status & 0b00000100)

    def reset(self):
        self.printer.write(self._ESC)
        self.printer.write(chr(64))

    def linefeed(self, number=1):
        for _ in range(number):
            self.printer.write(chr(10))

    def justify(self, align="L"):
        pos = 0
        if align == "L":
            pos = 0
        elif align == "C":
            pos = 1
        elif align == "R":
            pos = 2
        self.printer.write(self._ESC)
        self.printer.write(chr(97))
        self.printer.write(chr(pos))

    def bold(self, on=True):
        self.printer.write(self._ESC)
        self.printer.write(chr(69))
        self.printer.write(chr(on))

    def font_b(self, on=True):
        self.printer.write(self._ESC)
        self.printer.write(chr(33))
        self.printer.write(chr(on))

    def underline(self, on=True):
        self.printer.write(self._ESC)
        self.printer.write(chr(45))
        self.printer.write(chr(on))

    def inverse(self, on=True):
        self.printer.write(chr(29))
        self.printer.write(chr(66))
        self.printer.write(chr(on))

    def upsidedown(self, on=True):
        self.printer.write(self._ESC)
        self.printer.write(chr(123))
        self.printer.write(chr(on))

    def barcode_chr(self, msg):
        self.printer.write(chr(29)) # Leave
        self.printer.write(chr(72)) # Leave
        self.printer.write(msg)     # Print barcode # 1:Abovebarcode 2:Below 3:Both 0:Not printed

    def barcode_height(self, msg):
        self.printer.write(chr(29))  # Leave
        self.printer.write(chr(104)) # Leave
        self.printer.write(msg)      # Value 1-255 Default 50

    def barcode_height(self):
        self.printer.write(chr(29))  # Leave
        self.printer.write(chr(119)) # Leave
        self.printer.write(chr(2))   # Value 2,3 Default 2

    def barcode(self, msg):
        """ Please read http://www.adafruit.com/datasheets/A2-user%20manual.pdf
            for information on how to use barcodes. """
        # CODE SYSTEM, NUMBER OF CHARACTERS
        # 65=UPC-A    11,12    #71=CODEBAR    >1
        # 66=UPC-E    11,12    #72=CODE93    >1
        # 67=EAN13    12,13    #73=CODE128    >1
        # 68=EAN8    7,8    #74=CODE11    >1
        # 69=CODE39    >1    #75=MSI        >1
        # 70=I25        >1 EVEN NUMBER
        self.printer.write(chr(29))  # LEAVE
        self.printer.write(chr(107)) # LEAVE
        self.printer.write(chr(65))  # USE ABOVE CHART
        self.printer.write(chr(12))  # USE CHART NUMBER OF CHAR
        self.printer.write(msg)

    def print_text(self, msg, chars_per_line=None):
        """ Print some text defined by msg. If chars_per_line is defined,
            inserts newlines after the given amount. Use normal '\n' line breaks for
            empty lines. """
        if not chars_per_line:
            self.printer.write(msg)
            sleep(0.2)
        else:
            l = list(msg)
            le = len(msg)
            for i in xrange(chars_per_line + 1, le, chars_per_line + 1):
                l.insert(i, '\n')
            self.printer.write("".join(l))
            sleep(0.2)

    def print_markup(self, markup):
        """ Print text with markup for styling.

        Keyword arguments:
        markup -- text with a left column of markup as follows:
        first character denotes style (n=normal, b=bold, u=underline, i=inverse, f=font B)
        second character denotes justification (l=left, c=centre, r=right)
        third character must be a space, followed by the text of the line.
        """
        lines = markup.splitlines(True)
        for l in lines:
            style = l[0]
            justification = l[1].upper()
            text = l[3:]

            if style == 'b':
                self.bold()
            elif style == 'u':
               self.underline()
            elif style == 'i':
               self.inverse()
            elif style == 'f':
                self.font_b()

            self.justify(justification)
            self.print_text(text)
            if justification != 'L':
                self.justify()

            if style == 'b':
                self.bold(False)
            elif style == 'u':
               self.underline(False)
            elif style == 'i':
               self.inverse(False)
            elif style == 'f':
                self.font_b(False)

    def printBitmap(self, w, h, bitmap, LaaT=False):
        rowBytes = int((w + 7) / 8)  # Round up to next byte boundary
        if rowBytes >= 48:
            rowBytesClipped = 48  # 384 pixels max width
        else:
            rowBytesClipped = rowBytes

        # if LaaT (line-at-a-time) is True, print bitmaps
        # scanline-at-a-time (rather than in chunks).
        # This tends to make for much cleaner printing
        # (no feed gaps) on large images...but has the
        # opposite effect on small images that would fit
        # in a single 'chunk', so use carefully!
        if LaaT: maxChunkHeight = 1
        else:    maxChunkHeight = 50 # lower max chunk (not 255) for memory-constrained systems (LoPy v1)

        i = 0
        for rowStart in range(0, h, maxChunkHeight):
            chunkHeight = h - rowStart
            if chunkHeight > maxChunkHeight:
                chunkHeight = maxChunkHeight

            # Timeout wait happens here
            # TODO CGMORSE - originally this was writeBytes from Adafruit
            # self.printer.writeBytes(18, 42, chunkHeight, rowBytesClipped)

            for y in range(chunkHeight):
                line = bitmap[i:i+rowBytesClipped]
                # TODO CGMORSE - no timeout in this class
                # self.timeoutWait()
                # self.timeoutSet(len(line) * self.dotPrintTime)
                self.printer.write(bytearray(line))
                i += rowBytes

        self.prevByte = '\n'

    def printBitmapFromFile(self, w, h, filename, LaaT=False):
        rowBytes = int((w + 7) / 8)  # Round up to next byte boundary
        if rowBytes >= 48:
            rowBytesClipped = 48  # 384 pixels max width
        else:
            rowBytesClipped = rowBytes

        # if LaaT (line-at-a-time) is True, print bitmaps
        # scanline-at-a-time (rather than in chunks).
        # This tends to make for much cleaner printing
        # (no feed gaps) on large images...but has the
        # opposite effect on small images that would fit
        # in a single 'chunk', so use carefully!
        if LaaT: maxChunkHeight = 1
        else:    maxChunkHeight = 50 # lower max chunk (not 255) for memory-constrained systems (LoPy v1)

        try:
            with open(filename, 'rb') as bitmap_file:
                i = 0
                for rowStart in range(0, h, maxChunkHeight):
                    chunkHeight = h - rowStart
                    if chunkHeight > maxChunkHeight:
                        chunkHeight = maxChunkHeight

                    # Timeout wait happens here
                    # TODO CGMORSE - originally this was writeBytes from Adafruit
                    self.printer.write(18, 42, chunkHeight, rowBytesClipped)

                    for y in range(chunkHeight):
                        line = bytearray(bitmap_file.read(rowBytesClipped))
                        # TODO CGMORSE - no timeout in this class
                        # self.timeoutWait()
                        # self.timeoutSet(rowBytesClipped * self.dotPrintTime)
                        self.printer.write(line)
                        i += rowBytes
                        bitmap_file.seek(i)

                self.prevByte = '\n'

        except OSError as e:
            print('file access error: {}'.format(e.errno))


    def printBMPImage(self, filename, LaaT=False):
        try:
            with open(filename, 'rb') as bmp_file:
                header = BitmapHeader(bmp_file.read(BitmapHeader.SIZE_IN_BYTES))
                header_info = BitmapHeaderInfo(bmp_file.read(BitmapHeaderInfo.SIZE_IN_BYTES))

                data_end = header.file_size - 2

                if header_info.width_in_bytes >= 48:
                    rowBytesClipped = 48  # 384 pixels max width
                else:
                    rowBytesClipped = header_info.width_in_bytes

                # if LaaT (line-at-a-time) is True, print bitmaps
                # scanline-at-a-time (rather than in chunks).
                # This tends to make for much cleaner printing
                # (no feed gaps) on large images...but has the
                # opposite effect on small images that would fit
                # in a single 'chunk', so use carefully!
                if LaaT: maxChunkHeight = 1
                else:    maxChunkHeight = 50 # lower max chunk (not 255) for memory-constrained systems (LoPy v1)

                for startRow in range(0, header_info.height, maxChunkHeight):
                    chunkHeight = header_info.height - startRow
                    if chunkHeight > maxChunkHeight:
                        chunkHeight = maxChunkHeight

                    # Timeout wait happens here
                    # TODO CGMORSE - originally this was writeBytes from Adafruit
                    # converted to bytes(*args) and it now complains about 'wrong number of arguments'
                    self.printer.write(bytes(18, 42, chunkHeight, rowBytesClipped))
                    for row in range(startRow + 1, startRow + 1 + chunkHeight):
                        # seek to beginning of line
                        bmp_file.seek(data_end - row * header_info.line_width)

                        # read the whole line
                        if header_info.last_byte_padding == 0 or header_info.width_in_bytes <= rowBytesClipped:
                            line = bytearray(bmp_file.read(rowBytesClipped))
                            # TODO CGMORSE - no timeout in this class
                            # self.timeoutWait()
                            # self.timeoutSet(self.dotPrintTime)
                            self.printer.write(line)
                        else:
                            # TODO CGMORSE - no timeout in this class
                            # self.timeoutWait()
                            # self.timeoutSet(self.dotPrintTime)
                            if rowBytesClipped > 1:
                                line = bytearray(bmp_file.read(rowBytesClipped-1))
                                self.printer.write(line)

                            data = bmp_file.read(1)
                            mask = 0xFF<<header_info.last_byte_padding & 0xFF
                            self.printer.write(bytes([ord(data) & mask]))

                self.prevByte = '\n'

        except OSError as e:
            print('error: {}'.format(e))

    # def convert_pixel_array_to_binary(self, pixels, w, h):
    #     """ Convert the pixel array into a black and white plain list of 1's and 0's
    #         width is enforced to 384 and padded with white if needed. """
    #     black_and_white_pixels = [0] * 147456
    #     #black_and_white_pixels = [1] * 384 * h
    #     if w > 384:
    #         print(f"Bitmap width too large: {w}. Needs to be under 384")
    #         return False
    #     elif w < 384:
    #         print(f"Bitmap under 384 ({w}), padding the rest with white")

    #     print(f"Bitmap size {w}")

    #     if type(pixels[0]) == int: # single channel
    #         print(" => single channel")
    #         for i, p in enumerate(pixels):
    #             if p < self.black_threshold:
    #                 black_and_white_pixels[int(i % w + i / w * 384)] = 0
    #             else:
    #                 black_and_white_pixels[int(i % w + i / w * 384)] = 1
    #     elif type(pixels[0]) in (list, tuple) and len(pixels[0]) == 3: # RGB
    #         print(" => RGB channel")
    #         for i, p in enumerate(pixels):
    #             if sum(p[0:2]) / 3.0 < self.black_threshold:
    #                 black_and_white_pixels[i % w + i / w * 384] = 0
    #             else:
    #                 black_and_white_pixels[i % w + i / w * 384] = 1
    #     elif type(pixels[0]) in (list, tuple) and len(pixels[0]) == 4: # RGBA
    #         print(" => RGBA channel")
    #         for i, p in enumerate(pixels):
    #             if sum(p[0:2]) / 3.0 < self.black_threshold and p[3] > self.alpha_threshold:
    #                 black_and_white_pixels[i % w + i / w * 384] = 0
    #             else:
    #                 black_and_white_pixels[i % w + i / w * 384] = 1
    #     else:
    #         print("Unsupported pixels array type. Please send plain list (single channel, RGB or RGBA)")
    #         print(f"Type pixels[0]: {type(pixels[0])}, haz {pixels[0]}")
    #         return False

    #     return black_and_white_pixels


    # def print_bitmap(self, pixels, w, h, output_png=False):
    #     """ Best to use images that have a pixel width of 384 as this corresponds
    #         to the printer row width.

    #         pixels = a pixel array. RGBA, RGB, or one channel plain list of values (ranging from 0-255).
    #         w = width of image
    #         h = height of image
    #         if "output_png" is set, prints an "print_bitmap_output.png" in the same folder using the same
    #         thresholds as the actual printing commands. Useful for seeing if there are problems with the
    #         original image (this requires PIL).

    #         Example code with PIL:
    #             import Image, ImageDraw
    #             i = Image.open("lammas_grayscale-bw.png")
    #             data = list(i.getdata())
    #             w, h = i.size
    #             p.print_bitmap(data, w, h)
    #     """
    #     counter = 0

    #     self.linefeed()

    #     # black_and_white_pixels = self.convert_pixel_array_to_binary(pixels, w, h)
    #     black_and_white_pixels = pixels
    #     print_bytes = []

    #     # read the bytes into an array
    #     for rowStart in range(0, h, 256):
    #         chunkHeight = 255 if (h - rowStart) > 255 else h - rowStart
    #         print_bytes += (18, 42, chunkHeight, 48)
    #         print(len(black_and_white_pixels))
    #         for i in range(0, 48 * chunkHeight):
    #             # read one byte in
    #             byt = 0
    #             for xx in range(8):
    #                 pixel_value = black_and_white_pixels[counter]
    #                 counter += 1
    #                 # check if this is black
    #                 if pixel_value == 0:
    #                     byt += 1 << (7 - xx)
    #                     if output_png: draw.point((counter % 384, round(counter / 384)), fill=(0, 0, 0))
    #                 # it's white
    #                 else:
    #                     if output_png: draw.point((counter % 384, round(counter / 384)), fill=(255, 255, 255))

    #             print_bytes.append(byt)

    #     # output the array all at once to the printer
    #     # might be better to send while printing when dealing with
    #     # very large arrays...
    #     for b in print_bytes:
    #         self.printer.write(chr(b))

    #     if output_png:
    #         test_print = open('print-output.png', 'wb')
    #         test_img.save(test_print, 'PNG')
    #         print("output saved to {test_print.name}")
    #         test_print.close()

if __name__ == '__main__':
    p = ThermalPrinter()
#     p.print_text("\nHello maailma. How's it going?\n")
#     p.print_text("Part of this ")
#     p.bold()
#     p.print_text("line is bold\n")
#     p.bold(False)
#     p.print_text("Part of this ")
#     p.font_b()
#     p.print_text("line is fontB\n")
#     p.font_b(False)
#     p.justify("R")
#     p.print_text("right justified\n")
#     p.justify("C")
#     p.print_text("centered\n")
#     p.justify() # justify("L") works too
#     p.print_text("left justified\n")
#     p.upsidedown()
#     p.print_text("upside down\n")
#     p.upsidedown(False)
# 
#     markup = """bl bold left
# ur underline right
# fc font b centred (next line blank)
# nl
# il inverse left
# """
#     p.print_markup(markup)
    
    print("trying image")
    
    try:
        # Print some .bmp bitmap images
        p.printBMPImage('notbad.bmp')
    except OSError as e:
        print(e.errno)
        pass
        
    print("tried image")
#     p.linefeed()
#     p.justify("C")
#     p.barcode_chr("2")
#     p.barcode("014633098808")
#     p.linefeed(3)


