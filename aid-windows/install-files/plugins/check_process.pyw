#!/usr/bin/python

import subprocess
import sys

# Define return codes
UNKNOWN = -1
OK = 0
WARNING = 1
CRITICAL = 2

try:
	process = sys.argv[1]
except:
	print 'ERROR - Please give an arg for which mount point to check'
	raise SystemExit, CRITICAL
	
try:
	
	cmdLineContains = sys.argv[2]
except:
	cmdLineContains = ''
	
cmd = 'WMIC PROCESS get Caption,Commandline'
proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
for line in proc.stdout:
	if line.strip() == '':
		continue
	
	p = line.split()[0]
	c = line.split()[1:]
	c = ''.join(c)
	
	if p == process:
		if cmdLineContains == '' or cmdLineContains in c:
			print "OK - %s is running with %s in cmd" % (process, cmdLineContains)
			raise SystemExit, OK

			
print "CRITICAL - %s is not running or not with %s in cmd" % (process, cmdLineContains)
raise SystemExit, CRITICAL

