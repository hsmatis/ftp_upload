################################################################################
#
# Copyright (C) 2013-4 Neighborhood Guard, Inc.  All rights reserved.
# Original author: Jesper Jercenoks
# Some Tweaks by: Howard Matis - March 21, 2014 Added uploading of log files
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

######################################################################################
#                                                                                    #
# Program to upload images as part of the Neighborhood Guard software suite.         #
# Program only uploads files and directories whose pathnames conform to the          #
# date/time format.                                                                  #
#                                                                                    #
######################################################################################

# Version 1.5.4 - add saving of cron file at end of log

#import os.path
import os
import shutil
import datetime
from datetime import timedelta
import re
import time
import ftplib
import threading
import logging.handlers
import sys
import traceback
import signal
import schedule   #need to get this from gethub

from localsettings import *
from runtimesettings import *

version_string = "1.5.4.8"

current_priority_threads=0 # global variable shared between threads keeping track of running priority threads.

def mkdir(dirname):
    try:
        os.mkdir(dirname)
    except:
        pass


def rmdir(dirname):
    try:
        os.rmdir(dirname)
    except:
        pass


def change_create_ftp_dir(ftp_connection, dirname):
    # dirname is relative or absolute
    
    if ftp_connection != None:
        try:
            ftp_connection.cwd(dirname)
        except ftplib.error_perm :
            try:
                ftp_connection.mkd(dirname)
                ftp_connection.cwd(dirname)
            except Exception, e:
                logging.warning("can't make ftp directory %s" % dirname)
                logging.exception(e)
    
    return

def dir2date(indir):
    #extract date from indir style z:\\ftp\\12-01-2
    searchresult = re.search(r".*/([0-9]{4})-([0-9]{2})-([0-9]{2})", indir)
    if searchresult == None:     #extract date from indir style 12-01-2
        searchresult = re.search(r".*([0-9]{4})-([0-9]{2})-([0-9]{2})", indir)
    
    if searchresult != None:
        year= int(searchresult.group(1))
        month = int(searchresult.group(2))
        day = int(searchresult.group(3))
    else:
        year = None
        month = None
        day = None
    
    return (year, month, day)


def get_daydirs(location):
    daydirlist = os.listdir(location)
    
    daydirs=[]
    for direc in daydirlist:
        (year, unused_month, unused_day) = dir2date(direc)
        dirpath = os.path.join(location, direc)
        if os.path.isdir(dirpath) and year != None:
            daydirs.append((dirpath,direc))
    daydirs = sorted(daydirs)
    
    return daydirs


def connect_to_ftp():
    ftp_connection = None
    try:
        ftp_connection = ftplib.FTP(ftp_server,ftp_username,ftp_password,timeout=30)
        logging.debug(ftp_connection.getwelcome())
        logging.debug("current directory is: %s", ftp_connection.pwd())
        logging.debug("changing directory to: %s", ftp_destination)
        ftp_connection.cwd(ftp_destination)
        logging.debug("current directory is: %s", ftp_connection.pwd())
    except ftplib.error_perm, e:
        logging.error("Failed to open FTP connection, %s", e)
        ftp_connection = None
        message = "Sleeping " + str(sleep_err_seconds/60) + " minutes before trying again"
        logging.info(message)
        time.sleep(sleep_err_seconds)
    except Exception, e:
        logging.error("Unexpected exception in connect_to_ftp():")
        logging.exception(e)
        if ftp_connection != None:
            ftp_connection.close()  # close any connection to cloud server
        ftp_connection = None
    
    return ftp_connection

def quit_ftp(ftp_connection):
    if ftp_connection != None :
        try:
            ftp_connection.quit()
            logging.debug("ftp connection successfully closed")
        except Exception, e:
            #logging.warning("Exception during FTP.quit():", e)
            logging.warning("Exception during FTP.quit():")
            logging.exception(e)

