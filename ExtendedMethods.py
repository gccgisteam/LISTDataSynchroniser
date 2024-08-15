####=================####
#Author: Alex Leith, Duri Bradshaw
#Date: 2024-08-15
#Version: 0.0.2
#Purpose: Gets methods out of the main body. There is a custom 'processTriggers' method that needs to be removed for most people.
####=================####

import ftplib
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import COMMASPACE
from email import encoders
import globals
import zipfile
import glob

#Check for trigger files and if found, set up trigger. #CUSTOMISE THIS#
def processTriggers(downloadedFiles):
    
    if(len(downloadedFiles) == 0):
        globals.logging.info("No files downloaded, so no script triggers checked.")
        return '',globals.logging
        
    #Lists of triggers for FME scripts.
    fmeTrigger = 0 #FME Script Triggers
    twTrigger = 0 #TW script trigger
    
    #email message text.
    messageText = ''
    
    fmeTriggerList = ['Private_leases.zip',    'leases.zip',    'licences.zip',    'pluc.zip',    'lga_reserves.zip',    'transport.zip']
    TasWaterTriggerList = ['TasWater_Assets.zip']
    unzipList = ['TasNetworks_LGAs.zip']
    
    #Required: Buildings, Heritage, Kerbs, stormwaterpipes, stormwaterpits
    monthlyFilesList = [\
        "D:\\GIS\\Projects\\External\\Scheduled\\LIST_ftp\\Upload\\Buildings",\
        "TopographicInformation\\Cultural\\Heritage",\
        "TopographicInformation\\Transport\\kerbs",\
		"TopographicInformation\\Transport\\TrafficManagementDevice",\
        "TopographicInformation\\Infrastructure\\Stormwater\\Stormwaterpipes",\
        "TopographicInformation\\Infrastructure\\Stormwater\\Stormwaterpits"]
    
    for j in downloadedFiles:
        print('downloaded: ', j)
        #monthly script
        for k in fmeTriggerList:
            if(k == j):
                fmeTrigger = 1
        #Tas Water script
        for l in TasWaterTriggerList:
            if(l == j):
                twTrigger = 1
        #unzip list
        for o in unzipList:
            if(o == j):
                fullLocalFile = os.path.join(globals.localPath, j)    
                unzip(fullLocalFile, globals.localPath)

    if(fmeTrigger):
        globals.logging.info("Downloaded an FME trigger layer, triggering the FME script.")
        os.system("C:\Scripts\FME\monthly.cmd")
        globals.logging.info("FME Monthly Script has been run.")
        
        globals.logging.info("Zipping and Uploading Data.")
        
        rootDir = "D:\GIS\Corporate"
        sentItems = []
        
        #connect to FTP
        connected = 0
        
        globals.logging.info('Connecting to FTP site for Upload')            
        ftp = ftplib.FTP(globals.SITE)
        ftp.login(globals.UN,globals.PW)
        connected = 1
        
        #remove existing zip files
        for fl in glob.glob("D:\\GIS\\Projects\\External\\Scheduled\\LIST_ftp\\Upload\\*.zip"):
            os.remove(fl)
        
        if(connected):
            for uploadItem in monthlyFilesList:
                #Set up files for monthly upload...                
                destFile = uploadItem.split('\\')[-1] + ".zip"
                sentItems.append(destFile)
                if (not "C:\\" in uploadItem):
                    source = os.path.join(rootDir, uploadItem) + ".*"
                else:
                    source = uploadItem + ".*"

                destination = os.path.join("D:\GIS\Projects\External\Scheduled\LIST_ftp\\Upload", destFile)
                
                print('creating archive')
                zf = zipfile.ZipFile(destination, mode='w')
                try:
                    for fl in glob.glob(source):
                        if(os.path.splitext(fl)[1] == '.zip'): continue
                        print(fl)
                        zf.write(fl,os.path.basename(fl),compress_type=zipfile.ZIP_DEFLATED)
                finally:
                    print('closing')
                    zf.close()
            
                fp = open(destination,'rb') # open file to send
                ftp.storbinary('STOR dpiwe_upload/{0}'.format(destFile), fp)
            
            globals.logging.info("GCC Data uploaded to The LIST. Notifying them of datasets uploaded.")
            
            #email The LIST
            subjectTextLIST = "GCC Data Supply"    
            messageTextLIST = "Hi there \n\nWe supplied:\n"
            for i in sentItems:
                messageTextLIST = messageTextLIST + "* " + i + "\n"
            messageTextLIST = messageTextLIST + "\nRegards,\n\nGCC GIS\ngis@gcc.tas.gov.au"
            
            sendEmail(globals.emailAddress, globals.emailAddressLIST, subjectTextLIST, messageTextLIST, "0")
            globals.logging.info("Email sent to The LIST")
            ftp.quit()
        else:
            globals.logging.warning("Monthly data upload FAILED!")
            messageText = messageText + "\n\nWarning: Monthly data upload FAILED!\n"
			
    if(twTrigger):
        globals.logging.info("Downloaded a TasWater trigger layer, triggering the FME script.")
        os.system("C:\\Scripts\\FME\\tasWater.cmd")
        globals.logging.info("TasWater Script has been run.")

    if(fmeTrigger):
        messageText = messageText + "\n\nNOTE: FME script was run, data were uploaded to The LIST.\nCheck for other data to upload this month, update the Data Dictionary and notify The List.\n"

    if(twTrigger):
        messageText = messageText + "\n\nNOTE: TasWater script was run. Update the Data Dictionary and check Exponare.\n"

    return messageText, globals.logging
    
