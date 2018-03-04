#!/usr/bin/python
"""
Advanced Issue Detection (linux) - a monitoring agent. 
Runs checks on a Linux system to check that everything is working. 
The checks are executed using plugins and are defined in a config file.
Runs as an agent (service/daemon) as a web server and waits for requests
from an AID controller, then executes the checks and returns the results.
"""

__author__ = "Jack Rutherford"
__date__ = "2017-12-05"

# Python imports
import logging
import logging.config
import json
import subprocess
import socket
import re

# Partial imports
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from os import listdir
from os.path import isfile, join 


# Root dir
root_dir = '/opt/scripts/aid/'

# Set up logging files
logging.config.fileConfig(root_dir + 'etc/logging.conf')
logger = logging.getLogger('aidAgent.py')

# Set directories for aid stuff
plugin_dir = root_dir + 'plugins/'
conf_dir = root_dir + 'etc/'


# HTTP server to handle GET requests only
class ServerHandler(BaseHTTPRequestHandler):

	def do_GET(self):
		"""
		Handle get requests from the AID controller or otherwise
		"""

		response = {'success' : True, 'message' : 'Results incoming.', 'data' : ''}
		data = []

		logger.info('Making request to self for updates...')

		if self.path == '/agent-update':
			data = check_services()
			
			if data == []:
				response['success'] = False
				response['message'] = 'No data found - service checks failed.'
				response['data'] = ''
				logger.error('Recevied no data from service checks.. something went wrong.')
			else:
				hostname = socket.gethostname()
			
				if hostname == '':
					hostname = 'null'
				
				final_data = {'hostname':hostname}
				final_data['check_results'] = data
				response['data'] = final_data

			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self.end_headers()
			self.wfile.write(json.dumps(response))
			self.wfile.close()
			logger.info('Request complete.')

		elif self.path == '/sysinfo':
			hostname = socket.gethostname()
			if hostname == '': 
				hostname = 'null'
			data = check_sysinfo(hostname)
			if data == []:
				response['success'] = False
				response['message'] = 'No data found - systeminfo checks failed.'
				response['data'] = ''
				logger.error('Recevied no data from systeminfo checks.. something went wrong.')
			else:
				final_data = {'hostname':hostname}
				final_data['sysinfo_results'] = data
				response['data'] = final_data

			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self.end_headers()
			self.wfile.write(json.dumps(response))
			self.wfile.close()
			logger.info('Request complete.')

		else:
			self.send_error(500, 'YOU DIDNT GIVE ME WHAT I WANTED!')
			logger.error('Received request for invalid path')



class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
		'''Handle requests in a separate thread.'''


# spawn service check
def check_services():
	"""
	Called when a GET request is received to the check_services URI.
	Parses the config file, then executes the checks defined in the 
	config file and returns the results.
	"""
	
	# read in config file that defines which checks to perform for this host	
	with open(conf_dir+'aid.conf') as f:
		lines = f.readlines()

	# List containing checks defined in config file
	checks_alpha = []

	# clean the input from aid.conf
	for line in lines:
		if line[0].isalpha() or line[0] == '/' or line[0] == '.':
			checks_alpha.append(line)

	# chomp trailing whitespace
	checks = [c.rstrip() for c in checks_alpha]

	output = []

	# Execute checks
	for check in checks:

		split = check.split()
		program = split[0]

		# check if binary execution or other program
		if program.startswith('./'):
			script = split[0]
			script = script[2:]
			args = split[1:]
		else:
			script = split[1]
			args = split[2:]

		# build subprocess command to execute
		script_path = plugin_dir + script
		check_stat = {'name':script}
		check_stat['args'] = args
		if program.startswith('./'):
			subp_line = [script_path] + args
		else:
			subp_line = [program, script_path] + args

		# execute command
		try:
			proc_out = subprocess.check_output(subp_line)
			check_stat['output'] = proc_out
			check_stat['exit_code'] = 0
			logger.info('Script executed successfully: ' + script_path + ': ' + proc_out.strip())
					
		except subprocess.CalledProcessError as e:
			check_stat['output'] = e.output
			if check_stat['output'] == '':
				check_stat['output'] = 'No warning/error message provided\n'
			check_stat['exit_code'] = e.returncode
			if e.returncode == 1:
				logger.warn('Script exited with a warning: ' + program + ' ' + script_path + ': ' + e.output.strip())
			elif e.returncode == 2:
				logger.error('Script exited with an error: ' + program + ' ' + script_path + ': ' + e.output.strip())
			else:
				logger.error('Script exited with unknown return code: ' + program + ' ' + script_path + ': ' + e.output.strip())

		output.append(check_stat)

	if len(output) != len(checks): 
		logger.warning('Number of items in output does not match number of checks made. Maybe something went wrong?')
		logger.warning('Check that all scripts called exist in aid plugins directory.')

	return output


# Check system info about the host to be auto-imported into the wiki
def check_sysinfo(hostname):
	"""
	Called when a GET request is received to the sysinfo URI.
	Executes a number of commands to find out system info. If 
	the commands fail, empty string is returned for that item.
	"""

	# read in config file that defines which checks to perform for this host	
	with open(conf_dir+'sysinfo.conf') as f:
		syslines = f.readlines()

	# List containing checks defined in config file
	sysinfo_alpha = []

	# clean the input from sysinfo.conf
	for line in syslines:
		if line[0].isalpha() or line[0] == '/' or line[0] == '.':
			checks_alpha.append(line)

	# chomp trailing whitespace
	syschecks = [c.rstrip() for c in sysinfo_alpha]

	sysoutput = []

	# Execute checks
	for check in syschecks:

		split = check.split()
		program = split[0]

		# check if binary execution or other program
		if program.startswith('./'):
			script = split[0]
			script = script[2:]
			args = split[1:]
		else:
			script = split[1]
			args = split[2:]

		# build subprocess command to execute
		script_path = plugin_dir + script
		check_stat = {'name':script}
		check_stat['args'] = args
		if program.startswith('./'):
			subp_line = [script_path] + args
		else:
			subp_line = [program, script_path] + args

		# execute command
		try:
			proc_out = subprocess.check_output(subp_line)
			check_stat['output'] = proc_out
			check_stat['exit_code'] = 0
			logger.info('Sysinfo script executed successfully: ' + script_path + ': ' + proc_out.strip())

		except subprocess.CalledProcessError as e:
			check_stat['output'] = e.output
			if check_stat['output'] == '':
				check_stat['output'] = 'No warning/error message provided\n'
			check_stat['exit_code'] = e.returncode
			if e.returncode == 1:
				logger.warn('Script exited with a warning: ' + program + ' ' + script_path + ': ' + e.output.strip())
			elif e.returncode == 2:
				logger.error('Script exited with an error: ' + program + ' ' + script_path + ': ' + e.output.strip())
			else:
				logger.error('Script exited with unknown return code: ' + program + ' ' + script_path + ': ' + e.output.strip())

		sysoutput.append(check_stat)

	if len(sysoutput) != len(syschecks):
		logger.warning('Number of items in output does not match number of checks made. Maybe something went wrong?')
		logger.warning('Check that all scripts called exist in aid plugins directory.')


	return sysoutput


if __name__ == '__main__':

	server = ThreadedHTTPServer(('', 8666), ServerHandler)
	logger.info('Starting httpd...')
	server.serve_forever()

