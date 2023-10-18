# Import the necessary libraries
from machine import Pin
import time
from state_manager import load_state, save_state
from display_manager import DisplayManager
from led_manager import led_alert
from printer_manager import print_ticket
from config import *

class TicketManager:
    # Initialize the ticket manager
    def __init__(self):
        # Load the current ticket and serving numbers from the saved state
        self.ticket_number, self.serving_number = load_state()
        # Initialize the display
        self.display = DisplayManager()
        # Setup the GPIO pins for the buttons
        self.setup_pins()
        # Display the current serving number
        self.display.update(self.serving_number)
    # Initialize the pins for the arcade button and other control buttons.
    def setup_pins(self):
        self.arcade_button = Pin(ARCADE_BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
        self.button_1 = Pin(BUTTON_1_PIN, Pin.IN, Pin.PULL_DOWN)
        self.button_2 = Pin(BUTTON_2_PIN, Pin.IN, Pin.PULL_DOWN)
        self.button_3 = Pin(BUTTON_3_PIN, Pin.IN, Pin.PULL_DOWN)

    # Check if the arcade button is pressed and process the ticket request.
    def handle_arcade_button(self):
        if self.arcade_button.value():
            led_alert()
            self.ticket_number += 1
            if self.ticket_number > 999:
                self.ticket_number = 1
            print_ticket(self.ticket_number)
            save_state(self.ticket_number, self.serving_number)
            time.sleep(0.5)

    # Check if the button 1 is pressed and increment the serving number.
    def handle_button_1(self):
        if self.button_1.value():
            self.serving_number += 1
            if self.serving_number > 999:
                self.serving_number = 1
            self.display.update(self.serving_number)
            save_state(self.ticket_number, self.serving_number)
            time.sleep(0.5)

    # Check if the button 2 is pressed and decrement the serving number.
    def handle_button_2(self):
        if self.button_2.value():
            self.serving_number -= 1
            if self.serving_number < 1:
                self.serving_number = 999
            self.display.update(self.serving_number)
            save_state(self.ticket_number, self.serving_number)
            time.sleep(0.5)

    # Check if the button 3 is pressed and reset the ticket number and serving
    def handle_button_3(self):
        if self.button_3.value():
            self.ticket_number = 0
            self.serving_number = 1
            self.display.update(self.serving_number)
            save_state(self.ticket_number, self.serving_number)
            time.sleep(0.5)
    # Run the ticket manager
    def run(self):
        while True:
            self.handle_arcade_button()
            self.handle_button_1()
            self.handle_button_2()
            self.handle_button_3()
