from cookielib import CookieJar
from twisted.internet import reactor,task,endpoints
from twisted.web.client import Agent, CookieAgent, ResponseDone
from twisted.web.http_headers import Headers
from twisted.internet.protocol import Protocol, Factory
from twisted.internet.defer import Deferred
from twisted.web.client import FileBodyProducer
#import time
from time import time
from datetime import datetime
import urllib
import simplejson as json

import os
import subprocess
import threading
import logging

from zope.interface import implements
from twisted.internet.defer import succeed
from twisted.web.iweb import IBodyProducer
#server = 'http://matter.io/'
server = 'http://ec2-107-22-186-175.compute-1.amazonaws.com/'

logPath = '/home/pi/raspi/pinger/pinger.log'
logger = logging.getLogger('pingerLog')	#log name
git_commit=''

debug_internet=False
debug_server_response=False
debug_printer_socket=True
debug_printer_client_socket=True
debug_webcam=False

inet_iface=''
network_name=''
link_quality=''
signal_level=''
noise_level=''

lost_packets = 0
pic_count = 0

# printer_type=''
printer_type='Makerbot'
printer_type_ID=''
update_and_log=True

printer_profile = 0
printer_firmware = 0
printer_printerId = ''
printer_inUse = False
printer_tool1_temp = -1
printer_tool2_temp = -1
printer_bed_temp = -1
online = False # 'CONNECTED', 'DISCONNECTED'

pi_id = 'ASDF1234'

job_id = ''
job_filename = ''
job_num = -1  # (def) -1, read from jobadded or jobchanged in UNIXsocket
job_process = 'idle'
job_progress = -1
job_conclusion = ''  # 'ENDED','CANCELED','FAILED' 
job_started = False
job_fail_msg = ''
ip_address = ''


#---main brain services---
#1) moderate wifi connection
#2) find printer type (lsusb) and connect when disconnected
#3) talk to server, parse response, dole out tasks
#4) webcam - take pic, upload
#5) check for update, upload job log @ end of each job

def mainBrain():
	#variables I need - 
	global inet_iface, lost_packets, pic_count
	global printer_type, printer_printerId, printer_inUse
	global job_conclusion, printer_inUse
	global pi_id, online, ip_address
	global update_and_log
	global debug_internet, debug_server_response, debug_printer_socket, debug_printer_client_socket, debug_webcam

	status='done'

	#1) INTERNET cnx mediation - user print to debug
	print '\n----INTERNET cnx mediation---- (',debug_internet,')\n'
	getInetInfo()
	if lost_packets>=6: # no ip addres, reconnect after server timeout
		reconnectInternet(inet_iface)
		#should handle hotswapping...

	#2) PRINTER mediation - user print to debug
	print '\n----PRINTER mediation----(debug=',debug_printer_socket,'/',debug_printer_client_socket,')\n'
	if printer_printerId=='':
		print 'getting printer type from lsusb' #used for timing
		getPrinterType()
		print 'printer_type = ', printer_type
		print 'printer_type_ID = ', printer_type_ID
		if printer_type=='Makerbot':
			print 'there is a makerbot usb connected'
			print 'attempting connect to Makerbot printer'
			reconnectPrinter()
		elif printer_type=='Ultimaker':
			print 'start ultimaker pinger'
		elif printer_type=='LulzBot':
			print 'start LulzBot/reprap pinger'
		req_type='pi'
	else:
		print 'printer connected, id:',printer_printerId
		req_type='printer'

	#3) PING SERVER... once ip_address saving is consistent add - if ip_address!=''
	#	ping server with printer or pi info
	print '\n----SERVER mediation----(debug=',debug_server_response,')\n'
	makeRequest('printer',status) #status=done
	#makeRequest(req_type,status) #status=done

	#4) WEBCAM
	if printer_printerId=='':	
		print '\n----WEBCAM mediation----(debug=',debug_webcam,')\n'
	webcamPic()

	#5) UPDATE AND LOG UPLOAD
	print '\n----UPDATE mediation----\n'

	if update_and_log:
		if ip_address!='' and not printer_inUse:
			#upload last job's log file
			#LOG UPLOAD
			if job_id!='':
				print '\n\n\n\n\nattempting upload of log\n\n\n\n\n'
				makeRequest('log',status) #status=done

			print '\n\n\n\n\nattempting update now\n\n\n\n\n'
			#UPDATE via git
			#this script runs git fetch and will update branches if there's something new available.
			# it will also restart the startup script (canceling pinger and conveyor_service)
			#THUS, MAKE SURE NOTHING IS PRINTING when calling this the update routine
			
			arg='/home/pi/raspi/pinger/update_current.sh'
			p_git=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
			data_git=p_git.communicate()
			update_and_log=False

	print 'update/log section finished'
	#LOGGING:
	#download
	#printCmd, printExec(state_change)
	#cancelCmd, cancelExec(state_change to STOPPED)
	#job_conclusion()

