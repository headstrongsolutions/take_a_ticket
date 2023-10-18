from Adafruit_Thermal import *

# Function to print a ticket with a specific number
def print_ticket(ticket_number):
     printer = Adafruit_Thermal()
     # Initialize printer settings
     printer.wake()
     printer.setDefault()
     printer.justify('C')
     # Header: "Please Take Ticket"
     printer.setSize('M')  # Medium size
     printer.boldOn()  # Bold text for emphasis
     printer.println("################################")
     printer.println("")
     printer.println("Please Take Ticket")
     printer.boldOff()
     # Space
     printer.println("")
     # Ticket Number
     printer.setSize('L')  # Large size
     printer.doubleHeightOn()  # Make text double height
     printer.boldOn()  # Bold text for emphasis
     printer.println(f"{ticket_number:03}")
     printer.boldOff()
     printer.doubleHeightOff()
     # Space
     printer.println("")
     # Footer: "wait for your number"
     printer.setSize('M')  # Medium size
     printer.boldOn()  # Bold text for emphasis
     printer.println("wait for your tickets turn.")
     printer.println("")
     printer.println("################################")
     printer.boldOff()
     # Finalize
     printer.feed(3)  # Feed 3 lines for spacing
     printer.sleep()  # Save some power