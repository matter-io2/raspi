
#! /bin/bash

#comment 1
#comment 2
#cleanup
#sudo killall python

#svn update
#sudo mount / -o remount,rw
#cd /home/pi/raspi
#svn update
#sudo mount / -o remount,ro

echo "trying to pull"
sudo -u pi git pull
echo "pull finished"
#reslog_dev=$(git log HEAD..origin/dev --oneline)
#if [ "${reslog_dev}" != "" ] ; then
#	# new_update=true
#	echo 'updating dev branch'
#	sudo killall python
#	sudo -u pi git checkout dev
#	sudo -u pi git merge origin/dev
#	echo 'new update on dev'>/home/pi/raspi/piConfig/update.log
#else
#	echo '"dev" branch already up-to-date'
#fi
 reslog_working=$(git log HEAD..origin/working_base --oneline)
if [ "${reslog_working}" != "" ] ; then
 	new_update=true
 	echo 'updating working_base branch'

 	git checkout working_base
 	git merge origin/working_base #completing the pull
 	echo 'new update on working_base, restart pinger at next stop'>/home/pi/raspi/piConfig/update.log
 	sudo killall python
	sudo /home/pi/raspi/piConfig/startup_verbose.sh
else
	echo '"working_base" branch already up-to-date'
fi

# if [ $new_update ]; then
	

# fi


#greg's comment #1
#greg's comment #2





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

