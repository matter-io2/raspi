
#! /bin/sh

cd /home/pi


sudo killall -9 python
sudo rm /dev/shm/*.jpg #webcam cache location cleared

cd /home/pi/raspi/makerbot/conveyor/
rm conveyord.socket conveyord.pid conveyord.avail.lock conveyord.log
virtualenv/bin/python conveyor_service.py -c conveyor-raspi.conf
echo -e '\n ---------conveyord.log (tail 20)----------'
tail conveyord.log -n 20

#run these from commandline, comment out here when debugging
#cd /home/pi/raspi/pinger/
#nohup python pinger.py & # doesn't work with read only
#nohup python pinger.py >/dev/null 2>&1   # doesn't create nohup.out
#python pinger.py  # this version has output vs. nohup which doesn't

#cd ../../Desktop/GPIO_testing/
#sudo python test.py

