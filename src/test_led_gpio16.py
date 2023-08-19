from machine import Pin, PWM
import utime

led = PWM(Pin(16))
led.freq(1000)      # Set the frequency value
min_value = 25
max_value = 100
sleep_length = 50
led_duty_cycle = 500
led_value = 50       #LED brightness initial value
original_led_speed = 5      # Change brightness in increments of 5
led_speed = original_led_speed
if __name__ == '__main__':
    while True:                            
        led_value += led_speed           
        led.duty_u16(int(led_value * led_duty_cycle))     # Set the duty cycle, between 0-65535
        utime.sleep_ms(sleep_length)
        if led_value >= max_value:
            led_value = max_value
            led_speed = -original_led_speed
            utime.sleep_ms(sleep_length*sleep_length)
        elif led_value <= min_value:
            led_value = min_value
            led_speed = original_led_speed

