#!/usr/bin/python

"""
AID Controller makes requests to all the hosts in it's zone, as defined by a config file in ./etc/
The controller only has the ability to make requests to hosts on the same subnet.
Results from the requests are stored in text files that indicate the UP/DOWN status of the host,
and if up, the status of the checks.

Each controller also handles requests from AID Master. AID Controller simply reads the text files 
and returns the results in a HTTP response.
"""

__author__ = "Jack Rutherford"
__date__ = "2017-12-07"


# Python imports
import logging
import logging.config
import json
import SocketServer
import socket
import threading
import re
import requests
import sys
import time
import os
import zlib

# Custom imports
import helperController

# Partial imports
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from datetime import datetime


## Global variables
# Set up logging files
logging.config.fileConfig('/opt/scripts/aid-controller/etc/logging.conf')
logger = logging.getLogger('aidController.py')

# Set directories for aid controller configs
conf_dir = ('/opt/scripts/aid-controller/etc/')
status_dir = ('/opt/scripts/aid-controller/status/')
sysinfo_dir = ('/opt/scripts/aid-controller/sysinfo/')


class SpawnSysAgent(threading.Thread):
	"""
	Spawn a thread to handle checking of system information for hosts
	"""
	
	def __init__(self, hosts_list):
		
		self.host_list = hosts_list
		threading.Thread.__init__(self)

	def run(self):
	
		while True:

			for host in self.host_list:

				hostname = host['hostname']
				IP = host['IP']

				logger.info("Requesting sysinfo check of agent at " + IP)
				host_state = ''
				host_sysinfo_path = sysinfo_dir + str(IP)

				# Check if host is up or down
 				try:
 					r = requests.get('http://' + IP + ':8666/sysinfo')
 					host_state = 'UP'
 				except Exception, why:
 					logger.error('Connection to host \'' + IP +'\' failed: %s' % why)
 					host_state = 'DOWN'
 
 				if host_state == 'UP':
					content = json.loads(r.content)
					# if state change, remove old file
					if os.path.isfile(host_sysinfo_path):
						os.remove(host_sysinfo_path)

					sysinfo_data = content['data']

					f = open(host_sysinfo_path,'w')
					f.write('hostname : ' + sysinfo_data['hostname'] + '\n')
					for result in sysinfo_data['sysinfo_results']:
						f.write(result + ' : ' + str(sysinfo_data["sysinfo_results"][result]) + '\n')
					f.write('LastUpdate : ' + str(datetime.now()) + '\n')
					f.close()
					logger.info('Results for ' + IP + ' written to file')

 				elif host_state == 'DOWN':
 					# Set somethings to NULL... I'll get there
					print 'CANNOT CONTACT HOST DEAR LORD WHAT SHALL WE DO'
 				else:
 					logger.critical("Umm this should be impossible mayday mayday alert alert host state is NOTHING")
			time.sleep(30)
	

class SpawnAgent(threading.Thread):
	"""
	#Spawn a thread per host to handle service checking. Makes the check
	#then waits a number of seconds as defined in the AID config file
	"""

	def __init__(self, host_info):
		
		self.host = host_info['IP']
		self.freq = host_info['freq']
		self.hostname = host_info['hostname']
		threading.Thread.__init__(self)

	def run(self):
	
		while True:

			logger.info("Requesting check of agent " + self.host)
			host_state = ''
			host_up_path = status_dir + str(self.host) + '-' + 'UP'
			host_down_path = status_dir + str(self.host) + '-' + 'DOWN'

			# Check if host is up or down
			try:
				r = requests.get('http://' + self.host + ':8666/agent-update')
				host_state = 'UP'
			except Exception, why:
				logger.error('Connection to host \'' + self.host +'\' failed: %s' % why)
				host_state = 'DOWN'
			
			if host_state == 'UP':

				# Get the content of the response from the host we're checking
				content = json.loads(r.content)

				# if state change, remove old file
				if os.path.isfile(host_down_path):
					os.remove(host_down_path)
				
				# Write the results of the request to file (w/ filename as IP of agent)
				# Will overwrite previous state file if it exists, which is fine
				cont_data = content['data']

				f = open(host_up_path,'w')
				f.write(self.hostname + '\n')
				for result in cont_data['check_results']:
					f.write(str(result['exit_code']) + ';' + result['name'] + ';' + ' '.join(result['args']) + ';' +  result['output'])
				f.close()

			elif host_state == 'DOWN':

				# if state change, remove old file
				if os.path.isfile(host_up_path):
					os.remove(host_up_path)

				# Write error to file
				f = open(host_down_path, 'w')
				f.write('ERROR: Unable to make requeset to ' + self.hostname)
				f.close()

			# Wait x seconds before checking again
			time.sleep(self.freq)


