#! /bin/bash

# filename_local = '/home/pi/Desktop/printer_pic.jpg'
# fswebcam -r 940x720 -S 8 -d /dev/video0 --jpeg 95 --save $filename_local
# curl -F "file=@$filename_local;filename=$0.jpg" 

echo printerId passed = $1,
echo pic_count = $2
#fswebcam -r 960x544 -S 8 -d /dev/video0 --jpeg 95 --save /home/pi/Desktop/$1.jpg
fswebcam -r 640x480 -S 8 -d /dev/video0 --jpeg 95 --save /home/pi/Desktop/$1.jpg

#matter server
#curl -F "file=@/home/pi/Desktop/$1.jpg;filename=$1_$2.jpg" -m 15 http://matter.io/webcamUpload

#dev server
#echo "starting http post"
#curl -F "file=@/home/pi/Desktop/$1.jpg;filename=$1_$2.jpg" -m 15 http://ec2-107-22-186-175.compute-1.amazonaws.com/webcamUpload
#echo "post finished"

#curl reference
#http://curl.haxx.se/docs/manpage.html#-F
#-F "file=@/filename/;filename="
#--data ensures the info is uploaded as post
#type=image/jpg
#--request POST
