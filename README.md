Advanced Issue Detection (AID). 

Developed as a solution to monitor systems and software for faults and errors.

Runs as a 3-tiered system, with the 3 components being: 

* aid-agent.py - the agent running on every host that needs checking. Comes with 
a number of plugins out of the box to check system services and logs on both Linux
and Windows. Checks are defined in a config file. Runs as a python webserver on
port 8666, and will execute the checks when a GET request to the correct URI is 
performed by a controller. It will then return the results of the checks in JSON.

* aid-controller.py - intended to manage 'zones' in an environment, i.e. is not 
firewall or proxy aware (this is the masters job). Has a config file that defines
all host in a zone that have an agent, and will make requests to the agent for 
the status of various checks at a default or defined frequency. Multi-threaded, 
spawning 1 thread per host in the environment. Results of the checks will be 
stored in a number of status files on disk. The controller is also a python
web server, running on port 8866, that can receive requests from a specific URI 
from the master, then return the bundled results of all hosts in a zone.

* aid-master.py - collects results from all controllers. Can be configured with 
proxy awareness and can retrieve results from hostnames or IP addresses. Parses
the JSON results from each controller and updates the DB, in which there is a 
Hosts table and a Services table, each with an indication of status (UP / DOWN).
All communication between the master and the controller is compressed, then 
encrypted. 
