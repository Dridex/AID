#!/usr/bin/python

"""
Advanced Issue Detection - master script. 
Collates data from controllers which are pulling data from agents.
Handles all DB operations. 
"""

__author__ = "Jack Rutherford"
__date__ = "2017-12-05"

# Python imports
import logging
import logging.config
import json
import re
import requests
import sys
import time
import threading
import zlib

# Custom imports
import helperMaster

## Global variables
# Set up logging files
logging.config.fileConfig('/opt/scripts/aid-master/etc/logging.conf')
logger = logging.getLogger('aidMaster.py')

# Set directories for aid controller configs
conf_dir = ('/opt/scripts/aid-master/etc/')
status_dir = ('/opt/scripts/aid-master/status/')


# Handle creation of threads for agent checks
class SpawnAgent(threading.Thread):
	
	def __init__(self, host_info):
		
		self.host = host_info['IP']
		self.port = host_info['port']
		self.hostname = host_info['hostname']
		self.proxy = host_info['proxy']
		self.method = host_info['method']
		threading.Thread.__init__(self)

	def run(self):
	
		while True:
			
			req_stat = ''

			# Set up logging, make request for agent
			logger.info("Requesting check of controller " + self.host)

			try:
				if self.proxy == 'NULL' and self.method == 'IP':
					r = requests.get('http://' + self.host + ':' + self.port + '/controller-update')
				elif self.proxy == 'NULL' and self.method == 'Host':
					r = requests.get('http://' + self.hostname + ':' + self.port + '/controller-update')
				elif self.proxy != 'NULL' and self.method == 'IP':
					proxies = {'http' : 'http://' + self.proxy['username'] + ':' + self.proxy['password'] + '@' + self.proxy['address']}
					r = requests.get('http://' + self.host + ':' + self.port + '/controller-update', proxies=proxies)
				elif self.proxy != 'NULL' and self.method == 'Host':
					proxies = {'http' : 'http://' + self.proxy['username'] + ':' + self.proxy['password'] + '@' + self.proxy['address']}
					r = requests.get('http://' + self.hostname + ':' + self.port + '/controller-update', proxies=proxies)
				else:
					raise Exception('Error contacting controller due to malformed request. Perhaps a problem with controllers.conf')

				content = json.loads(r.content)

				# Decrypt and decompress the data field of the response content
				decrypted = helperMaster.decrypt(content['data'])
				decompressed = zlib.decompress(decrypted)
				host_list = json.loads(decompressed)
				cont_hostname = self.hostname
				host_status_list = host_list[1:]
				req_stat = 'SUCCESS'

			except Exception, why:
				logger.error('Unable to make request to controller at \'' + self.host + '\': %s' % why)
				req_stat = 'FAIL'

			if req_stat == 'SUCCESS':
			
				# Check if controller exists in DB already
				controller = helperMaster.queryHost(self.host, 'NULL')

				logger.info('Request was success.')

				if not controller:
					# Insert controller into database
					# Null argument is because controllers don't have parents. Like Batman.
					helperMaster.insertAidHost(cont_hostname, 'UP', self.host, '')
					controller = helperMaster.queryHost(self.host, 'NULL')
			
				# Set the controller status to up if it was previous down	
				cont_status = controller[0][2]
				cont_hostname = controller[0][1]
				if cont_status == 'DOWN':
					helperMaster.updateHost(cont_hostname, 'UP', self.host, 'NULL')

				# Loop through hosts in controllers zone
				for host_results in host_status_list:

					hostname = host_results['hostname']
					status_list = host_results['check_results']
					IP = host_results['IP']

					# Get the controller information for this host to be used later
					controllerUID = ''
					if controller:
						controllerUID = controller[0][0]
					
					# Check if host exists in DB, [] if no
					host_info = helperMaster.queryHost(IP, controllerUID)
					hostUID = []

					if not host_info:
						if 'ERROR' in hostname:
							status = 'DOWN'
							split = hostname.split(' ')
							hostname = split[-1]
							logger.error('Host ' + IP + ' is not contactable. Haven\'t seen this host before.')
						else:
							status = 'UP'
						helperMaster.insertAidHost(hostname, status, IP, controllerUID)
						host_info = helperMaster.queryHost(IP, controllerUID)
						hostUID = host_info[0][0]
					else:
						hostUID = host_info[0][0]	
						if 'ERROR' in hostname:
							status = 'DOWN'
							split = hostname.split(' ')
							hostname = split[-1]
							logger.error('Host ' + IP + ' has died. Setting all services to down.')
							helperMaster.setServicesDown(hostUID)
						else:
							status = 'UP'
						helperMaster.updateHost(hostname, status, IP, controllerUID)
					
					# Process all the services for this host. If host is down, this will skip because list will be empty	
					for service in status_list:
						
						# split the service name and output
						split = service.split(';')
						try:
							service_state = int(split[0])
						except:
							logger.error('Was give a non-integer in service state field... Not cool')
							service_state = 2
						service_name = split[1]
						service_args = split[2]
						service_output = split[3:]
				
						service_output_str = ' '.join(service_output)
	
						# Check if service exists in DB
						service_db_info = helperMaster.queryService(service_name, service_args, hostUID)
						logger.info('Service_db_info: ' + str(service_db_info))
						
						# If service doesn't exist, add it. Otherwise, compare DB status to checked status
						if not service_db_info:
							helperMaster.insertService(service_name, service_args, service_state, hostUID, service_output_str)
						else:
							service_db_state = service_db_info[0][2]
							service_db_output = service_db_info[0][4]
						
							if (service_db_state != service_state) or (service_db_output != service_output_str):
								helperMaster.updateService(service_name, service_args, hostUID, service_state, service_output_str)

			elif req_stat == 'FAIL':
				# Find all hosts belonging to that controller and set status to DOWN (including controller itself)
				logger.critical('Request to controller \'' + self.host + '\' failed, controller is down.')
				dead_controller = helperMaster.getContID(self.host)
				if dead_controller == []:
					logger.critical('Dead controller not in database yet. Skipping setting hosts / services to down.')
				else:
					dc_id = dead_controller[0][0]
					helperMaster.setHostsDown(dc_id)

					# Find all services for all hosts, set services to down
					hosts = helperMaster.getHostIDs(dc_id)
					for host in hosts:
						helperMaster.setServicesDown(host[0])
				
			else: 
				# SOMETHING WENT HORRIBLY WRONG	
				logger.critical('Request status was not a success nor a fail. This should never happen. WHAT IS GOING ON.')

			# Wait 30 seconds before checking again
			time.sleep(30)
		

