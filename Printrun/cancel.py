#run pronsole to print script
import subprocess
from subprocess import Popen, PIPE
import sys
import os
import printcore

import serial
if __name__ == "__main__":
	#print command
	#also connects at specified port and defaults to a baud rate of 115200
	fname = "Small_buddha.gcode"
	port = "/dev/ttyACM0"

	#cancel command
	#pauses, sends commands to turn off temperature and go to home axis
	#commands from config end_gcode, it should accept all gcode ref /Printrun/printrun/GcodeAnalyzer.py
	# subprocess.call() is equivalent to using subprocess.Popen() and wait()
	p=printcore.printcore()
	p.disconnect()
	p.connect(port, '115200')
	p.send_now(port, 'M104 S0')
	p.send_now(port, 'G28')
	p.send_now(port, 'M84')
	#p = subprocess.Popen(['python','printcore.py', 'pause', port],close_fds=True)
	#turn off extruder
	#p = subprocess.call(['python','printcore.py', 'send_now', port,'M104 S0'],close_fds=True)
	#go to home axis
	#p = subprocess.call(['python','printcore.py', 'send_now', port,'G28'],close_fds=True)
	#disable motors
	#p = subprocess.call(['python','printcore.py', 'send_now', port,'M84'],close_fds=True)

	#Won't work b/c princore "Usage: python  printcore.py [-h|-b|-v|-s] /dev/tty[USB|ACM]x filename.gcode"
	#in pronsole.py
	#	pause, home xy, home e, settemp 0, move z 200
	#terminate script after print
	sys.exit()