#driver (below)
# contains all low level commands
# - connect, print, cancel, monitor

def initialize(): #startup script, only run once at beginning, run here because global variables aren't initialized yet in __main__
	global debug_internet,debug_server_response,debug_printer_socket,debug_printer_client_socket,debug_webcam
	global logPath
	global logger
	global git_commit
	print "----Debug Settings----"
	print "internet", debug_internet
	print "server_response", debug_server_response
	print "printer_socket", debug_printer_socket
	print "printer_client_socket", debug_printer_client_socket
	print "webcam", debug_webcam

	get_pi_id()
	getInetInfo()
	setupLog(logPath)
	#find git commit and post to log files
	arg=['cd /home/pi/raspi/pinger && git log -1']
	p_git=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
	data_git=p_git.communicate()
	if len(data_git)>1:
		git_commit=data_git[0]



# http://docs.python.org/2/library/logging.html
def setupLog(filepath):
	global logger
	
	hdlr = logging.FileHandler(filepath)	#i.e. '/var/tmp/myapp.log'
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	hdlr.setFormatter(formatter)
	logger.addHandler(hdlr) 
	logger.setLevel(logging.INFO)

	#example log messages
	# logger.error('We have a problem')
	# logger.info('While this is just chatty')


#add real pi_id
def get_pi_id():  #saves raspi's serial # as unique pi_id
	global pi_id
	arg='cat /proc/cpuinfo'
	p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
	data = p.communicate()
	split_data = data[0].split()
	if 'Serial' in split_data:
		pi_id = split_data[split_data.index('Serial')+2]
		print '\npi_id:' + str(pi_id) + '\n'
	#comment this out to turn on pi_id trigger
	print 'using old pi id until the server accepts unique pi_idz'
	pi_id = 'ASDF1234'


#---------INTERNET subroutines------------
# From: http://cagewebdev.com/index.php/raspberry-pi-showing-some-system-info-with-a-python-script/
# saves connection interface and ip address
def getInetInfo():
	global ip_address, inet_iface
	global network_name, link_quality, signal_level, noise_level
	global debug_internet

	#Returns the current IP address
	arg='ip route list'
	p1=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
	data1 = p1.communicate()
	#determine active internet interface - eth0/wlan0
	if data1[0]=='': #no internet CNX
		#see if ethernet cable is physically connected
		try:	
			p2=subprocess.Popen('cat /sys/class/net/eth0/carrier',shell=True,stdout=subprocess.PIPE)
			data_eth=p2.communicate()
			if len(data_eth)>1:
				if bool(int(data_eth[0][0])): #tells me whether ethernet is connected or not 1=connected, 0=not connected
					#ethernet is still attached, try to reconnect to eth0!
					inet_iface='eth0' #reconnect on ethernet even if it's not in the ip table right now...because it's still plugged in
				else:  #no ethernet, reconnect on wlan0
					inet_iface='wlan0'
		except:
			pass

	else: #internet CNX! - parse data
		split_ipRoute = data1[0].split()
		#get interface - doesn't reset until another connection comes online
		if 'eth0' in split_ipRoute:
			inet_active = 'active'
			inet_iface='eth0'
		elif 'wlan0' in split_ipRoute:
			inet_active = 'active'
			inet_iface='wlan0'
			p3=subprocess.Popen('iwconfig wlan0',shell=True,stdout=subprocess.PIPE)
			data_wlan0=p3.communicate()
			network_name=data_wlan0[0].split('ESSID:"')[1].split('"')[0]
			link_quality=data_wlan0[0].split('Link Quality=')[1].split(' ')[0]
			signal_level=data_wlan0[0].split('Signal level=')[1].split(' ')[0]
			noise_level=data_wlan0[0].split('Noise level=')[1].split('\n')[0]
		#save lan_ip
		if 'src' in split_ipRoute:
			ip_address = split_ipRoute[split_ipRoute.index('src')+1]
		else:
			ip_address = ''

	if debug_internet:
		if ip_address=='':
			print "internet interface:",inet_iface
			print 'no LAN IP address assigned - missing "src" key \n interface is probably inactive'
		else:
			print "internet interface:",inet_iface
			print 'LAN IP Address:' + str(ip_address)