def storefile(ftp_dir, filepath, donepath, filename, today):
    global current_priority_threads
    if today:
        current_priority_threads += 1
        logging.info("current Priority threads %s", current_priority_threads)
    
    ftp_connection = connect_to_ftp()
    if ftp_connection != None:
        change_create_ftp_dir(ftp_connection, ftp_dir)
        logging.info("Uploading %s", filepath)
        try:
            filehandle = open(filepath, "rb")
            ftp_connection.storbinary("STOR " + filename, filehandle)
            filehandle.close()
            logging.info("file : %s stored on ftp", filename)
            logging.info("moving file to Storage")
            
            try :
                # if the directory we want to move the file into doesn't exist,
                # create it.  This is a hack.  It's intended to recover from the
                # case where the purge process has deleted an old storage day-
                # directory, but for whatever reason, there are still files in
                # the incoming area for that day that need to be FTP'd to the
                # server
                #
                donedir = os.path.dirname(donepath)
                if not os.path.exists(donedir):
                    os.makedirs(donedir)
                
                shutil.move(filepath, donepath)
            except Exception, e:
                logging.warning("can't move file %s, possible sharing violation", filepath )
                logging.exception(e)
        
        except Exception, e:
            logging.error("Failed to store ftp file: %s: %s", filepath, e)
            logging.exception(e)
            filehandle.close()
            message = "Sleeping " + str(sleep_err_seconds/60) + " minutes before trying again"
            logging.info(message)
            time.sleep(sleep_err_seconds)
        
        quit_ftp(ftp_connection)
    
    else :
        message = "Sleeping " + str(sleep_err_seconds/60) + " minutes before trying again - general error"
        logging.info(message)
        time.sleep(sleep_err_seconds)
    # end if
    
    if today :
        current_priority_threads -= 1
    
    return

def storelogfile(ftp_dir, filepath, filename, today):             #For storing log files
    global current_priority_threads
    if today:
        current_priority_threads += 1
        logging.info("current Priority threads %s", current_priority_threads)
    
    logging.info("In routine storelogfile")
    logging.info("ftp_dir = %s", ftp_dir)
    logging.info("filepath = %s", filepath)
    logging.info("filename = %s", filename)
    
    ftp_connection = connect_to_ftp()
    count = 0
    not_upload = True
    while not_upload and count < 5:           #Loop to upload files
        count += 1
        if ftp_connection != None:
            ftp_connection = ftplib.FTP(ftp_server,ftp_username,ftp_password,timeout=30) #not sure if this is needed
            change_create_ftp_dir(ftp_connection, ftp_dir)
            logging.info("Uploading %s", filepath)
            try:
                filehandle = open(filepath, "rb")
                ftp_connection.storbinary("STOR " + filename, filehandle)
                filehandle.close()
                logging.info("file : %s stored on ftp", filename)
                logging.info("moving file to Storage")
                not_upload = False

            except Exception, e:
                logging.error("Failed to store logfile file: %s: %s", filepath, e)
                logging.exception(e)
                filehandle.close()
                message = "Sleeping " + str(sleep_err_seconds/60) + " minutes before storing logfile"
                logging.info(message)
                message = "ftp upload error"
                logging.info(message)
                time.sleep(sleep_err_seconds)
        
            quit_ftp(ftp_connection)
    
        else :
            message = "Sleeping " + str(sleep_err_seconds/60) + " minutes before uploading logfile"
            logging.info(message)
            message = "ftp connection error"
            logging.info(message)
            time.sleep(sleep_err_seconds)
        # end if
    
    if today :
        current_priority_threads -= 1
    
    return


def storedir(dirpath, ftp_dir, done_dir, today):
    global current_priority_threads
    global reserved_priority_threads
    
    logging.info("starting storedir")
    logging.info("dirpath = %s", dirpath)
    logging.info("ftp_dir = %s", ftp_dir)
    logging.info("done_dir = %s", done_dir)
    
    ftp_connection = connect_to_ftp()
    change_create_ftp_dir(ftp_connection, ftp_dir)
    quit_ftp(ftp_connection)
    
    mkdir(done_dir)

    files = sorted(os.listdir(dirpath))
    for filename in files:
        filepath = os.path.join(dirpath, filename)
        donepath = os.path.join(done_dir, filename)
        if os.path.isfile(filepath):
            
            current_threads = threading.active_count()
            logging.info("current threads: %s", current_threads)
            
            if (current_threads >= max_threads) or (not today and current_priority_threads>=reserved_priority_threads):
                # to many threads running already, upload ftp in current thread (don't move forward until upload is done)
                storefile(ftp_dir, filepath, donepath, filename, today)
                current_threads = threading.active_count()
                logging.info("current threads: %s", current_threads)
            else:
                
                # start new thread
                logging.info("starting new storefile thread")
                threading.Thread(target=storefile, args=(ftp_dir, filepath, donepath, filename, today)).start()
                current_threads = threading.active_count()
                logging.info("current threads: %s", current_threads)
        #end if
        
        elif os.path.isdir(filepath):
            logging.info("Handling subdirectory %s", filepath)
            new_ftp_dir = ftp_dir + "/" + filename
            storedir(filepath, new_ftp_dir, donepath, today)
    # end if
    # end for
    
    rmdir(dirpath)
    return

def addSecs(tm, secs):              #routine to add seconds to the current time
    fulldate = datetime.datetime(100, 1, 1, tm.hour, tm.minute, tm.second)
    fulldate = fulldate + datetime.timedelta(seconds=secs)
    return fulldate.time()


