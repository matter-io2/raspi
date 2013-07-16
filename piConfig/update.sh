
#! /bin/sh

#cleanup
#sudo killall python

#svn update
#sudo mount / -o remount,rw
#cd /home/pi/raspi
#svn update
#sudo mount / -o remount,ro

git fetch origin
reslog_working=$(git log HEAD..origin/working_base --oneline)
reslog_master=$(git log HEAD..origin/master --oneline)
if [[ "${reslog_working}" != "" ]] ; then
	sudo killall python
	git checkout working_base
	git merge origin/working_base #completing the pull
	
fi
if [[ "${reslog_master}" != ""]] ; then
	sudo killall python
	git checkout master
	git merge origin/master
fi




#restart conveyor
# cd /home/pi/raspi/makerbot/conveyor/
# rm conveyord.socket conveyord.pid conveyord.avail.lock
# virtualenv/bin/python conveyor_service.py -c conveyor-debian.conf

# #run these from commandline, comment out here when debugging
# cd /home/pi/raspi/pinger/
# nohup python pinger.py &
# #python pinger.py  # this version has output vs. nohup which doesn't

#cd ../../Desktop/GPIO_testing/
#sudo python test.py

