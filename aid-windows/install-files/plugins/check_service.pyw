#!/usr/bin/python

import subprocess
import sys

# Define return codes
UNKNOWN = -1
OK = 0
WARNING = 1
CRITICAL = 2

try:
	service = sys.argv[1:]
	service = ' '.join(service)
except:
	print 'ERROR - Please give an arg for service to check'
	raise SystemExit, CRITICAL
	
	
cmd = 'net start | find "' + service + '"'
proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
for line in proc.stdout:

	if service in line:
		print "OK - %s service is running" % (service)
		raise SystemExit, OK

			
print "CRITICAL - %s service is not running" % (service)
raise SystemExit, CRITICAL

