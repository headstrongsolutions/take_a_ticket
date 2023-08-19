from Adafruit_Thermal import *

def print_ticket(ticket_number: int):
     printer = Adafruit_Thermal(heatdots=15, heatinterval=80)
     printer.println("")
     printer.inverseOff()
     printer.justify('C')
     printer.setSize('S')
     printer.println("################################")
     printer.println("")
     printer.println("Take your ticket")
     printer.println("")
     printer.setSize('L') # doesnt work for some weird reason
     printer.doubleHeightOn()
     printer.boldOn()
     printer.print(f"{ticket_number:03}")
     printer.println("")
     printer.boldOff()
     printer.doubleHeightOff()
     printer.setSize('S')
     printer.println("")
     printer.println("Wait till your tickets turn")
     printer.println("")
     printer.println("################################")
     printer.feed(3)



