import subprocess
import sys
import os

import re
import subprocess
def scanUSB():
	device_re = re.compile("Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<id>\w+:\w+)\s(?P<tag>.+)$", re.I)
	df = subprocess.check_output("lsusb", shell=True)
	devices = []
	for i in df.split('\n'):
	    if i:
	        info = device_re.match(i)
	        if info:
	            dinfo = info.groupdict()
	            dinfo['device'] = '/dev/bus/usb/%s/%s' % (dinfo.pop('bus'), dinfo.pop('device'))
	            devices.append(dinfo)
	            if dinfo['id'] == '23c1:b015': 
	            	print 'found a Replicator2!'
	            	print dinfo['device']

#	print devices



if __name__ == '__main__':
	scanUSB()

#def cancelFile(fileName)
