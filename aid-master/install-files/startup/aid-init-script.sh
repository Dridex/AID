#!/bin/bash
### BEGIN INIT INFO
# Provides: aid-master
# Required-Start: $local_fs
# Required-Stop: $local_fs
# Short-Description: Start and Stop aid-master monitoring service
# Description: AID is the Advanced Issue Detection monitoring service
# Default-Start: start
# Default-Stop: stop
### END INIT INFO

PATH=/bin:/usr/bin:/sbin:/usr/sbin

DESC="AID master startup script"
NAME=aid-master
DAEMON=aid-masterd

do_start()
{
   su -s /bin/bash -c '/usr/bin/python /opt/scripts/aid-master/aid-master.py >/dev/null 2>/dev/null &' aid
   sleep 2
   startpid=`pgrep -f aid-master.py`
   if [ -z "$startpid" ]
   then
      echo "aid-master failed to start"
      exit
   else
      echo "aid-master started with pid $startpid"
      exit
   fi
}

do_stop()
{
   echo "aid-master has stopped"
   pid=`pgrep -f aid-master.py`
   kill $pid
}

do_status()
{
   aidpid=`pgrep -f aid-master.py`
   if [ -z "$aidpid" ]
   then
        echo "aid-master is not currently running"
        exit
   else
        echo "aid-master running with pid $aidpid"
   fi
}

case "$1" in
   start)
     do_start
     ;;
   stop)
     do_stop
     ;;
   status)
     do_status
     ;;
   restart)
     do_stop
     do_start
     ;;
esac

exit 0
