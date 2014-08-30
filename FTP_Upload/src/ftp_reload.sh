#!/bin/bash
#
#ftp_reload.sh is a script written by Howard Matis - 2014 - Version 1.1
#check if ftp_upload is running
#
# local variables
DIR=/home/pi/camera/ftp_upload		#directory of this program and ftp_upload.sh
LOGDIR=/home/pi                    #Location of log file for Howard's Pi
#LOGDIR=/media/usb0                  #Pi configuration for disk writing Pi's
PROCESSLOG=$LOGDIR/ftp_upload.log	#Name of log file
CRONLOG=$LOGDIR/ftp_reload.log      #Name of cron log file
#
NOW=$(date)
PROCESS=ftp_upload					#Name of process to check if running
MYNAME=FTP_RELOAD                  #Name of this process
#
ps -ef | grep -v grep | grep $PROCESS.py > /dev/null

# if not found - equals to 1, start it
if [ $? -eq 1 ]
then
# Process is not found
echo " " >> $PROCESSLOG
echo "$MYNAME> $NOW – Error $PROCESS not found - Retarted" >> $PROCESSLOG
echo " " >> $PROCESSLOG
sudo -u pi bash $DIR/ftp_upload.sh &
#
else
# Process is found (can't write to ftp_upload because program would overwrite this command)
echo "$MYNAME> $NOW – $PROCESS found - No need to do anything" >> $CRONLOG
fi