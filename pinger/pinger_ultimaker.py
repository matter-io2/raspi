# this is Drew's change!!!  booya
#comment #2

#what drew's script does now
# - connect,print,cancel

# next steps
# - create or generate a unique id for arduino
# - 
# - 
import sys
sys.path.insert(0, '../Printrun')

from cookielib import CookieJar
from twisted.internet import reactor,task,endpoints
from twisted.web.client import Agent, CookieAgent, ResponseDone
from twisted.web.http_headers import Headers
from twisted.internet.protocol import Protocol, Factory
from twisted.internet.defer import Deferred
from twisted.web.client import FileBodyProducer
import time
from time import time
import urllib
import simplejson as json

import os
import subprocess

from zope.interface import implements
from twisted.internet.defer import succeed
from twisted.web.iweb import IBodyProducer

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

#define pronsole
pron=pronsole.pronsole()
#define printcore
pron.p=printcore.printcore()

#globals for drew to manipulate
printer_profile = 0 # type of machine
printer_firmware = 0 # i.e. 700 for makerbot firmware 7.0
printer_printerId = '' # unique id from makerbot json
printer_inUse = False  # is printer doing something
printer_tool1_temp = -1 
printer_tool2_temp = -1
printer_bed_temp = -1
online = False # 'CONNECTED', 'DISCONNECTED'


job_process = 'idle' # idle, verify, or print=
job_progress = -1 # % progress
job_conclusion = '' # 'ENDED','CANCELED','FAILED' 
job_fail_msg = ''   # error message when something fails to be reported to server for online debug w/o screen

#globals that don't need changing
pi_id = 'ASDF1234'

job_filename = '' #
job_id = '' # unique job id passed from the server, used to see if a new job has come up
job_started = False # internal
ip_address = ''     # lan ip 
job_num = -1  #  local job id used to cancel jobs in makerbot driver -> (def) -1, read from jobadded or jobchanged in UNIXsocket

#website comm utility
# From: http://twistedmatrix.com/documents/current/web/howto/client.html
class StringProducer(object): 
	implements(IBodyProducer)

	def __init__(self, body):
		self.body = body
		self.length = len(body)

	def startProducing(self, consumer):
		consumer.write(self.body)
		return succeed(None)

	def pauseProducing(self):
		pass

	def stopProducing(self):
		pass
	
#website comm utility
# From: http://twistedmatrix.com/documents/current/web/howto/client.html
class BeginningPrinter(Protocol):
	def __init__(self, finished,remaining):
		self.finished = finished
#		self.remaining = remaining
		self.display = ''
	def dataReceived(self, bytes):
#		if self.remaining:
			self.display += bytes
#			self.remaining -= len(bytes[:self.remaining])

	def connectionLost(self, reason):
		if reason.getErrorMessage().startswith('Response body fully received'):
			self.finished.callback(self.display)
		else:
			print reason.printTraceback()

#gets lan ip address
# From: http://cagewebdev.com/index.php/raspberry-pi-showing-some-system-info-with-a-python-script/
def get_ipaddress():
	global ip_address
	#Returns the current IP address
	arg='ip route list'
	p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
	data = p.communicate()
	split_data = data[0].split()
	if 'src' in split_data:
		ip_address = split_data[split_data.index('src')+1]
		print 'LAN IP Address:' + str(ip_address)
	else:
		print 'no LAN IP address assigned - missing "src" key'

#sends information to the website		
def makeRequest(status):
	global printer_profile, printer_firmware, printer_printerId, printer_inUse, online
	global printer_tool1_temp, printer_tool2_temp, printer_bed_temp

	global job_num, job_process, job_progress, job_conclusion
	global pi_id
	
