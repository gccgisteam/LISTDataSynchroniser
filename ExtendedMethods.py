####=================####
#Author: Alex Leith
#Date: 26/08/13
#Version: 0.0.1
#Purpose: Gets methods out of the main body. There is a custom 'processTriggers' method that needs to be removed for most people.
####=================####

from ftplib import FTP
import ConfigParser
import socket
import os
import smtplib
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.utils import COMMASPACE
from email import Encoders
import types
import globals
import zipfile

#Check for trigger files and if found, set up trigger. #CUSTOMISE THIS#
def processTriggers(downloadedFiles):
    
    if(len(downloadedFiles) == 0):
        globals.logging.info("No files downloaded, so no script triggers checked.")
        return '',globals.logging
        
    #Lists of triggers for FME scripts.
    fmeTrigger = 0 #FME Script Triggers
    twTrigger = 0 #SW script trigger
    
    #email message text.
    messageText = ''
    
    fmeTriggerList = ['Private_leases.zip',    'leases.zip',    'licences.zip',    'pluc.zip',    'lga_reserves.zip',    'transport.zip']
    TasWaterTriggerList = ['ReuseLines.zip', 'ReusePts.zip', 'SewerLines.zip', 'SewerPts.zip', 'WaterLines.zip', 'WaterPts.zip']
    
    #Required: Buildings, Heritage, Contours 2m, Public Toilets, AssetAreas, Kerbs, Zoning, Notations, Ordinance, stormwaterpipes, stormwaterpits
    monthlyFilesList = [\
        "C:\GIS\Projects\External\Scheduled\LIST_ftp\Upload\Buildings",\
        "TopographicInformation\Cultural\Heritage",\
        "TopographicInformation\Infrastructure\BuildingPlumbing\PublicToilets",\
        "TopographicInformation\Transport\kerbs",\
        "LandUseAndAdministration\Planning\zoning",\
        "LandUseAndAdministration\Planning\Notations",\
        "TopographicInformation\Infrastructure\Stormwater\Stormwaterpipes",\
        "TopographicInformation\Infrastructure\Stormwater\Lagoons",\
        "TopographicInformation\Infrastructure\Stormwater\Stormwaterpits"]
    
    for j in downloadedFiles:
        #monthly script
        for k in fmeTriggerList:
            if(k == j):
                fmeTrigger = 1
        #tas water script
        for l in TasWaterTriggerList:
            if(l == j):
                twTrigger = 1
            
    if(fmeTrigger):
        globals.logging.info("Downloaded an FME trigger layer, triggering the FME script.")
        os.system("C:\Scripts\FME\monthly.cmd")
        globals.logging.info("FME Monthly Script has been run.")
        
        globals.logging.info("Zipping and Uploading Data.")
        
        rootDir = "C:\GIS\Corporate"
        sentItems = []
        
        #connect to FTP
        connected = 0
        try:
            globals.logging.info('Connecting to FTP site for Upload')
            ftp = FTP(globals.SITE)
            ftp.login(globals.UN,globals.PW)
            connected = 1
        except (EOFError, socket.error):
            globals.logging.error("FTP Connection Failed")
            connected = 0
        
        if(connected):
            for uploadItem in monthlyFilesList:
                #Set up files for monthly upload...                
                destFile = uploadItem.split('\\')[-1] + ".zip"
                sentItems.append(destFile)
                if (not "C:\\" in uploadItem):
                    source = os.path.join(rootDir, uploadItem) + ".*"
                else:
                    source = uploadItem + ".*"
                    
                destination = os.path.join("C:\GIS\Projects\External\Scheduled\LIST_ftp\Upload", destFile)
                os.system(r'"C:\Program Files\7-Zip\7z.exe" a %s %s -tzip' %(destination, source))
            
                fp = open(destination,'rb') # file to send
                ftp.storbinary('STOR dpiwe_upload/Stormwaterpipes.zip', fp)
            
            globals.logging.info("GCC Data uploaded to The LIST. Notifying them of datasets uploaded.")
            
            #email The LIST
            subjectTextLIST = "GCC Data Supply"    
            messageTextLIST = "Hi there \n\nWe supplied:\n"
            for i in sentItems:
                messageTextLIST = messageTextLIST + "* " + i + "\n"
            messageTextLIST = messageTextLIST + "\nRegards,\n\nGCC GIS\ngis@gcc.tas.gov.au"
            
            sendEmail(globals.emailAddress, globals.emailAddressLIST, subjectTextLIST, messageTextLIST, "0")
            globals.logging.info("Email sent to The LIST")
        else:
            globals.logging.warning("Monthly data upload FAILED!")
            messageText = messageText + "\n\nWarning: Monthly data upload FAILED!\n"

        ftp.quit()

    if(twTrigger):
        globals.logging.info("Downloaded a Southern Water trigger layer, triggering the FME script.")
        os.system("C:\\Scripts\\FME\\tasWater.cmd")
        globals.logging.info("SW Script has been run.")

    if(fmeTrigger):
        messageText = messageText + "\n\nNOTE: FME script was run, data were uploaded to The LIST.\nCheck for other data to upload this month, update the Data Dictionary and notify The List.\n"

    if(twTrigger):
        messageText = messageText + "\n\nNOTE: Southern Water (WaterSewer) script was run. Update the Data Dictionary and check Exponare.\n"

    return messageText, globals.logging

    
#OTHER METHODS
##METHODS##

#sends an email with one subject, message and attachment
def sendEmail(emailFrom, emailTo, subject, message, attachment):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = emailFrom
    
    if(type(emailTo) == types.ListType):
        msg['To'] = COMMASPACE.join(emailTo)
    else:
        msg['To'] = emailTo
        emailTo = [emailTo]
    
    msg.attach(MIMEText(message))
    
    if(attachment != "0"):
        #attach the log file
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(globals.logFile,"rb").read() )
        Encoders.encode_base64(part)
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

    print "Downloading: "+remoteFile
    try:
        ftp.retrbinary("RETR " + remoteFile, f.write)
        f.close()

        globals.downloadedFiles.append(remoteFile)
        globals.logging.info("Retrieved: " + remoteFile + " to: " + localFile)
        globals.logging.info("Unzipping...")
        unzip(localFile, globals.localPath)
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
