#! /bin/bash

# filename_local = '/home/pi/Desktop/printer_pic.jpg'
# curl -F "file=@$filename_local;filename=$0.jpg" 

echo server_address = $1
echo logPath = $2
echo job_id passed = $3,
curl -F "file=@$2;filename=$3.log" -m 15 $1
#sudo rm /home/pi/raspi/pinger/pinger.log

#curl reference
#http://curl.haxx.se/docs/manpage.html#-F
#-F "file=@/filename/;filename="
#--data ensures the info is uploaded as post
#type=image/jpg
#--request POST