# debugger that shows what is being posted to the server (see agent.request for actual posting)	
	print 'Data Sent:',urllib.urlencode({'type':'update',
														'online':online,
														'ipAddress':ip_address,
														'printer_profile':printer_profile,
														'printer_firmware':printer_firmware,
														'printer_printerId':printer_printerId,
														'printer_inUse':printer_inUse,
														'printer_tool1_temp':printer_tool1_temp,
														'printer_tool2_temp':printer_tool2_temp,
														'printer_bed_temp':printer_bed_temp,
														'pi_id':pi_id,
														'job_id':job_id,
														'job_process':job_process,
														'job_progress':job_progress,
														'job_conclusion':job_conclusion,
														'job_fail_msg':job_fail_msg,
														'status':status})
	# print 'Data Sent'
# posts information to server
	d = agent.request(	'POST',  
						'http://matter.io/printerPing/',
						Headers({'Content-Type': ['application/x-www-form-urlencoded']}),
						StringProducer(urllib.urlencode({'type':'update',
														'online':online,
														'ipAddress':ip_address,
														'printer_profile':printer_profile,
														'printer_firmware':printer_firmware,
														'printer_printerId':printer_printerId,
														'printer_inUse':printer_inUse,
														'printer_tool1_temp':printer_tool1_temp,
														'printer_tool2_temp':printer_tool2_temp,
														'printer_bed_temp':printer_bed_temp,
														'pi_id':pi_id,
														'job_id':job_id,
														'job_process':job_process,
														'job_progress':job_progress,
														'job_conclusion':job_conclusion,
														'job_fail_msg':job_fail_msg,
														'status':status}))
					)
	
	# d.addCallback(cbRequest, cookieJar)
	# filename = '/home/pi/webcam/printer.jpg'
	# body = FileBodyProducer('/home/pi/webcam/printer.jpg')
	# with open(filename) as imageOut:
	# 	c = agent.request(	'POST',  
	# 						'http://matter.io/webcamUpload/',
	# 						Headers({'Content-Type': ['application/form-data']}),
	# 						FileBodyProducer(imageOut)
	# 					)

	print 'Request Sent' # debug output
# queue's up next method	
	d.addCallback(cbRequest, cookieJar)

#data sent back from server
def cbRequest(response, cookieJar):
	print 'Response Code:', response.code

	headersDict = {}
	for i in response.headers.getAllRawHeaders():
#		print i
		headersDict[i[0]] = i[1]
	
	finished = Deferred()
	if response.code == 500:
		# f = open(logFile_4Tobe.txt)
		# f.write(response)

		response.deliverBody(BeginningPrinter(finished,response.length))
		finished.addCallback(print500Response)
	
	if response.code == 200 and headersDict['Content-Type'][0] == 'application/json':
		response.deliverBody(BeginningPrinter(finished,response.length))
		finished.addCallback(parseJSON)


	return response

cancelCmdTime = time()


#parses json string from server
def parseJSON(bodyString):
	global printer_inUse, job_process, job_progress, job_conclusion, job_num, job_id
	global cancelCmdTime, job_started
	bodyDict = json.loads(bodyString)
	print bodyDict
	# this is the Json packet from the server
	job_cancel = False
	if bodyDict.has_key('job_id'):  
	# this is the 
		if bodyDict['job_id'] == job_id: 
		# job_ids match!
			if bodyDict.has_key('job_cancelCmd') and bodyDict['job_cancelCmd'] == True and printer_inUse:
				job_cancel = True
		else:
		#new job_id don't match or
			job_id = bodyDict['job_id']
			job_process = 'idle'
			job_progress = 0
			job_conclusion = '' #default value when job has not concluded (used above)
			job_started = False
			#need to keep job_num for cancel command
			if job_id != '': # not nitial value
				#delete current job
				job_cancel = True
		#Cancel job (currentJob or previous job that was left running)
	else:
		if printer_inUse:
			job_cancel = True
	if job_cancel and int(job_num) >= 0:
		dif = time()-cancelCmdTime
		if int(dif) > 10: # timeout... not sure if it's working
#DREW
# cancel job command

			#makeCmdlineReq('hello')  # handshake!  
			#makeCmdlineReq('canceljob',{'id':job_num})  # kills job [id]
			pron.do_pause(port)
			pron.do_home("xye")
			pron.do_move("z 200")
			pron.do_settemp("0")
			#technically doesn't end the job but the printer is ready to take a new one
			job_num = -1 # important to say new job has not yet been added 
