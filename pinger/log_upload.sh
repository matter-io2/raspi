#! /bin/bash

#DEBUG input
#echo server_address = $1
#echo logPath = $2
#echo job_id passed = $3,

#defines return format
output=",%{url_effective},%{size_upload},%{speed_upload},%{time_total},%{time_connect}"

#upload call
curl -F "file=@$2;filename=$3.log" -m 15 -s -w $output $1
#sudo rm /home/pi/raspi/pinger/pinger.log


#curl reference
#http://curl.haxx.se/docs/manpage.html#-F
#-F "file=@/filename/;filename="
#--data ensures the info is uploaded as post
#type=image/jpg
#--request POST
