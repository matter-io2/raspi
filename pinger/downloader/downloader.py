from twisted.web.client import Agent,CookieAgent, ResponseDone
from twisted.web.http_headers import Headers
from twisted.internet.protocol import Protocol
from twisted.internet.defer import Deferred
import os
import sys

class BeginningPrinter(Protocol):
	def __init__(self, finished,remaining):
		self.finished = finished
#		self.remaining = remaining
		self.display = ''
	def dataReceived(self, bytes):
#		if self.remaining:
			self.display += bytes
#			print len(self.display)
#			self.remaining -= len(bytes[:self.remaining])

	def connectionLost(self, reason):
		#print self.display
		if reason.getErrorMessage().startswith('Response body fully received'):
			self.finished.callback(self.display)
			
		else:
			reason.printTraceback()
		if __name__ == '__main__':
			reactor.stop()

def downloadFile(url,agent):
	d = agent.request(
				'GET',
				url,
				Headers({'Accept':['text/html','*/*'],'Host':['ec2-23-20-192-37.compute-1.amazonaws.com'],'Accept-Encoding':['gzip','deflate','sdch']}),
				None,
				)
	fileName = '/home/pi/gcodeFiles/'+url.split('/')[-1]
	d.addCallback(cbRequest,fileName)
	return d
	
def saveBody(body,fileSaved,fileName):
	# fileName = ''
	# if os.name == 'posix':
	# 	fileName = '/home/pi/toPrint.gcode'
	# else:
	# 	fileName = 'toPrint.gcode'
	
	with open(fileName,'w') as fileOut:
		fileOut.write(body)
	
	fileSaved.callback(fileName)
	

def cbRequest(response,fileName):
	# print 'Response Code:',response.code,'Response Length:',response.length

	headersDict = {}
	for i in response.headers.getAllRawHeaders():
		# print i
		headersDict[i[0]] = i[1]
#	
	finished = Deferred()
	if response.code == 200:  # if the response is good
		#remove all cached files

		folder = '/home/pi/gcodeFiles'
		for the_file in os.listdir(folder):
			file_path = os.path.join(folder, the_file)
			try:
				# if os.path.isfile(file_path):
				os.unlink(file_path)
			except Exception, e:
				print e
		#write out new file into ~/gcodeFiles
		response.deliverBody(BeginningPrinter(finished,response.length))
		fileSaved = Deferred()
		finished.addCallback(saveBody,fileSaved,fileName)
		return fileSaved

if __name__ == '__main__':
	from twisted.internet import reactor,task
	agent = Agent(reactor)
	downloadFile('http://ec2-23-20-192-37.compute-1.amazonaws.com/files/Princeton/single.gcode',agent)
	reactor.run()