#DREW - END

			# makeCmdlineReq('hello')  # handshake!  
			# makeCmdlineReq('getjob',{'id':job_num})  # kills job [id]		
	#print gcode if there is a url 
	#and the job hasn't started
	if bodyDict.has_key('url') and bodyDict['url'] != 'none': 
		if not printer_inUse and not job_started: 
		#debug this logic soon
			print 'New URL:', bodyDict['url']
			job_started = True # prevents another call to download and print
			downloadFile(bodyDict['url'])


import downloader.downloader as dl

def downloadFile(url):
	global job_filename
	agent = Agent(reactor)
	print "In Download File:",url

	job_fileName = url.split('/')[-1]
	if url != None:
		d = dl.downloadFile(url,agent)
		d.addCallback(printFile)

import printer.printer as p

def printFile(fileName):

	print 'In PrintFile',fileName  # shows file path
	#determine which slicer was used...
# 	slicer = "miraclegrue" 
# 	with open(fileName) as fileIn:
# 		for i in range(15):
# 			line = fileIn.readline()
# 			if line.find("Skeinforge") > 0:
# 				slicer = "skeinforge"
#DREW-start
# print command goes here

	filename = '/home/pi/Printrun/Small_buddha.gcode'
	#reprap print function here
	gcode = [i.strip() for i in open(fname)]#sends gcode line by line
	gcode = gcoder.GCode(gcode)
	pron.p.startprint(gcode) #calls method in printcore through pronsole only takes arrays

#DREW- end

#LIGHTS - fLASH GREEN WHEN GOING

def findPrinter_and_Ip():
	global printer_profile, printer_firmware, printer_printerId 
	if printer_printerId == '':
		print 'trying to connect to printer...'
		online == False
#DREW-start
# connect to printer

		#makeCmdlineReq('hello')  # handshake!  
		#makeCmdlineReq('connect',{'machine_name':None ,'port_name':None , 'persistent':'true','profile_name':'Replicator2' ,'driver_name':'s3g'})  # gets printer properties! 
		# print '!!new printerId', printer_printerId
		port = '/dev/ttyACM0'#defines port name for arduino
		#^need to stop pi from locking port in /var/lock/LCK..ttyACM0
		#gets locked everytime program is stopped w/'control z'
		baud = '115200'
		#thread.start_new_thread(pron.do_connect, (port,))#run it in a seperate thread
		#thread.start_new_thread(pron.p.connect,(port,baud))
		pron.p.connect(port, baud)
		while True:
			line=pron.p._readline()#reads output from printer, returns by line
			#^need to parse
			if (line == None) or (line == ''):
				break
			if line.find('Echo: External',0,len(line)) != -1:
				(before,sep,after)=line.partition('-')
				(b,s,a)=after.partition(' ')
				printer_printerId = b
				break
			elif line.find('ok',0,len(line)):#if its connected
				printer_printerId = "Batman"
				print "The Printer has no ID, it's a phantom of the night"
			print (line)

		print "!!new printerId", printer_printerId

#DREW-end

	if ip_address == '':
		get_ipaddress()

def print500Response(bodyString):
	print bodyString

# def makeCmdlineReq(cmd,params = {}):
# 	unixEndPoint = endpoints.UNIXClientEndpoint(reactor, '/home/pi/raspi/makerbot/conveyor/conveyord.socket')
# 	newCmdReq = CmdlineReqFactory()
# 	newCmdReq.cmd = cmd
# 	newCmdReq.params = params
# 	unixEndPoint.connect(newCmdReq)
# 	print cmd
# 	print params

