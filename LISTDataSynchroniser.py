####=================####
#Author: Alex Leith
#Date: 26/08/13
#Version: 1.1.0
#Purpose: To automate the downloading and uploading of GIS data from the LIST FTP server
#Usage: LISTDataSynchroniser.py -c "c:\Path\to\configFile.txt" (-t 1) the () bit is optional 
#       and will run the method 'processTriggers' from the ExtendedMethods file..
####=================####

##Import statements (could be pared down a bit)
import logging, os.path, time
from ftplib import FTP
import smtplib
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.utils import COMMASPACE
from email import Encoders
import types
import socket #used to catch ftp error
import ConfigParser
from optparse import OptionParser #parse command line arguments
import ExtendedMethods #a file full of custom methods including triggers.
import zipfile

#handle command line arguments
processTriggersScript = 0;
configFile = "LIST_ftp_script_details.txt"
parser = OptionParser()
parser.add_option("-c", "--config", dest="configFile",
                  help="File to load configuration from", metavar="FILE")
parser.add_option("-t", "--triggers", dest="processTriggersScript",
                  help="True or false for processing the triggers script", metavar="FILE")
(options, args) = parser.parse_args()
if(options.configFile):
    configFile = options.configFile
processTriggersScript = options.processTriggersScript
#load config
config = ConfigParser.ConfigParser()
config.read(configFile)

print

#[email]
emailAddress = config.get("email","emailAddress")
mailServer = config.get("email","mailServer")
#[log]
logFile = config.get("log","logFile")
localPath = config.get("log","localPath")
#[ftpdetails]
SITE = config.get("ftpdetails","SITE")
UN = config.get("ftpdetails","UN")
PW = config.get("ftpdetails","PW")
    
#email strings
warnText = ""
subjectText = "FTP Download Script Run"
messageText = ""
triggerText = ""

#some lists
tempList = [] #temporary remote file list
fileList = [] #remote file list, full file details
fileNames = [] #remote file names (abstracted, e.g., southern water) this is redundant and should be removed
fileNameTrue = [] #remote file names (actual)
remoteFileSize = [] #remote file size
localFileList = []
localFileSize = []
downloadedFiles = [] #a list of files that were downloaded

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
        part.set_payload( open(logFile,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(logFile))
        msg.attach(part)
    
    s = smtplib.SMTP(mailServer)
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

def downloadFile(localFile, remoteFile):
    f = open(localFile,"wb")

    print "Downloading: "+remoteFile
    ftp.retrbinary("RETR " + remoteFile, f.write)
    f.close()

    downloadedFiles.append(remoteFile)
    logging.info("Retrieved: " + remoteFile + " to: " + localFile)
    logging.info("Unzipping...")
    unzip(localFile, localPath)
    #os.system(r'"C:\Program Files\7-Zip\7z.exe" e %s -oC:\GIS\Projects\External\Scheduled\LIST_ftp -y' % localFile)

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

##everything else##

#set up log
logging.basicConfig(filename=logFile, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO, filemode='w')
logging.info('Script starts')
#logging.basicConfig(filename='C:\GIS\Projects\GIS-Admin\FTPDL\LIST_FTP_Download.log',level=logging.INFO)

#connect to FTP
connected = 0
try:
    logging.info('Connecting to FTP site')
    ftp = FTP(SITE)
    ftp.login(UN,PW)
    connected = 1
except (EOFError, socket.error):
    logging.error("FTP Connection Failed")
    connected = 0

if (connected):
    #Find remote files
    ftp.dir(tempList.append)

    for line in tempList:    
        if (os.path.splitext(line)[1].lower() == '.zip'):
            fileList.append(line)            
            fileName, fileSize = getAttributes(line)            
            fileNameTrue.append(fileName)            
            remoteFileSize.append(fileSize)
            logging.debug('found remote: ' + fileName + ", file size is: " + fileSize)

            fileNames.append(fileName)

    #Find local files.
    for file in os.listdir(localPath):
        if (os.path.splitext(file)[1].lower() == '.zip'):        
            localFileList.append(file)
            file2 = os.path.join(localPath, file)    
            localFileSize.append(str(os.path.getsize(file2)))
            logging.debug('found local: ' + file + ", file size is: " + str(localFileSize[-1]))

    #Download new files
    countMatches = 0
    for n,rFile in enumerate(fileNames):
        matchNotFound = 1
        for n2,localFile in enumerate(localFileList):
            if(fileNames[n] == localFile):    
                matchNotFound=0
                if(remoteFileSize[n] == localFileSize[n2]):
                    logging.debug("Found Match! Don't download file: " + fileNames[n])
                    countMatches = countMatches + 1
                else:                
                    logging.info("Found Match! Add file for download: " + fileNames[n])                 

                    fullLocalFile = os.path.join(localPath, fileNames[n])
                    fullRemoteFile = fileNameTrue[n]                    
                    downloadFile(fullLocalFile, fullRemoteFile)                 
                    
        if(matchNotFound):    
            logging.info("Downloading new file: " + rFile)

            fullLocalFile = os.path.join(localPath, fileNames[n])
            fullRemoteFile = fileNameTrue[n]
            downloadFile(fullLocalFile, fullRemoteFile)

    logging.info("%i file matches found, not downloading." %countMatches)
   
    #process triggers, optional step
    triggerText = ''
    if(processTriggersScript):
        triggerText, logging = ExtendedMethods.processTriggers(downloadedFiles, logging)
    
    #Determine which files are no longer on the server.
    for i in localFileList:
        found = 0
        for j in fileNames:
            if(i == j):
                found = 1
                break
        if(not found):
            logging.warning("Found local file, %s , no longer in remote directory." %i)
            warnText = warnText + "Local file: %s no longer in remote directory.\n" %i

    logging.info("Sending email")
    messageText = "Download was successful\n%i new file(s) downloaded:" %(len(downloadedFiles))

else:
    #Script Failed to Connect to FTP
    subjectText = "NOTICE! FTP Script Failed to Connect"
    messageText = "Download Failed, check FTP connection manually and rerun."

##email details##
for i in downloadedFiles:
    messageText = messageText + "\n- %s" %i

messageText += triggerText

if(len(warnText) > 1):
    messageText = messageText + "\n\n~~~Warning!~~~\n" + warnText

#Send email to GIS
sendEmail(emailAddress, emailAddress, subjectText, messageText, logFile)

logging.info("Email sent")
logging.info("Script Ends")