# Return a unique list of hosts in a common format from the agents config file
def get_conts():

	try:
		# Read the proxy file details in
		with open(conf_dir+'proxy.conf') as f2:
			lines_p = f2.readlines()
	except FileNotFoundError:
		logger.critical('proxy.conf file does not exist in ' + conf_dir)
	except Exception, why: 
		logger.critical("Reading proxy config failed: %s" % why)

	proxy_details = {}

	for l in lines_p:
		line_p = l.strip()
		if 'Username' in line_p:
			start = '<Username>'
			end = '</Username>'
			proxy_details['username'] = line_p[len(start):-len(end)]
		elif 'Password' in line_p:
			start = '<Password>'
			end = '</Password>'
			proxy_details['password'] = line_p[len(start):-len(end)]
		elif '<Address>' in line_p:
			start = '<Address>'
			end = '</Address>'
			proxy_details['address'] = line_p[len(start):-len(end)]

	if proxy_details['username'] == 'REPLACEME' or proxy_details['username'] == '':
		logger.info('No proxy details specified - continuing.')

	try:
		# read in config file that defines controllers to check
		with open(conf_dir+'controllers.conf') as f:
			lines = f.readlines()
	except FileNotFoundError:
		logger.critical('controllers.conf file does not exist in ' + conf_dir)
	except Exception, why: 
		logger.critical("Reading controller config failed: %s" % why)

	addrs = []

	# Ensure first character of line is a number
	for line in lines:
		if re.match("^[0-9]", line):
			cont_dirty = line.split(';')
			cont = []
			for cd in cont_dirty:
				cont.append(cd.strip())
			IPPort = cont[0].split(':')
			IP = IPPort[0]
			port = IPPort[1]
			cont_d = {'IP' : IP, 'port' : port, 'hostname' : cont[1], 'method' : cont[3]}
			if cont[2] == 'True':
				cont_d['proxy'] = proxy_details
			else:
				cont_d['proxy'] = 'NULL'
			addrs.append(cont_d)

	# Unique the list of controllers (IP addresses must be unique)
	seen = []
	uhosts = []
	index = 0 
	for index in range(0, len(addrs)):
		if addrs[index]['IP'] not in seen:
			seen.append(addrs[index]['IP'])
			uhosts.append(addrs[index])
		index += 1

	return uhosts


if __name__ == "__main__":

	conts = get_conts()

	# Spawn threads to handle controller checks (1 thread per controller)
	try:
		for cont in conts:
			contThread = SpawnAgent(cont)
			contThread.start()
	except Exception, why:
		logger.critical("Thread failed: %s" % why)
		sys.exit(1)