# global currentCommand
# class CmdlineReqProtocol(Protocol):
# 	def connectionMade(self):
# 		global currentCommand
# 		self.cmd = self.factory.cmd
# 		self.params = self.factory.params
# 		outDict = {}
# 		if self.cmd == 'hello':
# 			outDict['id'] = 0
# 		elif self.cmd == 'connect' or self.cmd == 'canceljob' or self.cmd == 'getjob':
# 			outDict['id'] = 1
# 		outDict['params'] = self.params
# 		outDict['jsonrpc'] = '2.0'
# 		outDict['method'] = self.cmd
# 		currentCommand = self.cmd
# 		print 'current command is',currentCommand

# 		self.transport.write(json.dumps(outDict))

# 	def dataReceived(self,data):
# 		global currentCommand
# 		global printer_profile, printer_firmware, printer_printerId, printer_inUse, online
# 		print 'CmdLineReq Received:',data

# # add data stream parser
# 		if '}{' in data:
# 			parsed = True
# 			# print '\n\n splitting data \n\n'
# 			data = data.split('}{')
# 			count = 0
# 			for i in range(len(data)):
# 				if i == 0:
# 					data[0] = data[0] + '}'
# 				elif i == len(data) - 1:
# 					data[len(data)-1] = '{' + data[len(data)-1]
# 				else:
# 					data[i] = '{' + data[i] + '}'
# 		else:
# 			data = [data]

# 			# data = [data_array[0]+'"}' , '{' + data_array[1]]  #save only first data chunk

# 		for msg in data:
# 			print 'unpacking msg from cmdlineReq'
# 			cmdResponseData = json.loads(msg)
# 			if cmdResponseData.has_key('error'):
# 				print 'error while executing ', currentCommand
# 				print 'error feedback:',cmdResponseData['error']
# 				print 'error code = ', cmdResponseData['error']['code']
# 				if cmdResponseData['error']['data'].has_key('name') and cmdResponseData['error']['data']['name'] == 'NoPortsException':
# 					print 'USB DISCONNECTED!\n\n\n\n\n\n\n'
# 					online = False
# 				if cmdResponseData['error'].has_key('name'):
# 					print '\n\tErrorName:\t'+str(cmdResponseData['error']['name'])
# 					#'UnknownJobError' if job is not available

# 			elif cmdResponseData.has_key('result'):
# 				online = True
# 				if cmdResponseData['id'] == 1:  # this works for everything but print [file] where the print function is id=2 (3rd cmd)
# 					print 'response id = 1, unpacking info'
# 					print currentCommand
# 					if currentCommand == 'connect':
# 						print 'printer recognized, saving information'
# 						printer_profile = cmdResponseData['result']['profile_name']
# 						printer_firmware = cmdResponseData['result']['firmware_version']
# 						printer_printerId = cmdResponseData['result']['name'].split(':')[-1]
# 						printer_tool1_temp = cmdResponseData['result']['temperature']['tools']['0'] #1st tool
# 						if printer_profile == 'Replicator2X':
# 							printer_bed_temp = cmdResponseData['result']['temperature']['heated_platforms']['0']
# 							printer_tool2_temp = cmdResponseData['result']['temperature']['tools']['1'] # 2nd tool
# 						print 'printer:'
# 						print '\tprofile\t\t', printer_profile
# 						print '\tfirmware \t', printer_firmware
# 						print '\tid\t\t', printer_printerId
# 						print '\textruder Temp\t', printer_tool1_temp

# 					elif currentCommand == 'canceljob': # following cancel command
# 						#think job was canceled
						
# 						#only add this if it's going to link directly to job_num and job_id (respectively)
# 						#makeCmdlineReq('hello')  # handshake!  
# 						#makeCmdlineReq('getjob',{'id':job_num})  # kills job [id]			
# 						pass

# 					elif currentCommand == 'getjob': # following cancel command

# 						#only add this if it's going to link directly to job_num and job_id (respectively)
# 						# job_conclusion = cmdResponseData['params']['conclusion']
# 						pass
# 					currentCommand = ''

# 			else:
# 				print '\n\n\n\n\n\n Unknown response to command - did not contain "error" or "result" keys \n\n\n\n\n\n'



