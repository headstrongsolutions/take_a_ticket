# Import required libraries
from machine import Pin
import time
from state_manager import load_state, save_state
from display_manager import DisplayManager
from led_manager import led_alert
from printer_manager import print_ticket

# Load the current ticket and serving numbers from the saved state
ticket_number, serving_number = load_state()

# Initialize the display
display = DisplayManager()

# Define the pin connections for the various buttons
arcade_button = Pin(17, Pin.IN, Pin.PULL_DOWN)
button_1 = Pin(20, Pin.IN, Pin.PULL_DOWN)
button_2 = Pin(19, Pin.IN, Pin.PULL_DOWN)
button_3 = Pin(18, Pin.IN, Pin.PULL_DOWN)

# Display the initial serving number
display.update(serving_number)

# Start the main loop
while True:
    # If the arcade button is pressed, increment the ticket number and print a ticket
    if arcade_button.value():
        led_alert()  # Activate LED alert
        ticket_number += 1
        if ticket_number > 999:
            ticket_number = 1
        print_ticket(ticket_number)
        save_state(ticket_number, serving_number)  # Save the updated state
        time.sleep(0.5)
    
    # If button 1 is pressed, increment the serving number and update the display
    if button_1.value():
        serving_number += 1
        if serving_number > 999:
            serving_number = 1
        display.update(serving_number)
        save_state(ticket_number, serving_number)
        time.sleep(0.5)

    # If button 2 is pressed, decrement the serving number and update the display
    if button_2.value():
        serving_number -= 1
        if serving_number < 1:
            serving_number = 999
        display.update(serving_number)
        save_state(ticket_number, serving_number)
        time.sleep(0.5)
    
    # If button 3 is pressed, reset both the ticket and serving numbers
    if button_3.value():
        ticket_number = 0
        serving_number = 1
        display.update(serving_number)
        save_state(ticket_number, serving_number)
        time.sleep(0.5)
