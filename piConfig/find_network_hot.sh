#!/bin/bash

# killall python
while true ; do
   if ifconfig wlan0 | grep -q "inet addr:" ; then
     # sudo /home/pi/raspi/piConfig/startup_verbose.sh &
     echo "killing bash script"
     exit
     echo "this shouldn't print - if printed, bash script didn't exit"
     # sleep 60
   else
      echo "Network connection down! Attempting reconnection."
      ifup --force wlan0
      sleep 5
   fi

done
