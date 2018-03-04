#!/bin/bash
### BEGIN INIT INFO
# Provides: aid
# Required-Start: $local_fs
# Required-Stop: $local_fs
# Short-Description: Start and Stop aid monitoring service
# Description: aid is the Advanced Issue Detection monitoring service
# Default-Start: start
# Default-Stop: stop
### END INIT INFO

PATH=/bin:/usr/bin:/sbin:/usr/sbin

DESC="aid startup script"
NAME=aid
DAEMON=aidd

do_start()
{
   su -s /bin/bash -c '/opt/scripts/aid/aid-agent.py >/dev/null 2>/dev/null &' aid
   sleep 2
   startpid=`pgrep -f aid-agent.py`
   if [ -z "$startpid" ]
   then
      echo "aid failed to start"
      exit
   else
      echo "aid started with pid $startpid"
      exit
   fi
}

do_stop()
{
   stoppid=`pgrep -f aid-agent.py`
   
   if [ -z "$stoppid" ]
   then
      echo "aid is not currently cunning."
   else
      kill $stoppid
      echo "aid has stopped"
   fi
}

do_status()
{
   aidpid=`pgrep -f aid-agent.py`
   if [ -z "$aidpid" ]
   then
        echo "aid is not currently running"
        exit
   else
        echo "aid running with pid $aidpid"
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
