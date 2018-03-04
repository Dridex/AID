#!/usr/bin/python

import subprocess
import sys

try:
	mount = sys.argv[1]
except:
	print 'ERROR - Please give an arg for which mount point to check'
	sys.exit(2)

df = subprocess.Popen(['df','-h',mount], stdout = subprocess.PIPE)
grep = subprocess.Popen(['grep','-v','Filesystem'], stdin = df.stdout, stdout = subprocess.PIPE)
awk = subprocess.Popen(['awk','{print $5}'], stdin = grep.stdout, stdout = subprocess.PIPE)

newline_space = awk.communicate()[0]
used_perc = newline_space.strip()
used_space = int(used_perc.split('%')[0])

if used_space <= "80":
	print "OK - %s%% of disk space used." % used_space
	sys.exit(0)
elif used_space < "90":
	print "WARNING - %s%% of disk space used." % used_space
	sys.exit(1)
elif used_space >= "90":
	print "CRITICAL - %s%% of disk space used." % used_space
	sys.exit(2)
else:
	print "UNKNOWN - %s%% of disk space used." % used_space
	sys.exit(3)
