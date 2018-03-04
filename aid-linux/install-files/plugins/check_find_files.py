#!/usr/bin/python

import sys


def printHelp():
	print 'This script will check a log file for errors or warnings, and print output and exit code accordingly.'
	print 'Main purpose is as a Nagios / AID plugin.'
	print ''
	print 'USAGE: '
	print '\t $ python check_logs.py <logfile>'


if len(sys.argv) < 2:
	print 'ERROR - not enough arguements given.'
	printHelp()
	sys.exit(2)


logfile = sys.argv[1]
try:
	with open(logfile, 'r') as f:
		lines = f.readlines()
except:
	print 'ERROR - Could not open log file. Check the path / permissions.'
	sys.exit(2)

crits = []
errs = []
warns = []

for line in lines:
	split = line.split(' - ')
	if split[2] == 'CRITICAL':
		crits.append(line)
	elif split[2] == 'ERROR':
		errs.append(line)
	elif split[2] == 'WARNING': 
		warns.append(line)


# find errors
#errors = []
#e_pattern = r"ERROR"
#for match in re.finditer(e_pattern, lines):
#	errors.append(match.group(0))

# find crits
#c_pattern = r"CRITICAL"
#for match in re.finditer(c_pattern, lines):
#	errors.append(match.group(0))

# find warnings
#warnings = []
#w_pattern = r"WARNING"
#for match in re.finditer(w_pattern, lines):
#	warnings.append(match.group(0))

if (len(errs) >= 1) or (len(crits) >= 1):
	print "CRITICAL - %s errors/crits in log file: %s" % ((len(errs)+len(crits)),logfile)
	sys.exit(2)
elif len(warns) >= 1:
	print "WARNING - %s warnings in log file: %s" % (len(warns),logfile)
	sys.exit(1)
else:
	print "OK - No errors or warnings in log file \'%s\'" % (logfile)
	sys.exit(0)

