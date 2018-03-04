#!/usr/bin/python

import subprocess
import sys

try:
	program = sys.argv[1]
	
except:
	print 'ERROR - Please give a process name to check'
	sys.exit(2)

ps = subprocess.Popen(['ps','aux'], stdout = subprocess.PIPE)
grep = subprocess.Popen(['grep','-i',program,], stdin = ps.stdout, stdout = subprocess.PIPE)
grepv = subprocess.Popen(['grep','-v','grep'], stdin = grep.stdout, stdout = subprocess.PIPE)
grepv2 = subprocess.Popen(['grep','-v','check_procs.py'], stdin = grepv.stdout, stdout = subprocess.PIPE)

newline = grepv2.communicate()[0]
procs = newline.strip()

proc_list = procs.split('\n')
proc_count = len(proc_list)

if proc_count == 1 and proc_list[0] == '':
	proc_count = 0

if proc_count >= 1:
	print "OK - %s processes containing name \'%s\'" % (proc_count,program)
	sys.exit(0)
elif proc_count == 0:
	print "CRITICAL - %s processes containing name \'%s\'" % (proc_count,program)
	sys.exit(2)
