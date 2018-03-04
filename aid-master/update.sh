#!/bin/bash

if [ "$EUID" -ne 0 ]
then 
	echo "Please run as root"
	exit
fi

echo "Checking version of python..."
pv=`python -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' | grep 2.7`
if [ -z $pv ]; then
   echo "Python 2.7 not installed or not default... please install python2.7"
   exit
else
   echo "Python 2.7 installed and default. Continuing."
fi

echo "Setting up directories..."
mkdir -p /opt/scripts/aid-master/logs
mkdir -p /opt/scripts/aid-master/etc
echo "Done."

echo "Copying files..."
cp -i ./install-files/aid-master.py /opt/scripts/aid-master/
chmod 744 /opt/scripts/aid-master/aid-master.py
cp -i ./install-files/etc/controllers.conf /opt/scripts/aid-master/etc/
chmod 644 /opt/scripts/aid-master/etc/controllers.conf
cp -i ./install-files/etc/proxy.conf /opt/scripts/aid-master/etc/
chmod 644 /opt/scripts/aid-master/etc/proxy.conf
cp -i ./install-files/etc/logging.conf /opt/scripts/aid-master/etc/
chmod 644 /opt/scripts/aid-master/etc/logging.conf
cp -i ./install-files/helperMaster.py /opt/scripts/aid-master/
chmod 644 /opt/scripts/aid-master/helperMaster.py
echo "Done."

echo "Creating init script..."
if [ -d "/etc/init.d/" ]; then
   cp -i ./install-files/startup/aid-init-script.sh /etc/init.d/aid-master
   chmod 755 /etc/init.d/aid-master
fi
if [ -d "/etc/systemd/system" ]; then
   cp -i ./install-files/startup/aid-master.service /etc/systemd/system/aid-master.service
   chmod 644 /etc/systemd/system/aid-master.service
fi
echo "Done."

echo "Creating aid user..."
useradd -s /bin/false -M aid
chown -R aid. /opt/scripts/aid-master/
usermod -d /opt/scripts/ aid

echo "AID installed to /opt/scripts/aid-master/"

# Find which init system is running
init=`stat /proc/1/exe | head -n1 | awk '{print $4}' | awk -F"/" '{print $3}' | awk -F"’" '{print $1}'`

if [ "$init" == "systemd" ]; then
   echo "Run 'systemctl start aid-master' to start the daemon."
elif [ "$init" == "init" ]; then
   echo "Run 'service aid-master start' to start the daemon"
else
   echo "Could not determine init system."
fi
