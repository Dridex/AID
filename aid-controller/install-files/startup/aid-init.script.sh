#!/bin/bash
### BEGIN INIT INFO
# Provides: aid-controller
# Required-Start: $local_fs
# Required-Stop: $local_fs
# Short-Description: Start and Stop aid-controller monitoring service
# Description: AID is the Advanced Issue Detection monitoring service
# Default-Start: start
# Default-Stop: stop
### END INIT INFO

PATH=/bin:/usr/bin:/sbin:/usr/sbin

DESC="AID controller startup script"
NAME=aid-controller
DAEMON=aid-controllerd

do_start()
{
   su -s /bin/bash -c '/usr/bin/python /opt/scripts/aid-controller/aid-controller.py >/dev/null 2>/dev/null &' aid
   sleep 2
   startpid=`pgrep -f aid-controller.py`
   if [ -z "$startpid" ]
   then
      echo "aid-controller failed to start. Try starting manually with python to get exception."
      exit
   else
      echo "aid-controller started with pid $startpid"
      exit
   fi
}

do_stop()
{
   echo "aid-controller has stopped"
   pid=`pgrep -f aid-controller.py`
   kill $pid
}

do_status()
{
   aidpid=`pgrep -f aid-controller.py`
   if [ -z "$aidpid" ]
   then
        echo "aid-controller is not currently running"
        exit
   else
        echo "aid-controller running with pid $aidpid"
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
