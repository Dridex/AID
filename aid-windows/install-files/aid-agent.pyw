# Python imports
import logging
import logging.config
import subprocess
import socket

# Partial imports
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from os import listdir
from os.path import isfile, join
from json import dumps


# Set up logging files
logging.config.fileConfig("C:\Program Files\AID\etc\logging.conf")
logger = logging.getLogger('aid-agent.pyw')

# Set directories for aid stuff
plugin_dir = "C:\Program Files\AID\plugins\\"
conf_dir = "C:\Program Files\AID\etc\\"


# HTTP server to handle GET requests only
class ServerHandler(BaseHTTPRequestHandler):

	def do_GET(self):

		response = {'success' : True, 'message' : "Results incoming.", 'data' : ''}
		data = []

		if self.path != "/agent-update":
			self.send_error(500, 'YOU DIDNT GIVE ME WHAT I WANTED!')
			logger.error('Received request for invalid path')
		else:
			data = check_services()

			if data == []:
				response["success"] = False
				response["message"] = "No data found - service checks failed."
				response["data"] = ''
				logger.error('Recevied no data from service checks.. something went wrong.')
			else:
				hostname = socket.gethostname()
				if hostname == '':
					hostname = 'null'

				final_data = {'hostname':hostname}
				final_data['check_results'] = data
				response["data"] = final_data

		self.send_response(200)
		self.send_header("Content-type", "application/json")
		self.end_headers()
		self.wfile.write(dumps(response))
		self.wfile.close()
		logger.info('Request complete.')


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""


# spawn service check
def check_services():
	
	# read in config file that defines which checks to perform for this host	
	with open(conf_dir+'aid.conf') as f:
		lines = f.readlines()

	checks_alpha = []

	# clean the input from aid.conf
	for line in lines:
		if line[0].isalpha():
			checks_alpha.append(line)

	# chomp trailing whitespace
	checks = [c.rstrip() for c in checks_alpha]

	# get file listing for plugins directory; remove extensions
	plugins = [f for f in listdir(plugin_dir) if isfile(join(plugin_dir, f))]

	output = []
	python_path = "C:\Python27\pythonw.exe"

	# Execute checks
	for check in checks:

		split = check.split()
		script = split[0]
		args = split[1:]
		check_stat = {'name':script}
		check_stat['args'] = args
		script_path = plugin_dir + script

		program = []
		if script[-3:] == '.py' or script[-4:] == '.pyw':
			program.append(python_path)

		try:
			proc_out = subprocess.check_output(program + [script_path] + args)
			check_stat['output'] = proc_out
			check_stat['exit_code'] = 0
			logger.info('Script executed successfully: ' + script_path + ': ' + proc_out.strip())

		except subprocess.CalledProcessError as e:
			check_stat['output'] = e.output
			check_stat['exit_code'] = e.returncode
			if check_stat['output'] == '': 
				check_stat['output'] = 'No warning/error message provided\n'
			if e.returncode == 1:
				logger.warn('Script exited with a warning: ' + script_path + ': ' + e.output.strip())
			elif e.returncode == 2:
				logger.error('Script exited with an error: ' + script_path + ': ' + e.output.strip())
			else:
				logger.error('Script exited with unknown return code: ' + program + ' ' + script_path + ': ' + e.output.strip())

		output.append(check_stat)

	if len(output) != len(checks): 
		logger.warning('Number of items in output does not match number of checks made. Maybe something went wrong?')
		logger.warning('Check that all scripts called exist in aid plugins directory.')

	return output


if __name__ == "__main__":

		server = ThreadedHTTPServer(('', 8666), ServerHandler)
		logger.info('Starting httpd...')
		server.serve_forever()
