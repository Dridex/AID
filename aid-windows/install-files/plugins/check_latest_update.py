#!/usr/bin/python

import subprocess
import sys
import datetime

# Define return codes
UNKNOWN = -1
OK = 0
WARNING = 1
CRITICAL = 2

cmd = 'wmic qfe list'
proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
for line in proc.stdout:
	if line.strip() == '':
		continue
		
	l = line.replace('y U','y-U')
	l = l.replace('NT A','NT-A')
	
	p = l.split()
	
	if p[5] == "InstallDate":
		continue
	
	d = datetime.datetime.strptime(p[5],'%m/%d/%Y')
	
	if d > datetime.datetime.now()-datetime.timedelta(days=30):
		# in most recent 30 days
			print "OK - An update was installed in the last 30 days." 
			raise SystemExit, OK
			
print "CRITICAL - An update has not been installed in the last 30 days" 
raise SystemExit, CRITICAL