# 		#reset current Command
# 		self.transport.loseConnection()

# class CmdlineReqFactory(Factory):
# 	protocol = CmdlineReqProtocol

import traceback

#passive listener watching the printer feedback (temp, events, etc.)
# class UnixSocketProtocol(Protocol):
# 	def connectionMade(self):
# 		print 'Unix Socket Connected'
# 		self.factory.conn = self

# 	def dataReceived(self, data):
# 		global printer_profile, printer_firmware, printer_printerId, printer_inUse, online
# 		global printer_tool1_temp, printer_tool2_temp, printer_bed_temp
# 		global job_filename, job_process, job_progress, job_conclusion, job_num
# 		global pi_id
# 		global job_fail_msg

# 		# DEBUG - supressing json output
# 		# print 'PRINTER SOCKET:',
# 		# print '\n'.join([l.rstrip() for l in data.splitlines()])

# 		#jsonDebug 
# 		#enable this to view the intermediate json stream
# 		# self.factory.parent.transport.write(data)

# 		# split up multiple data packets coming back in one chunk
# 		parsed = False
# 		if '}{' in data:
# 			parsed = True
# 			# print '\n\n splitting data \n\n'
# 			data = data.split('}{')
# 			count = 0
# 			for i in range(len(data)):
# 				if i == 0:
# 					data[0] = data[0] + '}'
# 				elif i == len(data) - 1:
# 					data[len(data)-1] = '{' + data[len(data)-1]
# 				else:
# 					data[i] = '{' + data[i] + '}'
# 		else:
# 			data = [data]

# 			# data = [data_array[0]+'"}' , '{' + data_array[1]]  #save only first data chunk

# 		for msg in data:
# 			printerData = json.loads(msg)
# 			# else:
# 			# 	printerData = json.loads(data)
# 			print msg
# 			if not printerData.has_key('method'):
# 				return
# 			if printerData['method'] == 'jobadded':
# 				printer_inUse = True
# 				job_num = printerData['params']['id']
# 				job_progress = 0
# 				job_conclusion = ''

# 			if printerData['method'] == 'jobchanged':
# 			# get progress, printerId

# 				if job_num == printerData['params']['id']:
# 					# doesn't need to be saved... because they match!
# 					# job_num = printerData['params']['id']
# 					print '\nDEBUG'
# 					print 'job_num matched - saving data\n'

# 					if printerData['params']['state'] == 'RUNNING':
# 						printer_inUse = True
# 						job_process = printerData['params']['progress']['name']
# 						job_progress = printerData['params']['progress']['progress']
# 						job_conclusion = ''
# 						# if job_process == 'print' or job_process == 'heatup':
# 						# 	#clean up - delete this and move to server side
# 						# 	#this should change to be just below the desired temperature passed from the server
# 						# 	if printer_tool1_temp <220:
# 						# 		job_process = 'heatup'
# 						# 	else:
# 						# 		job_process = ''
# 					elif printerData['params']['state'] == 'STOPPED':
# 						print '\n job state STOPPED \N'
# 						job_conclusion = printerData['params']['conclusion']
# 						printer_inUse = False
# 						if printerData['params']['failure']:
# 							if printerData['params']['failure'].has_key('exception') and printerData['params']['failure']['exception'].has_key('message'):
# 								job_fail_msg = printerData['params']['failure']['exception']['message']
# 				else:
# 					print '\njob_num mismatch - not saving any info\n'

# 			elif printerData['method'] == 'machine_state_changed':
# 			# get printerId, firmware, profile
# 				if printerData['params']['state'] == 'DISCONNECTED':
# 					online = False
# 					printer_printerId = ''
# 				elif printerData['params']['state'] == 'IDLE':
# 					#reseting info after job is finished
# 					printer_inUse = False 
# 				else:
# 					printer_profile = printerData['params']['profile_name']
# 					printer_firmware = printerData['params']['firmware_version']
# 					printer_printerId = printerData['params']['name'].split(':')[-1]
# 					if printer_tool1_temp == -1 and printerData['params']['temperature']['tools'].has_key('0'):
# 						printer_tool1_temp = printerData['params']['temperature']['tools']['0'] # get first tool if first value hasn't been saved

