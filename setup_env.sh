#! /bin/sh

#cd root dir of raspi
cd /home/pi/raspi
cd piConfig
chmod +x startup.sh startup_verbose.sh

cd ../makerbot/conveyor
./setup.sh

cd ../s3g
./setup.sh
