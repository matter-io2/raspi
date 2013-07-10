#! /bin/sh

# filename_local = '/home/pi/Desktop/printer_pic.jpg'
# fswebcam -r 940x720 -S 8 -d /dev/video0 --jpeg 95 --save $filename_local
# curl -F "file=@$filename_local;filename=$0.jpg" 

fswebcam -r 940x720 -S 8 -d /dev/video0 --jpeg 95 --save /home/pi/Desktop/printer_pic.jpg
#curl -F "file=@/home/pi/Desktop/printer_pic.jpg;filename=$0.jpg" http://matter.io/webcamUpload
curl -F "file=@/home/pi/Desktop/printer_pic.jpg;filename=zztest.jpg" http://matter.io/webcamUpload




#curl reference
#http://curl.haxx.se/docs/manpage.html#-F
#-F "file=@/filename/;filename="
#--data ensures the info is uploaded as post
#type=image/jpg
#--request POST
