#!/bin/bash

# killall python
echo attempting reconnect on $1
while true ; do
   if ifconfig $1 | grep -q "inet addr:" ; then
     # sudo /home/pi/raspi/piConfig/startup_verbose.sh &
     echo "killing bash script"
     exit
     echo "this shouldn't print - if printed, bash script didn't exit"
     # sleep 60
   else
      echo "Network connection down! Attempting reconnection."
      ifup --force $1
      sleep 5
   fi

done
