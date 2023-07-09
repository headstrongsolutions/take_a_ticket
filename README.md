# Take A Ticket

<img src="header.png" />

## Overview

So, you know those times when someone turns up at your desk and either just hovers there till you're ready, or breaks your flow when you're in teh middle of something?
Even worse is when you're already talking to someone and they just cut in as if they have the power to somehow automatically know out of the two conversations which one holds the precedence?
..ever wish you could actually have a ticket machine so you can say 'take a ticket' and point to it?

Well here it is.

## Setting up, playing around and testing

## Micropython

The Pico should be flashed with MicroPython (perfect for a good cobbling), you can find it here:

 - Pico https://micropython.org/download/rp2-pico/
 - Pico W https://micropython.org/download/rp2-pico-w/

Download the latest .uf2 for either a Pico or a Pico-W (if it has wifi it's a Pico-W), hold the button down on the Pico, then plug in the USB. Copy and Paste the .uf2 file you downloaded to the new usb drive that just appeared and when it's finished copying over the Pico will reboot into MicroPython mode, simple as that.

### Thonny

There's more than enough tutorials out there for this, but short story, install the latest version of Thonny you can lay hands on, run it, in `Run`->`Configure Interpreter` menu item go to the `Interpreter` tab, set the top dropdown to `MicroPython (Raspberry Pi Pico)`.

To upload a file from this repo to a Pico, open it in Thonny then select the menu item `File`->`Save Copy`, pick `Raspberry Pi Pico` then save it as the same name.
To run a Python file on the Pico, open it (either locally from a file or from teh Pico itself) simply have it as the active open file and press Run (or F5).
To edit a file open it from the Pico, make the changes and save it again, it will automatically save to the Pico. 

### VSCode

For this I think the `Pico_W_Go` extension might be perfect: https://marketplace.visualstudio.com/items?itemName=paulober.pico-w-go 
... however, I have a SteamDeck which is being a little nightmare at the moment, I can't get access to the Serial port that a Pico raises, however this solution does have `Pico_W_Go` VSCode settings embedded into it, so your mileage may vary, it might work for you, it might not.
...and before someone chips in with 'you *did* run the `scripts/permissiosnSolver.sh` didn't you?' yes, yes I did, but it doesn't persist.

Until I get that sorted I strongly suggest using Thonny as described above.

## List of Materials

Not a 'Bill of Materials' because this is just cobbled together, find the cheapest versions.
 
 - Raspberry Pico (W or old school, it doesn't matter, we don't need any wireless where we're going)
 - E-Paper display (we used a Waveshare 2.13 PHat, because it was cheap and had nice breakouts fo the SPI pins)
 - Button (we used a LED backlit transparent one, because it was pretty)
 - Serial/TTY Thermal Printer (we got the cheapest we could find that had a serial connection)
 - 3 X generic tactile switches 

### E-Paper finaglery

Just basic text is fine on a E-Paper if you're happy with the font being 8 pixels high, but we are not. The current ticket number must be as readable as possible, so we need to use some extra cleverness to use 'fonts'. The fonts can be created using PeterHinh's very excellent `font_to_py` python application: https://github.com/peterhinch/micropython-font-to-py
The documentation there is remarkably good, but short version would be I got the Days font from dafont: https://www.dafont.com/days.font and then I used `font_to_py` against it to create two sizes of the font at 10 pixels and 75 pixels height using the following in cli:
 - python font_to_py.py -x days.ttf 75 days_font_83.py -c 1234567890 days_font_83.py
 - python font_to_py.py -x days.ttf 10 days_font_10.py

 Explanation of the `font_to_py` switches:
  - -x renders the font horizontally
  - -c 1234567890 causes only the numbers 0-9 to be rendered, these are the only characters I need so best to save file space

  So, when we have the python fonts these can be uploaded to the board and imported in as libraries in the normal fashion.

  Then to actually use them we can use the main Waveshare library to setup the E-Paper module itself, then halfway through the process create a sub-frame buffer that can then be mixed with Peter Hinch's other very excellent library `writer`. 
  This library is best thought of as a middleware for a framebuffer, it enables you to do additional things to it that you don't get out of the box. This is preffered here as it means we don't need to break out the big guns on an expensive canvassing framework like `Pillow` etc.. and no that's not a slight, I love using `Pillow`, it's very natural but literally the only thing that `frameBuffer` doesn't give us is pixel fonts.

#### Pins

This may well not be the same for anything other than the Waveshare 2.13 V3 PHat, do your research.
The following table was taken from : https://www.waveshare.com/wiki/Pico-ePaper-2.13

| E-Paper | Pico | Description |
|---|---|---|
| VCC | VSYS | Power input |
| GND | GND | Ground |
| DIN | GP11 | MOSI pin of SPI interface, data transmitted from Master to Slave. |
| CLK | GP10 | SCK pin of SPI interface, clock input |
| CS | GP9 | Chip select pin of SPI interface, Low Active |
| DC | GP8 | Data/Command control pin (High: Data; Low: Command) |
| RST | GP12 | Reset pin, low active  |

<img src="https://www.raspberrypi.com/documentation/microcontrollers/images/pico-pinout.svg" />

*Raspberry Pico Pinout sheet from raspberrypi.com*

<img src="https://www.waveshare.com/img/devkit/LCD/Pico-ePaper-2.13/Pico-ePaper-2.13-details-inter.jpg" />

*This waveshare model is not the 2.13 PHat version I used, but the pinout is identical*

So we now have a E-Paper display that can display some text in a font and size we specify. That's one half of the heavy lifting and leaves us with:

- LED backed button: lets have a pretty `breathe` animation when the unit is printing a ticket, otherwise the LED is turned off, LED Pin will be GPIO 16
- 3 tac buttons, button 1 resets the ticket number to 000, therefore when the button is next pressed it prints 001, button 2 decreases the number, button 3 increases the number
- Serial Thermal Printer - TBD (still on the long boat from AliExpress)