def deltree(deldir):
    logging.info("deltree: %s", (deldir))
    files_to_be_deleted = sorted(os.listdir(deldir))
    for file2del in files_to_be_deleted:
        filepath = os.path.join(deldir, file2del)
        if os.path.isdir(filepath):
            deltree(filepath)
            rmdir(filepath)
        else:
            logging.info("deleting %s", filepath)
            if delete == False :
                logging.info("would have deleted %s here - to really delete change delete flag to True", filepath)
            else :
                os.remove(filepath)
    rmdir(deldir)
    return

files_purged = False    # only used by testing code

def purge_old_images(purge_dir):
    global files_purged
    # Purge directories in Purge_dir, does not delete purge_dir itself
    purge_daydirs=get_daydirs(purge_dir)
    logging.debug("list of directories to be purged: %s", purge_daydirs[0:-retain_days])
    files_purged = False
    for purge_daydir in purge_daydirs[0:-retain_days]:
        (dirpath, unused_direc) = purge_daydir
        logging.info("purging directory %s", dirpath)
        deltree(dirpath)
        files_purged = True
    return

def isdir_today(indir):
    (processingyear,processingmonth, processingday) = dir2date(indir)
    current = datetime.date.today()
    return (processingyear==current.year and processingmonth == current.month and processingday==current.day)

def storeday(daydir, today=False):
    try:
        (dirpath, direc) = daydir
        logging.info("processing directory %s", direc)
        ftp_dir = ftp_destination + "/" + direc
        done_dir = os.path.join(processed_location, direc)
        storedir(dirpath, ftp_dir, done_dir, today)
    except Exception, e:
        logging.exception(e)
    
    return

def storedays(daydirs):
    logging.info("Starting storedays()")
    try:
        for daydir in daydirs:
            storeday(daydir)
    except Exception, e:
        logging.error("Unexpected exception in storedays()")
        logging.exception(e)
    logging.info("Returning from storedays()")
    return

def dumpstacks():
    '''For debugging purposes, dump a stack trace for each running thread
        to the log'''
    id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(threadId,""), threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    logging.info("User requested stack dumps"+("\n".join(code)))

def sighandler(signum, frame):
    dumpstacks()

def set_up_logging():
    if set_up_logging.not_done:
        # get the root logger and set its level to DEBUG
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # set up the rotating log file handler
        #
        logfile = logging.handlers.TimedRotatingFileHandler(ftp_upload_log, when= rotate, backupCount=logfile_max_days)
        logfile.setLevel(logfile_log_level)
        logfile.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(threadName)-10s %(message)s','%m-%d %H:%M:%S'))
        logger.addHandler(logfile)
                                                                                       
        # define a Handler which writes messages equal to or greater than
        # console_log_level to the sys.stderr
        console = logging.StreamHandler()
        console.setLevel(console_log_level)
        # set a format which is simpler for console use
        formatter = logging.Formatter('%(levelname)-8s %(message)s')
        # tell the handler to use this format
        console.setFormatter(formatter)
        # add the handler to the root logger
        logging.getLogger('').addHandler(console)
        set_up_logging.not_done = False

set_up_logging.not_done = True  # logging should only be set up once, but
# set_up_logging() may be called multiple times when testing

def save_yesterday_log_file():                #This is called when the scheduler decides it is time to save yesterday's log file
    todaydate = datetime.date.today()
    yesterday = todaydate - timedelta(1)
    yesterday_log = ftp_upload_log +"." + yesterday.strftime("%Y-%m-%d")    #File name of log file to be saved
    message = "About to save " + yesterday_log
    logging.info(message)
    dirpath = ""
    filepath = os.path.join(dirpath, yesterday_log)

    filename = "ftp_upload-" + yesterday.strftime("%Y-%m-%d") + ".log"      #File name written on server
    logging.info("Files waiting to be upload.")
    if os.path.isfile(yesterday_log):       #Check to see if the log file was written yesterday
        write_out_log_file(filepath,filename)
    else:
        logging.info("Yesterday's log file has not been saved in full: %s", yesterday_log)
    #end if
    command = "ls -R " + incoming_location + " >> " + ftp_upload_log      #list the number of files not yet transferred
    os.system(command)
    #

