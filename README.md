This program synchronises data from the Tasmanian Government's 'LIST' website.

It is intended for use by local governments or other agencies in Tasmania that have a login to the LIST via ftp to download data.

What it does is compares a local directory to the directory on the LIST's ftp server and downloads any files that are a different size.

It should work reliably and does nice things like keeps a log and emails you a summary.

It has been customised to run some scripts for us at Glenorchy City Council, and this can be used as a guide.

Some enhancements that could be undertaken include:
* logging to SQL Server or similar so that changes over time are tracked
* using http rather than ftp for the connection
* more comprehensive or rigorous extension/trigger system
