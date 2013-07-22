#import Printrun Stuff
import printcore
import pronsole
from printrun.printrun_utils import install_locale
from printrun import gcoder
install_locale('pronterface')

from printrun.GCodeAnalyzer import GCodeAnalyzer
from printrun import gcoder

import thread
from threading import Thread


class printer():
	def printerConnect(pi_id):
		print 'trying to connect to printer...'
		online == False
		port = '/dev/ttyACM0'#defines port name for arduino
		#^need to stop pi from locking port in /var/lock/LCK..ttyACM0
		#switches when switching printers?
		#gets locked everytime program is stopped w/'control z'
		baud = '115200'
		#it works but not consistently
		#Way to prompt printer to send back info?
		pron.p.connect(port, baud)
		while True:
			line=pron.p._readline()#reads output from printer, returns by line
			#^need to parse
			if (line == None) or (line == ''):
				break
			print (line)
			#Ultimaker only send back an ID when it wants :(
			#Marlin doesn't set a unique printer ID
			#not sure what this is
			if line.find('echo: External',0,len(line)) != -1:
				(before,sep,after)=line.partition('-')
				(b,s,a)=after.partition(' ')
				printer_printerId = b
				online = True
				break
				#this will always tell you when it's connected but comes before the possible ID
			elif (line != None) and (line != ''):#if its connected
			 	#printer_printerId = getPrinterID()
			 	printer_printerID = pi_id
			 	online = True
			 	break

		print "!!new printerId", printer_printerId

	def printFile(fileName):
		gcode = [i.strip() for i in open(filename)]#sends gcode line by line
		gcode = gcoder.GCode(gcode)
		###########################^this should probably be done server side
		pron.p.startprint(gcode) #calls method in printcore through pronsole only takes arrays
		#while printing
		#M105 - Read current temp
		#M117 - display message
		#	line=pron.p._readline()

	def do_cancel():
		pron.do_pause(port)
		pron.do_home("xye")
		pron.do_move("z 200")
		pron.do_settemp("0")
		#technically doesn't end the job but the printer is ready to take a new one

	def get_temp():
		pass
		#right code but doesn't send back consistant shit
		# tmp= None
		# pron.p.send('M105')
		# line=pron.p._readline()
		# split_line = line.split()
		# tmp=str(split_line[1])[2:len(split_time[1])]

if __name__ == '__main__':
	#define pronsole
	pron=pronsole.pronsole()
	#define printcore
	pron.p=printcore.printcore()