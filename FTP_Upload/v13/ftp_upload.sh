#!/bin/bash
#
# run the ftp protocol to transfer Axis camera images from a local server
# to the cloud
# This script is run by "./Users/camera/ftp/FTP_Upload/ftp_upload.sh" on a Mac
# and ./etc/profile on Linux  (profile has to be edited.)
# and ./etc/rc.local on Raspberry PI  (this needs to be edited to say something like
#       sudo -u pi  bash /home/pi/camera/ftp_upload/ftp_upload.sh &
#
#
export FTP_SCRIPT=/home/pi/camera/ftp_upload
export FTP_LOG=/home/pi
cd $FTP_LOG
python $FTP_SCRIPT/ftp_upload.py >& /dev/null &
#
