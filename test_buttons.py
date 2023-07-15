from machine import Pin
import time

led = Pin(16, Pin.OUT)
led.value(False)
arcade_button = Pin(17, Pin.IN, Pin.PULL_DOWN)
button_1 = Pin(20, Pin.IN, Pin.PULL_DOWN)
button_2 = Pin(19, Pin.IN, Pin.PULL_DOWN)
button_3 = Pin(18, Pin.IN, Pin.PULL_DOWN)

while True:
    if arcade_button.value():
        led.toggle()
        print("Arcade Button pressed")
        time.sleep(0.5)
        led.toggle()
    if button_1.value():
        print("button_1 pressed")
        time.sleep(0.5)
    if button_2.value():
        print("button_2 pressed")
        time.sleep(0.5)
    if button_3.value():
        print("button_3 pressed")
        time.sleep(0.5)
