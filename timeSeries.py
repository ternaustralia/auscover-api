# timeSeries.py - a WPS wrapper called by GeoServer
#
#  Note: as this is called from within the GeoServer app it runs under jython
#
#####
from geoserver.wps import process
#from com.vividsolutions.jts.geom import Geometry
import subprocess
import sys

#####

@process(
  title='timeSeries',
  description='Extract a time series from a layer',
  inputs={
    'layer': (str, 'Unique layer name'),
    'latlon': (str,'Location coords in lat,lon')
  },
  outputs={
    #'result': (str, 'Time series data for location'),
    'result': (str, 'Time series data for location', {'mimeType': (str, 'application/json')})
  }
)
def run(layer='', latlon=''):
  # For testing
  #out = 'Layer: %s  and LatLon: %s\n\n' % (layer, latlon)

  # What the real call should be
  # if layer is blank then return a list of layers
  # if layer is non-blank check that it exists, and if latlon blank return error to say it is required
  
  DIR = '/var/rs/auscover-api/'
  if layer == '':
    cargs = '-l'
  #cmd = ['cat', DIR + 'soilm-ts.csv']
  cmd = ['python', DIR + 'ts-request.py', cargs]
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  cmdout = p.communicate()[0]
  out = '<xml>%s</xml>' % cmdout
  return out

