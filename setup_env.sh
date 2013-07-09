#! /bin/sh

#cd root dir of raspi
cd /home/pi/raspi
cd piConfig
chmod +x startup.sh startup_verbose.sh

cd ../makerbot/conveyor
rm -rf virtualenv
python virtualenv.py virtualenv #sets up virtualenv folder
sudo ./setup.sh  #installs a bunch of dependencies
. virtualenv/bin/activate #activates virtualenv --both server and client need to be run in virtualenv

#test virtualenv by starting background service
python conveyor_service.py -c conveyor-raspi.conf

echo 'conveyord.log output!!'
cat conveyord.log

#cd submodule/conveyor_bins/python
#sudo easy_install pyserial-2.7_mb2.1-py2.7.egg

cd ../s3g
python virtualenv.py virtualenv
sudo ./setup.sh  # should install virtual env for s3g folder


