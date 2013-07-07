#!/usr/bin/env python

try:
	import RPi.GPIO as GPIO
	print "import worked"
except RuntimeError:
	print("Error importing RPi.GPIO!  This is probably because you need superuser priveleges.  You can achieve this by using sudo to run your script")
import time


GPIO.setmode(GPIO.BOARD)
print "set board mode"


#setup pin_modes
green = 8
blue = 10
red = 12
button = 16

GPIO.setup(red,GPIO.OUT)   #Red
GPIO.setup(green,GPIO.OUT)  #Green
GPIO.setup(blue, GPIO.OUT) #Blue
GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# set everything to OFF
GPIO.output(red,1)
GPIO.output(green,1)
GPIO.output(blue,1)

print "set pin 8,10,12 out"

color = [[0 for x in xrange(3)] for x in xrange(8)]
color[0] = [1,1,1]
color[1] = [0,1,1]
color[2] = [1,0,1]
color[3] = [1,1,0]
color[4] = [0,0,1]
color[5] = [1,0,0]
color[6] = [0,1,0]
color[7] = [0,0,0]
value = -1
index = 0

while 1:
    if value != GPIO.input(button):  #only act if there is a button change
	print ("button change!")
	value = GPIO.input(button)
	# remember
	# released ==1 --button has pull up resistor
	# pressed ==0 --ground wire shorted
	if value == 0 : 
	  c = color[0] # all off	  
	else: 
	  if index==8:
	    index = 0
	  c = color[index] # cache current led values
	  index = index+1
	  print c
	for i in range(3):# set led on/off
	  GPIO.output(red,c[0])
	  GPIO.output(green,c[1])
	  GPIO.output(blue,c[2])
    time.sleep(0.1)

GPIO.cleanup()
