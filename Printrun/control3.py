#run pronsole to print script
import subprocess
from subprocess import Popen, PIPE
import sys
import os
import pronsole
import time

import printcore
from printrun.printrun_utils import install_locale
from printrun import gcoder
install_locale('pronterface')

from printrun.GCodeAnalyzer import GCodeAnalyzer
from printrun import gcoder

from threading import Thread

def parseJSON(bodyString):
	global printer_inUse, job_process, job_progress, job_conclusion, job_num, job_id
	global cancelCmdTime, job_started
	bodyDict = json.loads(bodyString)
	print bodyDict


if __name__ == "__main__":
	#print command
	#also connects at specified port and defaults to a baud rate of 115200
	fname = "Small_buddha.gcode"
	port = '/dev/ttyACM0'
	#user control
	p= subprocess.Popen(['python','pronsole.py'], stdin=PIPE)#, stderr=PIPE stdout=subprocess.PIPE,
	p.stdin.write('connect')
	p.stdin.flush()
	var =raw_input("Print? (y/n)")
	if var == "y":
		p.stdin.write('load '+fname)
		p.stdin.flush()
		p.stdin.write('print')
		p.stdin.flush()
		p.stdin.write('monitor')
		p.stdin.flush()
	else:
		p.stdin.write('disconnect')
		p.stdin.flush()
		p.stdin.write('exit')
		p.stdin.flush()
	var =raw_input("Cancel? (y/n)")
	if var == "y":
		p.stdin.write('pause')
		p.stdin.flush()
		p.stdin.write('home')
		p.stdin.flush()
		p.stdin.write('move z 200')
		p.stdin.flush()
		p.stdin.write('settemp 0')
		p.stdin.flush()
	else:
		pass
	p.stdin.write('disconnect')
	p.stdin.flush()
	p.stdin.write('exit')
	p.stdin.flush()
	#terminate script after print
	sys.exit()
	#need close_fds=True to close the ports when the job is done or terminated