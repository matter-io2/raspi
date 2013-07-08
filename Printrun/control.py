#run pronsole to print script
import subprocess
from subprocess import Popen, PIPE
import sys
import os
import printcore
#to open serial port
import serial

if __name__ == "__main__":
	#print command
	#also connects at specified port and defaults to a baud rate of 115200
	fname = "Small_buddha.gcode"
	port = '/dev/ttyACM0'
	#p = subprocess.Popen(['python','printcore.py','-s', port ,fname], close_fds=True)
	#'-s' prints one line that updates the job % through
	#sys.stdout.write("Progress: 00.0%\r")

	#user control
	p=printcore.printcore()
	#p.connect(port,'115200')
	var = raw_input("Start print? (y/n)")
	if var == "y":
		#p.statusreport = True
		#p.startprint(fname)
		subprocess.Popen(['python','printcore.py','-s', port ,fname], close_fds=True)
	else:
		p.disconnect()
		sys.exit()
	var =raw_input("Cancel? (y/n)")
	if var == "y":
		p.disconnect()
		p.connect(port,'115200')
		p.send_now(port, 'M104 S0')
		p.send_now(port, 'G28')
		p.send_now(port, 'M84')
	else:
		pass
	p.disconnect()
	#terminate script after print
	sys.exit()
	#need close_fds=True to close the ports when the job is done or terminated