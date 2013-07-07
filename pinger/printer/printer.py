import subprocess
from subprocess import Popen, PIPE
import sys
import os
pathsAdded = False

def printFile(fileName,slicer):
	global pathsAdded 
	print '***************'
	print 'SLICER:',slicer
	print '***************'

	currPath = os.getcwd()
	os.chdir('/home/pi/raspi/makerbot/conveyor')
	if not pathsAdded:
		sys.path.insert(0,'./virtualenv/local/lib/python2.7/site-packages/pyserial-2.7_mb2.1-py2.7.egg')
		sys.path.insert(0,'./virtualenv/lib/python2.7/site-packages/pyserial-2.7_mb2.1-py2.7.egg')
		pathsAdded = True
		for i in sys.path:
			print i
	if slicer == 'skeinforge':
		subprocess.Popen(['python','conveyor_cmdline_client.py','-c','conveyor-debian.conf','print',fileName,'--has-start-end'], stdin = None, stdout = None, stderr = None, close_fds=True)
		print '***************'
		print 'Command:',' '.join(['python','conveyor_cmdline_client.py','-c','conveyor-debian.conf','print',fileName,'--has-start-end'])
		print '***************'
	else:
		subprocess.Popen(['python','conveyor_cmdline_client.py','-c','conveyor-debian.conf','print',fileName,'--has-start-end'], stdin = None, stdout = None, stderr = None, close_fds=True)
		print '***************'
		print 'Command:',' '.join(['python','conveyor_cmdline_client.py','-c','conveyor-debian.conf','print',fileName,'--has-start-end'])
		print '***************'
		sys.path = sys.path[2:]
	os.chdir(currPath)

#unused function - you can delete this, but is a good example of cmdline call
def findPrinter():
	global pathsAdded 
	print 'attempting to connect to 3d printer'		
	currPath = os.getcwd()
	os.chdir('/home/pi/raspi/makerbot/conveyor')
	if not pathsAdded:
		sys.path.insert(0,'./virtualenv/local/lib/python2.7/site-packages/pyserial-2.7_mb2.1-py2.7.egg')
		sys.path.insert(0,'./virtualenv/lib/python2.7/site-packages/pyserial-2.7_mb2.1-py2.7.egg')
		pathsAdded = True
		for i in sys.path:
			print i
	#pull info from the pipe
	p2 = subprocess.Popen(['python','conveyor_cmdline_client.py','-c','conveyor-debian.conf','connect'], stdin = None, stdout = subprocess.PIPE, stderr = None, close_fds=True)

	#p2 = subprocess.Popen(['python','conveyor_cmdline_client.py','-c','conveyor-debian.conf','ports'], stdin = None, stdout = subprocess.PIPE, stderr = None, close_fds=True)
	#output = p2.stdout.read()
	#print output
	#output.find('iSerial -')



	os.chdir(currPath)




def cancelCurrent():
	pass

if __name__ == '__main__':
	printFile('')


#def cancelFile(fileName)

