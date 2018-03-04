#!/bin/bash

if [ "$EUID" -ne 0 ]
then 
	echo "Please run as root"
	exit
fi

read -p "If AID-Agent is already installed, this will overwrite everything, including the config. ARE YOU SURE YOU WANT TO PROCEED? [y/n]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then

  echo "Checking version of python..."
  pv=`python -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' | grep 2.7`
  if [ -z $pv ]; then
     echo "Python 2.7 not installed or not default... please install python2.7"
     exit
  else
     echo "Python 2.7 installed and default. Continuing."
  fi
  
  mkdir -p /opt/scripts/aid/logs
  mkdir -p /opt/scripts/aid/plugins
  mkdir -p /opt/scripts/aid/etc
  
  echo "Copying files..."
  cp ./install-files/aid-agent.py /opt/scripts/aid/
  chmod 744 /opt/scripts/aid/aid-agent.py
  cp ./install-files/etc/aid.conf /opt/scripts/aid/etc/
  chmod 644 /opt/scripts/aid/etc/aid.conf
  cp ./install-files/etc/sysinfo.conf /opt/scripts/aid/etc/
  chmod 644 /opt/scripts/aid/etc/sysinfo.conf
  cp ./install-files/etc/logging.conf /opt/scripts/aid/etc
  chmod 644 /opt/scripts/aid/etc/logging.conf
  
  # Copy the entire plugins folder
  plugin_dir=./install-files/plugins
  for entry in "$plugin_dir"/*
  do
     cp $entry /opt/scripts/aid/plugins/
  done
  chmod 744 /opt/scripts/aid/plugins/*
  echo "Complete!"
  
  echo "Creating init script..."
  if [ -d "/etc/init.d/" ]; then
     cp ./install-files/startup/aid-init-script.sh /etc/init.d/aid
     chmod 755 /etc/init.d/aid
  fi
  if [ -d "/etc/systemd/system" ]; then
     cp ./install-files/startup/aid.service /etc/systemd/system/aid.service
     chmod 644 /etc/systemd/system/aid.service
  fi
  echo "Complete!"
  
  echo "Creating aid user..."
  useradd -s /bin/false -M aid
  chown -R aid. /opt/scripts/aid/
  usermod -d /opt/scripts/ aid
  
  echo "AID installed to /opt/scripts/aid/"
  
  # Find which init system is running
  init=`stat /proc/1/exe | head -n1 | awk '{print $4}' | awk -F"/" '{print $3}' | awk -F"’" '{print $1}'`
  
  if [ "$init" == "systemd" ]; then
     echo "Run 'systemctl start aid' to start the daemon."
  elif [ "$init" == "init" ]; then
     echo "Run 'service aid start' to start the daemon"
  else
     echo "Could not determine init system."
  fi
else
  echo "Exiting."
fi

