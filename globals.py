import logging

def init(lf):
    #set up global variables for use in multiple files.
    global logFile, emailAddress, mailServer, localPath,emailAddress,mailServer,emailAddressLIST,downloadedFiles
    logFile = lf
    downloadedFiles = []
    logging.basicConfig(filename=logFile, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO, filemode='w')
    logging.info('Script starts')
    #logging.basicConfig(filename='D:\GIS\Projects\GIS-Admin\FTPDL\LIST_FTP_Download.log',level=logging.INFO)