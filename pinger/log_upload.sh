#! /bin/bash

# filename_local = '/home/pi/Desktop/printer_pic.jpg'
# curl -F "file=@$filename_local;filename=$0.jpg" 

echo server_address = $1
echo job_id passed = $2,
curl -F "file=@/dev/shm/log.log;filename=$2.log" -m 15 $1
sudo rm /dev/shm/log.log

#curl reference
#http://curl.haxx.se/docs/manpage.html#-F
#-F "file=@/filename/;filename="
#--data ensures the info is uploaded as post
#type=image/jpg
#--request POST
