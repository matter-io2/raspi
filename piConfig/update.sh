
#! /bin/sh

#cleanup
#sudo killall python

#svn update
#sudo mount / -o remount,rw
#cd /home/pi/raspi
#svn update
#sudo mount / -o remount,ro

echo "trying to fetch"
sudo -u pi git fetch origin
echo "fetch finished"
reslog_working=$(git log HEAD..origin/working_base --oneline)
reslog_master=$(git log HEAD..origin/master --oneline)
if [ "${reslog_working}" != "" ] ; then
	echo 'updating working_base branch'
	sudo killall python
	git checkout working_base
	git merge origin/working_base #completing the pull
else
	echo '"working_base" branch already up-to-date'
fi
if [ "${reslog_master}" != "" ] ; then
	echo 'updating master branch'
	sudo killall python
	git checkout master
	git merge origin/master
else
	echo '"master" branch already up-to-date'
fi

#greg's comment #1





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

