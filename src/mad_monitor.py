'''
Created on Nov 22, 2018

@author: pjdrm
'''
from subprocess import Popen, PIPE
from datetime import datetime
import logging
import time
import threading
import os
import subprocess

class MADMonitor():
    
    def __init__(self, log_file,
                       madctl_path,
                       max_walker_secs=480,
                       max_ocr_secs=480):
        self.status_script = madctl_path+'MADstatus_overall.sh' 
        self.reset_all_script = madctl_path+'MADreset_all.sh'
        self.reset_scanner_script = madctl_path+'MADreset_scanner.sh'
        self.login_script = madctl_path+'MADlogin_device.sh'

        self.max_walker_secs = max_walker_secs
        self.max_ocr_secs = max_ocr_secs
        self.heart_beat_hour = -1
        
        self.logger = logging.getLogger('MAD Monitor')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
    def check_mad(self):
        timer = threading.Timer(300, self.check_mad)
        timer.start()
        current_date = datetime.now()
        current_hour = int(current_date.strftime('%H'))
        if current_hour >= 21 or current_hour < 9:
            return #Raid time is over
        elif current_hour > self.heart_beat_hour:
            self.heart_beat_hour = current_hour
            self.logger.info("Heart beat")
        result = subprocess.run([self.status_script], stdout=subprocess.PIPE)
        mad_status = str(result.stdout)
        last_walk_ts = mad_status.split('scanner process last submitted a raid at: ')[1].split('\\n')[0]
        last_ocr_ts = mad_status.split('OCR process last submitted a raid at: ')[1].split('  ')[0]
        
        last_walk_date = datetime.strptime(last_walk_ts, '%Y-%m-%d %H:%M:%S')
        last_ocr_date = datetime.strptime(last_ocr_ts, '%Y-%m-%d %H:%M:%S')
        
        current_date = datetime.now() #status command takes too long to execute better get time again
        last_walker_secs = (current_date-last_walk_date).seconds
        last_ocr_secs = (current_date-last_ocr_date).seconds
        
        if last_walker_secs >= self.max_walker_secs:
            timer.cancel() #we dont want another check_mad while recovering
            self.logger.warning("Walker seems to be down. Scanner process last submitted a raid at: "+last_walk_ts)
            self.recover_mad()
        elif last_ocr_secs >= self.max_ocr_secs:
            timer.cancel() #we dont want another check_mad while recovering
            self.logger.warning("OCR seems to be down. OCR process last submitted a raid at: "+last_ocr_ts)
            self.recover_mad()
            
    def recover_mad(self):
        process = Popen([self.login_script], stdout=PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        self.logger.info("Performed ?click login command.")
        time.sleep(40)
        os.system(self.reset_all_script+'  >/tmp/MADreset_all.log 2>&1 &')
        self.logger.info("Performed ?reset all command.")
        time.sleep(120)
        os.system(self.reset_scanner_script+' >/tmp/MADreset_scanner.log 2>&1 &')
        self.logger.info("Performed ?reset scanner command.")
        threading.Timer(405, self.check_mad).start()#need to give scanner time to get back up before checking again

madctl_path = '/home/pjdrm/Desktop/MADctl/'
log_file = '/home/pjdrm/eclipse-workspace/TeamRocketSpy/madctl_monitor.log' 
mon = MADMonitor(log_file, madctl_path)
mon.check_mad()