#OTHER METHODS
##METHODS##

#sends an email with one subject, message and attachment
def sendEmail(emailFrom, emailTo, subject, message, attachment):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = emailFrom
    
    if(type(emailTo) == list):
        msg['To'] = COMMASPACE.join(emailTo)
    else:
        msg['To'] = emailTo
        emailTo = [emailTo]
    
    msg.attach(MIMEText(message))
    
    if(attachment != "0"):
        #attach the log file
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(globals.logFile,"rb").read() )
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(globals.logFile))
        msg.attach(part)
    
    s = smtplib.SMTP(globals.mailServer)
    s.sendmail(emailFrom, emailTo, msg.as_string())
    s.quit()
    
#takes input from the file listing from the ftp site and returns a list of file names (fn) and file sizes (fs)
def getAttributes(line):
    lineSplit = line.split(' ')
    lineSplit = [x for x in lineSplit if x != ""]
    
    #file size
    fs = lineSplit[4]
    fnList = lineSplit[8:]
    
    #file name
    fn = ""
    for i in fnList:
        fn = fn + i + " "
    fn = fn.strip()
    
    return fn,fs

def downloadFile(localFile, remoteFile, ftp):
    f = open(localFile,"wb")

    print("INFO: Downloading: "+remoteFile)
    try:
        ftp.retrbinary("RETR " + remoteFile, f.write)
        f.close()

        globals.downloadedFiles.append(remoteFile)
        globals.logging.info("Retrieved: " + remoteFile + " to: " + localFile)
        #globals.logging.info("Unzipping...")
        #unzip(localFile, globals.localPath)
    except Exception as e:
        globals.logging.error("Failed to retrieve: " + remoteFile + " to: " + localFile + " error was: " + str(e))
        f.close()

#unzip files
def unzip(zipFilePath, destDir):
    zfile = zipfile.ZipFile(zipFilePath)
    for name in zfile.namelist():
        (dirName, fileName) = os.path.split(name)
        if fileName == '':
            # directory
            newDir = destDir + '/' + dirName
            if not os.path.exists(newDir):
                os.mkdir(newDir)
        else:
            # file
            fd = open(destDir + '/' + name, 'wb')
            fd.write(zfile.read(name))
            fd.close()
    zfile.close()
