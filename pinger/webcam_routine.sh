#! /bin/bash

# filename_local = '/home/pi/Desktop/printer_pic.jpg'
# fswebcam -r 940x720 -S 8 -d /dev/video0 --jpeg 95 --save $filename_local
# curl -F "file=@$filename_local;filename=$0.jpg" 

echo server_address = $1
echo printerId passed = $2,
echo pic_count = $3
#fswebcam -r 960x544 -S 8 -d /dev/video0 --jpeg 95 --save /home/pi/Des
echo 'clearing /dev/shm'
sudo rm /dev/shm/* # clear ram to prevent taking too much space
echo 'ram cleared'
#fswebcam -r 640x480 -S 8 -d /dev/video0 --jpeg 95 --save /dev/shm/$2.jpg
fswebcam -c fswebcam.conf --save /dev/shm/$2.jpg  #loads options that are in /raspi/pinger folder

#matter server
#curl -F "file=@/dev/shm/$2.jpg;filename=$2_$3.jpg" -m 15 http://matter.io/webcamUpload

#dev server
echo "starting http post"
curl -F "file=@/dev/shm/$2.jpg;filename=$2_$3.jpg" -m 15 http://ec2-107-22-186-175.compute-1.amazonaws.com/webcamUpload
echo "post finished"

#curl reference
#http://curl.haxx.se/docs/manpage.html#-F
#-F "file=@/filename/;filename="
#--data ensures the info is uploaded as post
#type=image/jpg
#--request POST
