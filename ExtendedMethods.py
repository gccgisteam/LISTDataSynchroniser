####=================####
#Author: Alex Leith
#Date: 26/08/13
#Version: 0.0.1
#Purpose: To abstract some custom functionality from the main file, LISTDataSynchroniser.py
#         It does this poorly and should probably not be copied!
####=================####



#Check for trigger files and if found, set up trigger.
def processTriggers(downloadedFiles):
    import ftplib
    import ConfigParser
	#load config
    config = ConfigParser.ConfigParser()
    config.read("C:\GIS\Corporate\GISAdministration\Security\LIST_ftp_script_details.txt")
    #[listEmail]
    emailAddressLIST = [i[1] for i in config.items("listEmail")]
    #Lists of triggers for FME scripts.
    fmeTrigger = 0 #FME Script Triggers
    twTrigger = 0 #SW script trigger

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
        "TopographicInformation\Infrastructure\Stormwater\Stormwaterpits"]
    print 'TRIGGER PROCESSOR RAN'
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
        logging.info("Downloaded an FME trigger layer, triggering the FME script.")
        os.system("C:\Scripts\FME\monthly.cmd")
        logging.info("FME Monthly Script has been run.")
        
        logging.info("Zipping and Uploading Data.")
        
        rootDir = "C:\GIS\Corporate"
        sentItems = []
        
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
        
        logging.info("GCC Data uploaded to The LIST. Notifying them of datasets uploaded.")
        
        #email The LIST
        subjectTextLIST = "GCC Data Supply"    
        messageTextLIST = "Hi there \n\nWe supplied:\n"
        for i in sentItems:
            messageTextLIST = messageTextLIST + "* " + i + "\n"
        messageTextLIST = messageTextLIST + "\nRegards,\n\nGCC GIS\ngis@gcc.tas.gov.au"
        
        sendEmail(emailAddress, emailAddressLIST, subjectTextLIST, messageTextLIST, "0")
        logging.info("Email sent to The LIST")

        ftp.quit()
    else:
        ftp.quit()

    if(twTrigger):
        logging.info("Downloaded a Southern Water trigger layer, triggering the FME script.")
        os.system("C:\Scripts\FME\southernWater.cmd")
        logging.info("SW Script has been run.")

    messageText = ''
    if(fmeTrigger):
        messageText = messageText + "\n\nNOTE: FME script was run, data were uploaded to The LIST.\nCheck for other data to upload this month, update the Data Dictionary and notify The List.\n"

    if(twTrigger):
        messageText = messageText + "\n\nNOTE: Southern Water (WaterSewer) script was run. Update the Data Dictionary and check Exponare.\n"

    return messageText