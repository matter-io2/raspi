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

if __name__ == "__main__":
	p=pronsole.pronsole()
	#progress=0
	#while progress<100:
		#	progress = 100*float(p.p.queueindex)/len(p.p.mainqueue)
		#	progress = int(progress*10)/10.0 #limit precision
		#	print(str(progress)+"%")
		#	time.sleep(3) #can't use sleep() method
	p.do_monitor('/dev/ttyACM0')
	sys.exit()