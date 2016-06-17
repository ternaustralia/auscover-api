#!/bin/bash
#
# Sync the WPS python scripts to the correct location
#
#DEST='/var/lib/tomcat7/webapps/geoserver-dev/data/scripts/wps/'
#SCRIPT='mntest.py timeSeries.py'
#echo 'Copying ' $SCRIPT ' to ' $DEST
#cp $SCRIPT $DEST

DEST='/usr/lib/cgi-bin/'
FILES='auscover-wps.py\ntimeSeries.zcfg\nmain.cfg'

echo -e "Syncing to ${DEST} ...\n"
echo -e $FILES |rsync -vt --files-from - . ${DEST}
