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

import thread
from threading import Thread

def parseJSON(bodyString):
	global printer_inUse, job_process, job_progress, job_conclusion, job_num, job_id
	global cancelCmdTime, job_started
	bodyDict = json.loads(bodyString)
	print bodyDict

def do_print(port,pron,piperead,pipewrite):
	var = raw_input("\n"+"Start print? (y/n)")
	if var == "y":
		#p.do_load(fname)
		gcode = [i.strip() for i in open(fname)]
		gcode = gcoder.GCode(gcode)
		p.p.startprint(gcode) #calls method in printcore through pronsole only takes arrays
		#pid = os.fork()#fork may fuck everything up, so take this condtion out if shit gets cray
		#if pid:
		thread.start_new_thread(mon, (port,p,pipewrite))
		#else:
		#thread.start_new_thread(display_pipe, (port, piperead))
	else:
		p.do_disconnect(port)
		sys.exit(port)
def do_cancel(port,pron):
	var =raw_input("\n"+"Cancel? (y/n)")
	if var == "y":
		p.do_pause(port)
		p.do_home("xye")
		p.do_move("z 200")
		p.do_settemp("0")
		#technically doesn't end the job but the printer is ready to take a new one
		#p,do_exit(port) fully ends the print job and disconnects
		p.do_disconnect(port)
		p.do_exit(port)
	else:
		p.do_disconnect(port)
		p.do_exit(port)
		#terminate script after print
	sys.exit()
	#need close_fds=True to close the ports when the job is done or terminated

def mon(port,pron,pipewrite):
	os.close(piperead)#gonna try this shit in the threaded function so it leaves the rest of my shit alone
	#notopen yet?
	pipewrite=os.fdopen(pipewrite, 'w')
	interval = 5
	if not pron.p.online:
		print(_("Printer is not online. Please connect to it first."))
		return
	if not (pron.p.printing or pron.sdprinting):
		print(_("Printer is not printing. Please print something before monitoring."))
		return
	#print(_("Monitoring printer, use ^C to interrupt."))
	pron.monitoring = 1
	prev_msg_len = 0
	try:
		while True:
			pron.p.send_now("M105")
			time.sleep(interval)
			if pron.p.printing:
				progress = 100*float(pron.p.queueindex)/len(pron.p.mainqueue)
			else:
				print("Done Monitoring")
				sys.exit()
				break
			progress = int(progress*10)/10.0 #limit precision
			prev_msg = str(progress) + "%"
			prog=prev_msg.ljust(prev_msg_len)
			#if pron.silent == False:
			#	sys.stdout.write("\r" + prev_msg.ljust(prev_msg_len))
			sys.stdout.write("\r"+"stdout:"+prog)
			sys.stdout.flush()
			#os.write(pipewrite, "\r"+prog)#writes to pipe "pipewrite"
			prev_msg_len = len(prev_msg)
	except KeyboardInterrupt:
		#if pron.silent == False: print _("Done monitoring.")
		pass
	pron.monitoring = 0

def display_pipe(port,stream):
	print ("The pipe was passed")
	while True:
		os.close(pipewrite)#gonna try this shit in the threaded function so it leaves the rest of my shit alone
		stream=os.fdopen(piperead,'r')
		#stream = os.fdopen(stream)
		out = stream.readline() #only reading first line of pipe
		if out == '':
			sys.exit()
			break
		sys.stdout.write("\n"+"Pipe:"+out)
		sys.stdout.flush()
	print("The Pipe is done")

if __name__ == "__main__":
	piperead,pipewrite=os.pipe()
	#print command
	#also connects at specified port and defaults to a baud rate of 115200
	fname = "PC.gcode"
	port = '/dev/ttyACM0'
	#user control
	p=pronsole.pronsole()
	p.do_connect(port)#port not needed? it should scan for an open port

	do_print(port,p,piperead,pipewrite)
	#Thread(target=parseJSON, name='print-progress-'+str(job.id), arggs=(job,proc.stdout)).start()

	do_cancel(port, p)
