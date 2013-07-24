#! /bin/bash

# filename_local = '/home/pi/Desktop/printer_pic.jpg'
# curl -F "file=@$filename_local;filename=$0.jpg" 

echo server_address = $1
echo logPath = $2
echo name passed = $3,
output=",%{url_effective},%{size_upload},%{speed_upload},%{time_total},%{time_connect}"
curl -F "file=@$2;filename=$3.log" -m 15 -s -w $output $1

if [ "$4" = "rm" ]
then
	> /home/pi/raspi/pinger/pinger.log
#	sudo rm /home/pi/raspi/pinger/pinger.log
fi

#curl reference
#http://curl.haxx.se/docs/manpage.html#-F
#-F "file=@/filename/;filename="
#--data ensures the info is uploaded as post
#type=image/jpg
#--request POST
