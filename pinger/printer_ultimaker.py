import sys
import subprocess
sys.path.insert(0, '../Printrun')

#import Printrun Stuff
import printcore
import pronsole
from printrun.printrun_utils import install_locale
from printrun import gcoder
install_locale('pronterface')

from printrun.GCodeAnalyzer import GCodeAnalyzer
from printrun import gcoder

pron=pronsole.pronsole()
#define printcore
pron.p=printcore.printcore()

printer_printerID = ''

pi_id = None

class printer():
	def printer_Connect(self):
		global online
		global printer_printerID
		global pi_id
		print 'trying to connect to printer...'
		online = False
		port = '/dev/ttyACM0'#defines port name for arduino
		#port = '/dev/ttyACM1'
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
			# if line.find('echo: External',0,len(line)) != -1:
			# 	(before,sep,after)=line.partition('-')
			# 	(b,s,a)=after.partition(' ')
			# 	printer_printerID = b
			# 	online = True
			# 	break
			# 	#this will always tell you when it's connected but comes before the possible ID
			if (line != None) and (line != ''):#if its connected
			 	printer_printerID = self.get_unique_id()
			 	#printer_printerID = pi_id
			 	online = True
			 	break

		print "!!new printerId", printer_printerID
	def get_unique_id(self):
		p= subprocess.Popen('udevadm info -q all -n /dev/ttyACM0',shell=True,stdout=subprocess.PIPE)
		dev_info = p.communicate()
		splt = dev_info[0].split()
		for x in splt:
			if 'ID_SERIAL_SHORT=' in x:
				#print ('RETURNED: '+ x[x.find('=')+1:len(x)])
				return x[x.find('=')+1:len(x)]
				break

	def findPrinter(self, piID):
		global printer_printerID
		global pi_id
		pi_id = piID
		if printer_printerID == '' or printer_printerID == None:
			print 'trying to connect to printer...'
			online = False
			self.printer_Connect()
		else:
			return printer_printerID

	def print_File(self, fileName):
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

	#prints
	def do_monitor():
		#right code but doesn't send back consistant shit
		tmp= None
		pron.p.send('M105')
		#monitor in pronsole has  a "sleep(interval)"
		#needed? or does pron just have it b/c it loops the monitor
		line=pron.p._readline()
		print (line) #debugging
		#split_line = line.split()
		#tmp=str(split_line[1])[2:len(split_time[1])]
		#^still need to parse consistently
		if pron.p.printing:
			progress = 100*float(pron.p.queueindex)/len(pron.p.mainqueue)
			progress = int(progress*10)/10.0 #limit precision
			#prev_msg = str(progress) + "%"
			#prog=prev_msg.ljust(0) #"0" used to be prev_msg_len from control2.py
			print progress

if __name__ == '__main__':
	#define pronsole
	pron=pronsole.pronsole()
	#define printcore
	pron.p=printcore.printcore()