#reconnects using sudo ifup [eth0/wlan0]
def reconnectInternet(debug_output):
		global inet_iface
		if debug_output: print 'starting bash script to reconnect to wifi'
		arg = ['bash','/home/pi/raspi/piConfig/find_network_hot.sh',str(inet_iface)] # find_network_hot.sh allows pinger to stay active
		p=subprocess.Popen(arg)
		# p.wait()
		if debug_output: print 'waiting... not worth doing anything until internet comes back'
		#reconnect should probably run in the background... might mess up conveyor_service and cause print to fail...
		p.wait()  # don't do anything until wifi comes back up, 
		if debug_output: print 'wait is finished'
		data = p.communicate()
		if debug_output: print 'printing data from python...\n\n\n'
		if debug_output: print data


#---------PRINTER subroutines------------
#uses lsusb to get printer make (used to decide which pinger file to use)
def getPrinterType():
	#author - Drew Beller
	global printer_type, printer_type_ID
	found = False
	arg='lsusb'
	p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
	data = p.communicate()
	split_data = data[0].split()
	if '23c1:d314' in split_data:
		printer_type_ID = '23c1:d314' #Makerbot Replicator 1
		printer_type = 'Makerbot'
		found = True
	elif '23c1:b015' in split_data:
		printer_type_ID = '23c1:b015'
		printer_type = 'Makerbot'#Makerbot Replicator2 or Replicator2x
		found = True
	elif '2341:0042' in split_data:
		printer_type_ID = '2341:0042'
		printer_type = 'Ultimaker'
		found = True
	elif '27b1:0001' in split_data:
		printer_type_ID = '27b1:0001'
		printer_type = 'LulzBot AO100'
		found = True
	elif 'Arduino' in split_data:#should work for Arduino based RepRaps
		printer_type_ID = split_data[split_data.index('Arduino')-1]
		printer_type = 'Unknown'
		found = True
	#Drew should explain this part to Greg
	#not sure what this does, 
	# else:#returns ID when printer has no name
	# 	cnt=-1
	# 	for i in split_data:
	# 		cnt=cnt+1
	# 		if (i == 'ID'):
	# 			if (len(split_data)-1)<(cnt+2):
	# 				printer_type_ID= split_data[cnt+1]
	# 				printer_type= "Unknown"
	# 				found = True
	# 			elif split_data[cnt+2]=='Bus':
	# 				printer_type_ID= split_data[cnt+1]
	# 				printer_type= "Unknown"
	# 				found = True
	if printer_type=='Unknown':
		print 'Not a Recognized Printer \n RepRaps may still work'
	if found==False:
		print 'No Printer Found'

#attempts connection to printer
def reconnectPrinter():
	global printer_profile, printer_firmware, printer_printerId 
	print 'trying to connect to printer...'
	online == False
	makeCmdlineReq('hello')  # handshake!  
	makeCmdlineReq('connect',{'machine_name':None ,'port_name':None , 'persistent':'true','profile_name':'Replicator2' ,'driver_name':'s3g'})  
	# gets printer properties
	#may need to change profile_name, not sure...


#---------WEBCAM subroutine------------
def webcamPic():
	global server, pic_count
	global printer_printerId, pi_id
	global debug_webcam
	address = server+'webcamUpload'
	if debug_webcam:
		print 'address for post', address
		print 'printer id = ',printer_printerId
	if printer_printerId == '': #no printerId, use pi_id
		#arg = ['/home/pi/raspi/pinger/webcam_routine.sh',address,str(pi_id),str(pic_count)]
		pass # do nothing if there is no printer_id
	else:
		arg = ['/home/pi/raspi/pinger/webcam_routine.sh',address,str(printer_printerId),str(pic_count),str(debug_webcam)]
		p_webcam=subprocess.Popen(arg,shell=False,stdout=subprocess.PIPE)
	pic_count = pic_count +1
	if debug_webcam:
		print '\n --------webcam_routine.sh exiting-------- \n'


