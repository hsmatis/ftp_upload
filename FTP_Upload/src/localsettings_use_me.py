################################################################################
#
# Copyright (C) 2013 Neighborhood Guard, Inc.  All rights reserved.
# Original author: Jesper Jercenoks
# 
# This file is part of FTP_Upload.
# 
# FTP_Upload is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# FTP_Upload is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with FTP_Upload.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

##################################################################################
#                                                                                #
#   "base_location" is the folder where images are stored (end with a slash)     #
#   "incoming_location" is the location of the uploaded images from the camera   #
#   "processed_location" is where uploaded images are stored                     #
#   "ftp_server" is the name of the ftp_server                                   #
#   "ftp_username" is the username to the ftp server                             #
#   "ftp_password" is the password to the ftp server                             #
#   "ftp_destination" is the directory on the ftp server for the images          #
#   ftp_destination must exist (safety check)                                    #
#                                                                                #
##################################################################################


ftp_server = "ftp.charingcrosssherwick.org"

ftp_username = "charingsherwick"  #Regular Account
#ftp_username = "pitester"       #Testing account

ftp_password = "CameraOnStreet"
ftp_destination = "/video.charingcrosssherwick.org" # remember to start with /

base_location = "/home/pi/camera/"                    #Pi configuration
base_location = "/Users/family/cameratest/sftp/"      #Howard's Computer

incoming_location = base_location + "new"
processed_location = base_location + "uploaded" # Make sure this directory is NOT below the incomming_location as you will be creating an endlees upload loop
	
sftp_server = "charingcrosssherwick.org"
sftp_username = "charingsherwicksftp"
sftp_password = "CameraOnStreet"
sftp_destination = "/home/charingsherwicksftp/video" # remember to start with / - This folder must exist

sleep_err_seconds = 180 #Time to sleep when error (Default = 600)
sleep_upload =  30	    #Time to sleep for new pictures (Default = 60)   (Useful to change during testing)
delete=True             # Change to True for Purge to work
		
retain_days = 6 # number of days to retain local images. (not on the FTP server)

#These parameters are needed so that Dreamhost does not get more than 9 FTP processes at once
max_threads = 2 # max number of total threads when needed one thread will be used for purging job, rest of time all threads will be used for upload.
reserved_priority_threads = 1 # previousdays can only upload multithreaded when running today threads fall below this number.

# Frequency that the log time is written to server - This should be different for each server
# So server does not have all logs written at the same time

#destination = "6824Sherwick"       #These are the addresses of the various cameras
destination = "6824aSherwick"
#destination = "6900Sherwick"
#destination = "6975Charing"
#destination = "6808Charing"

log_destination = "/logfiles/" + destination + "/"     # remember to start with / - This folder must existbase_location = "/Users/matis/cameratest/sftp/"

save_today_log_interval = 60   #minutes

if destination == "6900Sherwick":
    save_yesterday_log_time = "01:00"
elif destination == "6975Charing":
    save_yesterday_log_time = "01:15"
elif destination == "6808Charing":
    save_yesterday_log_time = "01:30"
elif destination == "6824Sherwick":
    save_yesterday_log_time = "02:00"   #24 hour time running
elif destination == "6824aSherwick":
    save_yesterday_log_time = "02:15"   #24 hour time running
else:
    save_yesterday_log_time= "22:22"



