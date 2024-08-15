####=================####
#Author: Alex Leith, Duri Bradshaw
#Date: 2024-08-15
#Version: 1.2.0
#Purpose: To automate the downloading and uploading of GIS data from the LIST FTP server
#Usage: LISTDataSynchroniser.py -c "c:\Path\to\configFile.txt" (-t 1) the () bit is optional 
#       and will run the method 'processTriggers' from the ExtendedMethods file..
####=================####

##Import statements (could be pared down a bit)
import os.path
import ftplib
import socket #used to catch ftp error
import configparser
from optparse import OptionParser #parse command line arguments
import ExtendedMethods #a file full of custom methods including triggers.
import globals

#handle command line arguments
processTriggersScript = 0
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
config = configparser.ConfigParser()
config.read(configFile)

#[log]
lf = config.get("log","logFile")
globals.localPath = config.get("log","localPath")

#set up global variable file
globals.init(lf)

#[email]
globals.emailAddress = config.get("email","emailAddress")
globals.mailServer = config.get("email","mailServer")
globals.emailAddressLIST = [i[1] for i in config.items("listEmail")]

#[ftpdetails]
globals.SITE = config.get("ftpdetails","SITE")
globals.UN = config.get("ftpdetails","UN")
globals.PW = config.get("ftpdetails","PW")
dirString = config.get('ftpdetails', 'ftpDirs')
remoteDirs = [dir.strip() for dir in dirString.split(',')]
    
#email strings
warnText = ""
subjectText = "FTP Download Script Run"
messageText = ""
triggerText = ""

# lists
localFileList = []
localFileSize = []
fileNames = [] #remote file names (abstracted, e.g., southern water) this is redundant and should be removed

#connect to FTP
connected = 0
try:
    globals.logging.info('Connecting to FTP site')
    ftp = ftplib.FTP(globals.SITE)
    ftp.login(globals.UN,globals.PW)
    connected = 1
except (EOFError, socket.error, ftplib.error_perm):
    print('Error: FTP Connection failed.')
    globals.logging.error("FTP Connection Failed...")
    connected = 0

#Find local files.
for file in os.listdir(globals.localPath):
    if (os.path.splitext(file)[1].lower() == '.zip'):        
        localFileList.append(file)
        file2 = os.path.join(globals.localPath, file)    
        localFileSize.append(str(os.path.getsize(file2)))
        globals.logging.debug('found local: ' + file + ", file size is: " + str(localFileSize[-1]))

countMatches = 0
if (connected):
    for dir in remoteDirs:
        tempList = [] #temporary remote file list

        #Move to remote Directory
        globals.logging.info('Connected to LIST FTP site  -  ' + dir)
        try:
            ftp.cwd(dir)
        except ftplib.error_perm as e:
            globals.logging.error('Cannot CD to ' + dir)
            ftp.quit()
        globals.logging.info('FTP: CWD %s OK' % dir)

        #Find remote files
        ftp.dir(tempList.append)
        for line in tempList:
            if (os.path.splitext(line)[1].lower() == '.zip'):         
                fileName, fileSize = ExtendedMethods.getAttributes(line)          
                globals.logging.debug('found remote: ' + fileName + ", file size is: " + fileSize)
                fileNames.append(fileName)  

                #Download new files
                matchNotFound = 1
                for n,localFile in enumerate(localFileList):
                    if(fileName == localFile):    
                        matchNotFound=0
                        if(fileSize == localFileSize[n]):
                            globals.logging.debug("Found Match! Don't download file: " + fileName)
                            countMatches = countMatches + 1
                        else:                
                            globals.logging.info("Found Match! Add file for download: " + fileName)
                            fullLocalFile = os.path.join(globals.localPath, fileName)              
                            ExtendedMethods.downloadFile(fullLocalFile, fileName, ftp)  
                if(matchNotFound):
                    globals.logging.info("Downloading new file: " + fileName)
                    fullLocalFile = os.path.join(globals.localPath, fileName)
                    ExtendedMethods.downloadFile(fullLocalFile, fileName, ftp)

    globals.logging.info("%i file matches found, not downloading." %countMatches)
    
    #process triggers, optional step
    triggerText = ''
    if(processTriggersScript):
        triggerText, globals.logging = ExtendedMethods.processTriggers(globals.downloadedFiles)
        
    #Determine which files are no longer on the server.
    for i in localFileList:
        found = 0
        for j in fileNames:
            if(i == j):
                found = 1
                break
        if(not found):
            globals.logging.warning("Found local file, %s , no longer in remote directory." %i)
            warnText = warnText + "Local file: %s no longer in remote directory.\n" %i

    ftp.quit()
    globals.logging.info("Sending email")
    messageText = "---- Message from Server DC3GISD02 ----\nDownload was successful\n%i new file(s) downloaded:" %(len(globals.downloadedFiles))

else:
    #Script Failed to Connect to FTP
    subjectText = "NOTICE! FTP Script Failed to Connect"
    messageText = "Download Failed, check FTP connection manually and rerun."

##email details##
for i in globals.downloadedFiles:
    messageText = messageText + "\n- %s" %i

messageText += triggerText

if(len(warnText) > 1):
    messageText = messageText + "\n\n~~~Warning!~~~\n" + warnText

#Send email to GIS
ExtendedMethods.sendEmail(globals.emailAddress, globals.emailAddress, subjectText, messageText, globals.logFile)

globals.logging.info("Email sent")
globals.logging.info("Script Ends")