#---------SERVER subroutines-----------
#http POST to website - also 
def makeRequest(req_type,status):
	global debug_server_response
	global printer_type, printer_type_ID,printer_profile, printer_firmware, printer_printerId, printer_inUse, online
	global printer_tool1_temp, printer_tool2_temp, printer_bed_temp
	global job_num, job_process, job_progress, job_conclusion
	global pi_id
	global server, lost_packets
	global inet_iface, pic_count
	global network_name,link_quality,signal_level, noise_level
	global git_commit
	address = server+'printerPing/'	
	print 'upload address = ',address

	if req_type=='printer':
		if debug_server_response:
			# debugger that shows what is being posted to the server (see agent.request for actual posting)	
			print 'sending printer data -- printer id is present'
			print 'Data Sent:',urllib.urlencode({'type':'update',
												'git_commit':git_commit,
												'packet_type':req_type,											
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

	# posts information to server
		d = agent.request(	'POST',
							address,
							Headers({'Content-Type': ['application/x-www-form-urlencoded']}),
							StringProducer(urllib.urlencode({'type':'update',
												'git_commit':git_commit,												'packet_type':req_type,
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

	elif req_type=='pi':
		if debug_server_response:
		# debugger that shows what is being posted to the server (see agent.request for actual posting)	
			print 'sending pi data -- no printer id'
			print 'Data Sent:',urllib.urlencode({'type':'update',
																'pi_id':pi_id,
																'git_commit':git_commit,
																'online':online,
																'ipAddress':ip_address,
																'network_type':inet_iface,															
																'network_name':network_name,
																'link_quality':link_quality,
																'signal_level':signal_level,
																'noise_level':noise_level,
																'status':status})
		# posts information to server
		d = agent.request(	'POST',
							address,
							Headers({'Content-Type': ['application/x-www-form-urlencoded']}),
							StringProducer(urllib.urlencode({'type':'update',
															'pi_id':pi_id,
															'online':online,
															'git_commit':git_commit,
															'ipAddress':ip_address,
															'network_type':inet_iface,															
															'network_name':network_name,
															'link_quality':link_quality,
															'signal_level':signal_level,
															'noise_level':noise_level,
															'status':status}))
						)
	elif req_type=='log':
		address=server+'piLogUpload'
		time_stamp=datetime.now().strftime("%Y-%m-%d__%I:%M:%S%p")
		name=printer_printerId+'_'+time_stamp+'_'+job_id
		arg=['/home/pi/raspi/pinger/log_upload.sh',str(address),str(logPath),str(name),'rm']
		p_job_log=subprocess.Popen(arg,shell=False,stdout=subprocess.PIPE)
		#block!
		data_log=p_job_log.communicate()

		#might want this data later
		# curl -F "file=@/dev/shm/$2_$3.jpg;filename=$2_$3.jpg" -m 15 address

	if debug_server_response:
		print 'Request Sent' # debug output
		print 'lost packet num =', str(lost_packets)
	lost_packets = lost_packets+1

	# adds next method to polling
	if req_type!='log':
		d.addCallback(cbRequest, cookieJar)

	# #this should live in main brain somewhere higher
	# # if lost_packets >= 5 and not printer_inUse:
	# if lost_packets > 6: # 30 seconds  
	# 	print 'no response from server - attempting reconnect via bash script now'
	# 	print '(>=6 packets missed, 30 seconds without connection)'
	# 	lost_packets=0
	# 	reconnectInternet()
	# # assume packet is lost unless you get a response in cbRequest()

#data sent back from server
def cbRequest(response, cookieJar):
	global lost_packets, debug_server_response
	if debug_server_response:
		print 'Response Code:', response.code
	lost_packets = 0

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
no_job_id_key_count=0
#parses json string from server
def parseJSON(bodyString):
	global printer_inUse, job_process, job_progress, job_conclusion, job_num, job_id
	global cancelCmdTime, job_started
	global no_job_id_key_count
	global logger

	bodyDict = json.loads(bodyString)
	print bodyDict
	# this is the Json packet from the server
	job_cancel = False
	if bodyDict.has_key('job_id'):
		if bodyDict['job_id'] == job_id:
		# job_ids match!
			print 'DEBUG: job_id MATCH'
			if bodyDict.has_key('job_cancelCmd') and bodyDict['job_cancelCmd'] == True and printer_inUse:
				print '\n\nAttempting cancel for current job via job_cancelCmd \n\n'
				logger.warning('Cancel Job - command from server for job_id:%s job_num:%s',str(job_id),str(job_num))
				job_cancel = True
		else:
		#new job_id don't match or
			print 'DEBUG: job_id mismatch'
			if printer_inUse:
				logger.warning('Cancel Job - Attempting cancel JOB_IDs DO NOT MATCH')
				logger.warning('old_job_id:%s job_num:%s ... attempting cancel',str(job_id),str(job_num))
				logger.warning('new_job_id:%s ',str(bodyDict['job_id']))
				print '\n\nAttempting cancel JOB_IDs DO NOT MATCH \n\n'
				print 'old_job_id:',str(job_id),' job_num:',str(job_num),' ... attempting cancel'
				print 'new_job_id:',str(bodyDict['job_id'])
				if job_id != '': # not intial value
						#delete current job
						job_cancel = True
			job_id = bodyDict['job_id']
			job_process = 'idle'
			job_progress = 0
			job_conclusion = '' #defaults to '' when job has not concluded (used above)
			job_started = False
			#need to keep job_num for cancel command

		#Cancel job (currentJob or previous job that was left running)
	else: #no job_id key
		if printer_inUse:
			print '\n\n\n\n\nprinter in use w/ no job_id from server... \n THIS SHOULD NEVER HAPPEN!!!\n\n\n\n'
			logger.warning('Cancel Job - printer in use w/ no job_id saved from server... this should never happen - noJobIdcount=%s',str(no_job_id_key_count))
			no_job_id_key_count = no_job_id_key_count+1
			if no_job_id_key_count>6: #prevents cancel from stray job cancels
				job_cancel = True
	#new features
	# - working timeout (cancelCmdTime set when cmd is called)
	# - counter on no_job_id_count...
	if job_cancel and int(job_num) >= 0:
		dif = time()-cancelCmdTime
		if int(dif) > 10: # timeout... not sure if it's working
			logger.warning('bodyDict on cancel = %s'+str(bodyDict))
			makeCmdlineReq('hello')  # handshake!  
			makeCmdlineReq('canceljob',{'id':job_num})  # kills job [id]
			job_num = -1 # important to say new job has not yet been added 
			cancelCmdTime=time()
			logger.warning(str(bodyDict))
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
	global logger
	agent = Agent(reactor)
	print "In Download File:",url

	job_filename = url.split('/')[-1]
	if url != None:
		logger.info('download %s started',str(url))
		d = dl.downloadFile(url,agent)
		logger.info('download %s finished',str(url))
		logger.info('print cmd called')
		d.addCallback(printFile)


import printer.printer as p
def printFile(fileName):
	global logger
	print 'In PrintFile',fileName  # shows file path
	#determine which slicer was used...
	slicer = "miraclegrue" 
	with open(fileName) as fileIn:
		for i in range(15):
			line = fileIn.readline()
			if line.find("Skeinforge") > 0:
				slicer = "skeinforge"
	#print file in printer.py
	p.printFile(fileName,slicer)
	logger.info('print started - %s ',str(fileName))

#LIGHTS - fLASH GREEN WHEN GOING

def print500Response(bodyString):
	print 'error 500!!! saved log out to Desktop'
	#print bodyString
	text_file = open("/home/pi/Desktop/error.html", "w")
	text_file.write("%s"%bodyString)
	text_file.close()

#----------------------------------/\------------------------------------#
#----------------------------------||------------------------------------#
#------------------------------MAIN BRAIN--------------------------------#
#-----------------------------|__________|-------------------------------#
#-----------------------------|          |-------------------------------#
#--------------------------------DRIVER----------------------------------#
#----------------------------------||------------------------------------#
#----------------------------------\/------------------------------------#

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
	

# From: http://twistedmatrix.com/documents/current/web/howto/client.html
class BeginningPrinter(Protocol):
	def __init__(self, finished,remaining):
		self.finished = finished
		# self.remaining = remaining
		self.display = ''
	def dataReceived(self, bytes):
		# if self.remaining:
			self.display += bytes
			# self.remaining -= len(bytes[:self.remaining])

	def connectionLost(self, reason):
		if reason.getErrorMessage().startswith('Response body fully received'):
			self.finished.callback(self.display)
		else:
			print reason.printTraceback()



def makeCmdlineReq(cmd,params = {}):
	global debug_printer_client_socket
	unixEndPoint = endpoints.UNIXClientEndpoint(reactor, '/home/pi/raspi/makerbot/conveyor/conveyord.socket')
	#READ ONLY TEST
	# unixEndPoint = endpoints.UNIXClientEndpoint(reactor, '/tmp/makerbot/conveyord.socket')
	
	newCmdReq = CmdlineReqFactory()
	newCmdReq.cmd = cmd
	newCmdReq.params = params
	unixEndPoint.connect(newCmdReq)
	if debug_printer_client_socket:
		print cmd
		print params

global currentCommand
class CmdlineReqProtocol(Protocol):
	def connectionMade(self):
		global debug_printer_client_socket
		global currentCommand
		self.cmd = self.factory.cmd
		self.params = self.factory.params
		outDict = {}
		if self.cmd == 'hello':
			outDict['id'] = 0
		elif self.cmd == 'connect' or self.cmd == 'canceljob' or self.cmd == 'getjob':
			outDict['id'] = 1
		outDict['params'] = self.params
		outDict['jsonrpc'] = '2.0'
		outDict['method'] = self.cmd
		currentCommand = self.cmd
		if debug_printer_client_socket: 
			print 'current command is',currentCommand

		self.transport.write(json.dumps(outDict))

	def dataReceived(self,data):
		global debug_printer_client_socket
		global currentCommand
		global printer_profile, printer_firmware, printer_printerId, printer_inUse, online
		if debug_printer_client_socket:
			print 'CmdLineReq Received:',data

		#parse multiple json packets into individual packets
		if '}{' in data:
			parsed = True
			# print '\n\n splitting data \n\n'
			data = data.split('}{')
			count = 0
			for i in range(len(data)):
				if i == 0:
					data[0] = data[0] + '}'
				elif i == len(data) - 1:
					data[len(data)-1] = '{' + data[len(data)-1]
				else:
					data[i] = '{' + data[i] + '}'
		else:
			data = [data]

		for msg in data:
			if debug_printer_client_socket: print 'unpacking msg from cmdlineReq'
			cmdResponseData = json.loads(msg)
			if cmdResponseData.has_key('error'):
				print 'error while executing ', currentCommand
				print 'error feedback:',cmdResponseData['error']
				print 'error code = ', cmdResponseData['error']['code']
				if cmdResponseData['error']['data'].has_key('name') and cmdResponseData['error']['data']['name'] == 'NoPortsException':
					print 'USB DISCONNECTED!\n\n\n\n\n\n\n'
					online = False
				if cmdResponseData['error'].has_key('name'):
					print '\n\tErrorName:\t'+str(cmdResponseData['error']['name'])
					#'UnknownJobError' if job is not available

			elif cmdResponseData.has_key('result'):
				online = True
				if cmdResponseData['id'] == 1:  # this works for everything but print [file] where the print function is id=2 (3rd cmd)
					if debug_printer_client_socket:
						print 'response id = 1, unpacking info'
						print currentCommand
					if currentCommand == 'connect':
						printer_profile = cmdResponseData['result']['profile_name']
						printer_firmware = cmdResponseData['result']['firmware_version']
						printer_printerId = cmdResponseData['result']['name'].split(':')[-1]
						printer_tool1_temp = cmdResponseData['result']['temperature']['tools']['0'] #1st tool
						if printer_profile == 'Replicator2X':
							printer_bed_temp = cmdResponseData['result']['temperature']['heated_platforms']['0']
							printer_tool2_temp = cmdResponseData['result']['temperature']['tools']['1'] # 2nd tool
						if debug_printer_client_socket:
							print 'printer recognized, saving information'
							print 'printer:'
							print '\tprofile\t\t', printer_profile
							print '\tfirmware \t', printer_firmware
							print '\tid\t\t', printer_printerId
							print '\textruder Temp\t', printer_tool1_temp

					elif currentCommand == 'canceljob': # following cancel command
						#think job was canceled
						
						#only add this if it's going to link directly to job_num and job_id (respectively)
						#makeCmdlineReq('hello')  # handshake!  
						#makeCmdlineReq('getjob',{'id':job_num})  # kills job [id]			
						pass

					elif currentCommand == 'getjob': # following cancel command

						#only add this if it's going to link directly to job_num and job_id (respectively)
						# job_conclusion = cmdResponseData['params']['conclusion']
						pass
					currentCommand = ''

			else:
				if debug_printer_client_socket:
					print '\n\n\n\n\n\n Unknown response to command - did not contain "error" or "result" keys \n\n\n\n\n\n'



		#reset current Command
		self.transport.loseConnection()

class CmdlineReqFactory(Factory):
	protocol = CmdlineReqProtocol

import traceback

#passive listener watching the printer feedback (temp, events, etc.)
class UnixSocketProtocol(Protocol):
	def connectionMade(self):
		print 'Unix Socket Connected'
		self.factory.conn = self

	def dataReceived(self, data):
		global printer_profile, printer_firmware, printer_printerId, printer_inUse, online
		global printer_tool1_temp, printer_tool2_temp, printer_bed_temp
		global job_filename, job_process, job_progress, job_conclusion, job_num, job_id
		global pi_id
		global job_fail_msg
		global debug_printer_socket
		global logger, update_and_log
		# DEBUG - supressing json output
		# print 'PRINTER SOCKET:',
		# print '\n'.join([l.rstrip() for l in data.splitlines()])

		#jsonDebug 
		#enable this to view the intermediate json stream
		# self.factory.parent.transport.write(data)

		# split up multiple data packets coming back in one chunk
		parsed = False
		if '}{' in data:
			parsed = True
			# print '\n\n splitting data \n\n'
			data = data.split('}{')
			count = 0
			for i in range(len(data)):
				if i == 0:
					data[0] = data[0] + '}'
				elif i == len(data) - 1:
					data[len(data)-1] = '{' + data[len(data)-1]
				else:
					data[i] = '{' + data[i] + '}'
		else:
			data = [data]

			# data = [data_array[0]+'"}' , '{' + data_array[1]]  #save only first data chunk

		for msg in data:
			printerData = json.loads(msg)
			# else:
			# 	printerData = json.loads(data)
			if debug_printer_socket: print msg
			if not printerData.has_key('method'):
				return
			if printerData['method'] == 'jobadded':
				printer_inUse = True
				job_num = printerData['params']['id']
				job_progress = 0
				job_conclusion = ''

			if printerData['method'] == 'jobchanged':
			# get progress, printerId

				if job_num == printerData['params']['id']:
					# doesn't need to be saved... because they match!
					# job_num = printerData['params']['id']
					if debug_printer_socket: print '\n\n----job_num matched----\nsaving data\n\n'
					if printerData['params']['state'] == 'RUNNING':
						printer_inUse = True
						job_process = printerData['params']['progress']['name']
						job_progress = printerData['params']['progress']['progress']
						job_conclusion = ''
						# if job_process == 'print' or job_process == 'heatup':
						# 	#clean up - delete this and move to server side
						# 	#this should change to be just below the desired temperature passed from the server
						# 	if printer_tool1_temp <220:
						# 		job_process = 'heatup'
						# 	else:
						# 		job_process = ''
					elif printerData['params']['state'] == 'STOPPED':
						job_conclusion = printerData['params']['conclusion']
						printer_inUse = False
						update_and_log=True
						if debug_printer_socket: print '\n job state STOPPED \N'
						logger.warning('job STOPPED')
						logger.warning('job conclusion: %s',job_conclusion)

						if printerData['params']['failure']:
							if printerData['params']['failure'].has_key('exception') and printerData['params']['failure']['exception'].has_key('message'):
								job_fail_msg = printerData['params']['failure']['exception']['message']
								logger.warning('job failed, error msg: %s', job_fail_msg)
				else:
					if debug_printer_socket: print '\n\n----job_num mismatch----\nnot saving any info\n\n'
					logger.warning('job num mismatch, job_id_current %s', job_id)


			elif printerData['method'] == 'machine_state_changed':
			# get printerId, firmware, profile
				if printerData['params']['state'] == 'DISCONNECTED':
					online = False
					printer_printerId = ''
				elif printerData['params']['state'] == 'IDLE':
					#reseting info after job is finished
					printer_inUse = False 
				else:
					printer_profile = printerData['params']['profile_name']
					printer_firmware = printerData['params']['firmware_version']
					printer_printerId = printerData['params']['name'].split(':')[-1]
					if printer_tool1_temp == -1 and printerData['params']['temperature']['tools'].has_key('0'):
						printer_tool1_temp = printerData['params']['temperature']['tools']['0'] # get first tool if first value hasn't been saved

			elif printerData['method'] == 'machine_temperature_changed':
			# get printerId and tool_temps
			# measure tool1 temp for all machines - Rep2 and Rep2X
				if printerData['params']['state'] == 'IDLE':
					printer_inUse = False
				printer_tool1_temp = printerData['params']['temperature']['tools']['0'] #1st tool
				if printer_profile == 'Replicator2X':
					printer_bed_temp = printerData['params']['temperature']['heated_platforms']['0']
					printer_tool2_temp = printerData['params']['temperature']['tools']['1'] # 2nd tool

			elif printerData['method'] == 'port_detached':
				online = False
				printer_inUse = False
				printer_profile = 0
				printer_printerId = ''
				printer_firmware = 0

			elif printerData['method'] == 'port_attached':
				print 'printer port recognized, saving printerID'
				printer_printerId = printerData['params']['iserial']

			#elif printerData['method'] == 'printerchanged':
			#elif printerData['method'] == 'printerAdded':

		# if printerData['method'] != 'port_detached' and printerData['method']!='machine_state_changed':
		# 	online = True
		if debug_printer_socket: 
			print '\nmethod =',printerData['method']
			print 'print job update:'
			print '\tfilename:\t',job_filename
			print '\tJob ID:\t\t',job_id
			print '\tJob num:\t',job_num		
			print '\tPrinter In Use:\t',printer_inUse
			print '\tTool Temp:\t',printer_tool1_temp
			print '\tprocess:\t',job_process
			print '\tprogress:\t',job_progress,'%'
			print '\tconclusion:\t', job_conclusion
			if job_fail_msg != '':
				print '\tfailure message\t', job_fail_msg
			print 'Debug:'
			print '\tjob_started:\t', job_started

class UnixSocketFactory(Factory):
	protocol = UnixSocketProtocol


class UnixMitmProtocol(Protocol):

	def connectionMade(self):
		self.conveyordEndpoint = endpoints.UNIXClientEndpoint(reactor,'/home/pi/raspi/makerbot/conveyor/conveyord.socket')
		#READ ONLY TEST
		# self.conveyordEndpoint = endpoints.UNIXClientEndpoint(reactor,'/tmp/makerbot/conveyord.socket')
		self.conveyordFactory = UnixSocketFactory()
		self.conveyordFactory.parent = self
		self.conveyordEndpoint.connect(self.conveyordFactory)

	def dataReceived(self,data):
		print 'cmdline -> MITM:',data
		self.conveyordFactory.conn.transport.write(data)

class UnixMitmFactory(Factory):
	protocol = UnixMitmProtocol


if __name__ == '__main__':
	#setup data connections
	cookieJar = CookieJar()
	agent = CookieAgent(Agent(reactor), cookieJar)

	initialize()
	print 'Reactor Started'
	f = task.LoopingCall(mainBrain)
	f.start(5)

	# l.start(5)
	# l = task.LoopingCall(makeRequest,status) #talks to server
	# l.start(5)
	# f = task.LoopingCall(findPrinter_and_Ip)
	# f.start(5)
	#g = task.LoopingCall(webcam_pic) #takes image and uploads it
	#g.start(5)
	#implements unique pi_id - currently saved to tool_temp2 as debugging measure until all pi id's are added, or website can receive them

	#jsonDebug
	#turn this OFF to disable passive listening
	#important to reduce amount of garbage on cmdline output
	
	unixEndPoint = endpoints.UNIXClientEndpoint(reactor, '/home/pi/raspi/makerbot/conveyor/conveyord.socket')
	#READ ONLY TEST
	# unixEndPoint = endpoints.UNIXClientEndpoint(reactor, '/tmp/makerbot/conveyord.socket')
	
	unixEndPoint.connect(UnixSocketFactory())

	#jsonDebug
	#uncomment this in order to see intermediate json stream - good for getting json commands generated from cmd_line
	# unixMitmEndPoint = endpoints.UNIXServerEndpoint(reactor,'/home/pi/mitm.socket')
	# unixMitmEndPoint.listen(UnixMitmFactory())
	


	reactor.run()