# HTTP server to handle GET requests only
class ServerHandler(BaseHTTPRequestHandler):
	"""
	Handle GET requests from AID Master and return results from checks
	stored on disk
	"""

	def do_GET(self):

		response = {'success' : True, 'message' : "Request successful", 'data' : ''}
		data = []

		if self.path == "/controller-update":

			# Retrieve results to return to master
			data = cont_update()
		else:
			self.send_error(500, 'YOU DIDNT GIVE ME WHAT I WANTED!')
			logger.error('Received request for invalid path')

		if data == []:
			response["success"] = False
			response["message"] = "No data found - service checks failed."
			response["data"] = ''
			logger.error('Recevied no data from service checks.. something went wrong.')
		else:
			response["data"] = helperController.encrypt(zlib.compress(json.dumps(data)))

		# Send the response back with all the data
		self.send_response(200)
		self.send_header("Content-type", "application/json")
		self.end_headers()
		self.wfile.write(json.dumps(response))
		self.wfile.close()
		logger.info('Request complete.')


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
		  """Handle requests in a separate thread."""


def cont_update():
	"""
	Get latest service data from status files to give to master
	"""
	
	results = []
	hosts = []

	config = get_hosts()
	for d in config:
		hosts.append(d['IP'])

	# This piece of code is obsolete and does nothing but I'd have to change the 
	# structure of the data if I removed it so no thank you sir.
	cont_hostname = socket.gethostname()
	if cont_hostname == '':
		cont_hostname = 'null'
	results.append(cont_hostname)

	for host in hosts:

		status_file = ''

		if os.path.isfile(status_dir + host + '-UP'):
			status_file = status_dir + host + '-UP'
		elif os.path.isfile(status_dir + host + '-DOWN'):
			status_file = status_dir + host + '-DOWN'
		
		if status_file == '':
			logger.warning('Unable to determine status file path for ' + host + '. If controller was just restarted, file may have not been written yet, and this is fine because it will be picked up later. If this is not the case, you might be in trouble buddy.')
		else:
			try:
				# read status file for host
				with open(status_file) as f:
					lines = f.readlines()
				
				# Append hostname, then append list of check results
				results_dict = {'hostname':lines[0].rstrip()}
				checks = lines[1:]
				results_dict['check_results'] = ([v.rstrip() for v in checks])
				results_dict['IP'] = host
				results.append(results_dict)

			except Exception, why: 
				logger.critical('Reading status file for ' + host + ' failed: %s' % why)

	logger.debug('Results list: ' + str(results))	
	return results
	

def get_hosts():
	"""
	Return a unique list of hostnames/ip addresses from the agents config file
	"""

	try:
		# read in config file that defines hosts (agents) to check	
		with open(conf_dir+'agents.conf') as f:
			lines = f.readlines()
	except FileNotFoundError:
		logger.critical('agents.conf file does not exist in ' + conf_dir)
	except Exception, why: 
		logger.critical("Reading config failed: %s" % why)

	addrs = []

	# Ensure first character of line is number
	for line in lines:
		if re.match("^[0-9]", line):
			agent = line.split(';')
			agent_d = {'IP' : agent[0].strip(), 'hostname' : agent[1].strip(), 'freq' : agent[2].strip(), 'sysinfo' : agent[3].strip()}
			addrs.append(agent_d)

	# Unique the list of hosts (only 1 instance of an IP may exist per zone)
	seen = []
	uhosts = []
	index = 0
	for index in range(0, len(addrs)):
		if addrs[index]['IP'] not in seen:
			seen.append(addrs[index]['IP'])
			uhosts.append(addrs[index])
		index += 1

	# Clean the input to avoid errors later down the track
	for d in uhosts:
		try:
			d['freq'] = int(d['freq'])
		except:
			logger.warn('Integer not given for frequency field in agents.conf, defaulting to 15 seconds.')
			d['freq'] = 15

	return uhosts


if __name__ == "__main__":

	# Clean and re-initialise status directory from config file before starting
	# This automates removal of old hosts / IPs
	for the_file in os.listdir(status_dir):
		file_path = os.path.join(status_dir, the_file)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
		except Exception as e:
			logger.error('Error deleting old status files: %s' % e)

	mhosts = get_hosts()

	# Spawn threads to handle agent checks
	# 1 thread per agent for service checks
	# 1 thread for all sysinfo checks
	try:
		for entry in mhosts:
			agentThread = SpawnAgent(entry)
			agentThread.start()

		sys_list = []
		for entry in mhosts:
			if entry['sysinfo'] == 'Y':
				sys_list.append(entry)
		sysThread = SpawnSysAgent(sys_list)
		sysThread.start()
		
	except Exception, why:
		logger.critical("Thread failed: %s" % why)
		sys.exit(1)

	# Start HTTP server to handle requests from master to get results for controller zone
	server = ThreadedHTTPServer(('', 8866), ServerHandler)
	logger.info('Starting controller server...')
	server.serve_forever()