def save_today_log_file():              #This is called regularly when the scheduler decides it is time to save today's log file
    todaydate = datetime.date.today()
    todaydate_log = ftp_upload_log    #File name of log file to be saved
    message = "About to save " + todaydate_log
    logging.info(message)

    message = "Looking for chron log " + ftp_reload_log
    logging.info(message)

    dirpath = ""
    reload_log = os.path.join(dirpath, ftp_reload_log)

    message = "Looking for the full path of chron log " + reload_log
    logging.info(message)

    if os.path.isfile(reload_log):
        message = "Saving " + reload_log
        logging.info(message)
        with open(reload_log) as f:
            for line in f:
                logging.info(line[:-1] )            #getting rid of extra new line
        os.remove(reload_log)        #remove the chron log file
    else:
        message = "Could not find " + ftp_reload_log
        logging.info(message)

    filepath = os.path.join(dirpath, todaydate_log)
    filename = "ftp_upload-" + todaydate.strftime("%Y-%m-%d") + ".log"      #File name written on server

    write_out_log_file(filepath,filename)


def write_out_log_file(filepath,filename):
    ftp_dir = log_destination
    logging.info("ftp_dir = %s", ftp_dir)
    logging.info("filepath = %s", filepath)
    logging.info("filename = %s", filename)
    current_threads = threading.active_count()
    logging.info("current threads: %s", current_threads)
    today = True        #not sure about this value
    if (current_threads >= max_threads) or (not today and current_priority_threads>=reserved_priority_threads):
        # too many threads running already, upload ftp in current thread (don't move forward until upload is done)
        storelogfile(ftp_dir, filepath, filename, today)
        current_threads = threading.active_count()
        logging.info("current threads: %s", current_threads)
    else:
        # start new thread
        logging.info("starting new storelogfile thread")
        threading.Thread(target=storelogfile, args=(ftp_dir, filepath, filename, today)).start()
        current_threads = threading.active_count()
        logging.info("current threads: %s", current_threads)
        #end if

def main():
    global uploads_to_do    # for testing only
    set_up_logging()
    signal.signal(signal.SIGINT, sighandler)    # dump thread stacks on Ctl-C
    logging.info("Program ftp_upload.py started: Version %s", version_string)
    
    schedule.every(save_today_log_interval).minutes.do(save_today_log_file)  # save today's log_file
    schedule.every().day.at(save_yesterday_log_time).do(save_yesterday_log_file)      #save the log file once a day
    message = "Saving yesterday's log file every day at " + save_yesterday_log_time
    logging.info(message)
    message = "Saving today's log file every " + str(save_today_log_interval) + " minutes"
    logging.info(message)
    message = "Saving log files to directory " + log_destination
    logging.info(message)

    save_today_log_file() #temp

    command = "ls -R " + incoming_location + " >> " + ftp_upload_log      #list the number of files not yet transferred
    logging.info("Beginning of the list of images not uploaded to the server")
    os.system(command)
    logging.info("End of list of Images not uploaded to the server")

    try:
        mkdir(processed_location)
        # Setup the threads, don't actually run them yet used to test if the threads are alive.
        processtoday_thread = threading.Thread(target=storeday, args=())
        process_previous_days_thread = threading.Thread(target=storedays, args=())
        
        purge_thread = threading.Thread(target=purge_old_images, args=())
        
        
        while True:
            
            daydirs = get_daydirs(incoming_location)
            
            #reverse sort the days so that today is first
            daydirs = sorted(daydirs, reverse=True)
            
            # Today runs in 1 thread, all previous days are handled in 1 thread starting with yesterday and working backwards.
            
            previous = 0    # starting index of possible previous days' uploads
            uploads_to_do = False
            if len(daydirs) > 0:
                uploads_to_do = True
                if isdir_today(daydirs[0][0]):
                    if not processtoday_thread.is_alive():
                        processtoday_thread = threading.Thread(target=storeday, args=(daydirs[0],True))
                        processtoday_thread.start()
                    previous = 1
            
            if len(daydirs) > previous:
                uploads_to_do = True
                # Only if previous days is not running, run it to check that everything is processed.
                if not process_previous_days_thread.is_alive():
                    process_previous_days_thread = threading.Thread(target=storedays, 
                                                                    args=(daydirs[previous:],))
                    process_previous_days_thread.start()
            
            
            if not purge_thread.is_alive():
                purge_thread = threading.Thread(target=purge_old_images, args=(processed_location,))
                purge_thread.start()
            
            schedule.run_pending()          #See if it is time to save log file
            message = "Sleeping " + str(sleep_upload) + " seconds for upload"
            logging.info(message)
            logging.info("Time is %s", time.ctime() )          
            try:
                time.sleep(sleep_upload) # sleep
            
            # hitting Ctl-C to dump the thread stacks will interrupt
            # MainThread's sleep and raise IOError, so catch it here
            except IOError, e:
                logging.warn("Main loop sleep interrupted")
            
            if terminate_main_loop:     # for testing purposes only
                break
    except Exception, e:
        logging.error("Unexpected exception in main()")
        logging.exception(e)
        raise   # rethrow so unit test code will know something went wrong

if __name__ == "__main__":
    main()
