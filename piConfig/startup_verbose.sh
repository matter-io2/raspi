
#! /bin/sh

cd /home/pi


killall python
cd /home/pi/raspi/makerbot/conveyor/
rm conveyord.socket conveyord.pid conveyord.avail.lock
virtualenv/bin/python conveyor_service.py -c conveyor-debian.conf

#run these from commandline, comment out here when debugging
cd /home/pi/raspi/pinger/
#nohup python pinger.py &
python pinger.py  # this version has output vs. nohup which doesn't

#cd ../../Desktop/GPIO_testing/
#sudo python test.py