# 			elif printerData['method'] == 'machine_temperature_changed':
# 			# get printerId and tool_temps
# 			# measure tool1 temp for all machines - Rep2 and Rep2X
# 				if printerData['params']['state'] == 'IDLE':
# 					printer_inUse = False


# 				printer_tool1_temp = printerData['params']['temperature']['tools']['0'] #1st tool
# 				if printer_profile == 'Replicator2X':
# 					printer_bed_temp = printerData['params']['temperature']['heated_platforms']['0']
# 					printer_tool2_temp = printerData['params']['temperature']['tools']['1'] # 2nd tool

# 			elif printerData['method'] == 'port_detached':
# 				online = False
# 				printer_inUse = False
# 				printer_profile = 0
# 				printer_printerId = ''
# 				printer_firmware = 0

# 			elif printerData['method'] == 'port_attached':
# 				print 'printer port recognized, saving printerID'
# 				printer_printerId = printerData['params']['iserial']

# 			#elif printerData['method'] == 'printerchanged':
# 			#elif printerData['method'] == 'printerAdded':

# 		# if printerData['method'] != 'port_detached' and printerData['method']!='machine_state_changed':
# 		# 	online = True
# 		print '\nmethod =',printerData['method']
# 		print 'print job update:'
# 		print '\tfilename:\t\t',job_filename
# 		print '\tJob ID:\t\t',job_id
# 		print '\tJob num:\t',job_num		
# 		print '\tPrinter In Use:\t',printer_inUse
# 		print '\tTool Temp:\t',printer_tool1_temp
# 		print '\tprocess:\t',job_process
# 		print '\tprogress:\t',job_progress,'%'
# 		print '\tconclusion:\t', job_conclusion
# 		if job_fail_msg != '':
# 			print '\tfailure message\t', job_fail_msg
# 		print 'Debug:'
# 		print '\tjob_started:\t', job_started

# class UnixSocketFactory(Factory):
# 	protocol = UnixSocketProtocol


# class UnixMitmProtocol(Protocol):

# 	def connectionMade(self):
# 		self.conveyordEndpoint = endpoints.UNIXClientEndpoint(reactor,'/home/pi/raspi/makerbot/conveyor/conveyord.socket')
# 		self.conveyordFactory = UnixSocketFactory()
# 		self.conveyordFactory.parent = self
# 		self.conveyordEndpoint.connect(self.conveyordFactory)

# 	def dataReceived(self,data):
# 		print 'cmdline -> MITM:',data
# 		self.conveyordFactory.conn.transport.write(data)

# class UnixMitmFactory(Factory):
# 	protocol = UnixMitmProtocol


if __name__ == '__main__':
	#setup data connections
	cookieJar = CookieJar()
	agent = CookieAgent(Agent(reactor), cookieJar)
	status = 'done'
# Greg commented out l = and l.start	
	# l = task.LoopingCall(makeRequest,status)
	#jsonDebug
	#disable this to stop posting and receiving info to/from the website
	# l.start(5)

	print 'Reactor Started'
	f = task.LoopingCall(findPrinter_and_Ip)
	f.start(5)

	#jsonDebug
	#turn this OFF to disable passive listening
	#important to reduce amount of garbage on cmdline output
#Greg commented out unixEndPoint stuff - 2 lines
	# unixEndPoint = endpoints.UNIXClientEndpoint(reactor, '/home/pi/raspi/makerbot/conveyor/conveyord.socket')
	# unixEndPoint.connect(UnixSocketFactory())

	#jsonDebug
	#uncomment this in order to see intermediate json stream - good for getting json commands generated from cmd_line
	# unixMitmEndPoint = endpoints.UNIXServerEndpoint(reactor,'/home/pi/mitm.socket')
	# unixMitmEndPoint.listen(UnixMitmFactory())
	


	reactor.run()