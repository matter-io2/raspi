#! /bin/bash

#comment for testing auto-update

#svn update
#sudo mount / -o remount,rw
#cd /home/pi/raspi
#svn update
#sudo mount / -o remount,ro

#get current branch name
current=$(git rev-parse --abbrev-ref HEAD)
echo 'current branch is '$current

#do a fetch
echo "trying to fetch"
sudo -u pi git fetch
echo "fetch finished"

#if there is new info on "current branch", then pull it
 reslog_working=$(git log HEAD..origin/$current --oneline)
if [ "${reslog_working}" != "" ] ; then
 	new_update=true
 	echo 'updating '$current
 	# git checkout $current
 	git merge origin/$current #completing the pull
 	echo 'new update merged on '$current', restart pinger now'>/home/pi/raspi/piConfig/update.log
 	sudo killall python
	echo 'sleeping between kill and restart'
	sleep 5
	sudo /home/pi/raspi/piConfig/startup_verbose.sh
else
	echo $current' already up-to-date'
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

