#!/bin/bash
#
# Move the WPS python script to the correct location in the GeoServer tree
#
DEST='/var/lib/tomcat7/webapps/geoserver-dev/data/scripts/wps/'
SCRIPT='mntest.py timeSeries.py'

echo 'Copying ' $SCRIPT ' to ' $DEST
cp $SCRIPT $DEST

