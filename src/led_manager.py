from machine import Pin, PWM
import utime
from printer_manager import is_printing

# Function to make the LED blink as an alert
def led_alert():
    led = PWM(Pin(16))
    led.freq(1000)
    min_value = 25
    max_value = 100
    sleep_length = 50
    led_duty_cycle = 500
    led_value = 50
    original_led_speed = 5
    led_speed = original_led_speed

    # Loop to make the LED brightness go up and down
    while is_printing():
        led_value += led_speed
        led.duty_u16(int(led_value * led_duty_cycle))
        utime.sleep_ms(sleep_length)
        if led_value >= max_value or led_value <= min_value:
            led_speed = -led_speed

    # Turn off the LED once printing is complete
    led.duty_u16(0)