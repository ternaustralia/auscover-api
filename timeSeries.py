# timeSeries.py - a WPS wrapper called by GeoServer
#
#  Note: as this is called from within the GeoServer app it runs under jython
#
#####
from geoserver.wps import process
from com.vividsolutions.jts.geom import Geometry
from com.vividsolutions.jts.geom import Point
import subprocess
#from simplejson import loads as jsload
import sys

#####

@process(
  title='timeSeries',
  description='Extract a time series from a layer',
  inputs={
    'layer': (str, 'Unique layer name'),
    #'latlon': (str,'Location coords in lat,lon')
    #'lon_lat_position': (str, 'Point location in geoJSON')
    'lon_lat_position': (Point, 'Point location in geoJSON')
    #'lon_lat_position': (Geometry, 'Point location in geoJSON', {'mimeTypes':'application/vnd.geo+json','chosenMimeType':'application/vnd.geo+json'})
  },
  outputs={
    #'result': (str, 'Time series data for location')
    'result': (str, 'Time series data for location', {'mimeType': (str, 'text/csv')})
  }
)
def run(layer='', lon_lat_position=''):
#def run(layer='', latlon=''):
  # For testing
  #out = 'Layer: %s  and LatLon: %s\n\n' % (layer, latlon)

  # What the real call should be
  # if layer is blank then return a list of layers
  # if layer is non-blank check that it exists, and if latlon blank return error to say it is required

  #print layer, latlon  
  print layer, lon_lat_position  
  DIR = '/var/rs/auscover-api/'
  if layer == '':
    cargs = ['-l']
  else:
    #/usr/lib/python2.7/dist-packages/simplejson
    try:
      sys.path.append('/usr/lib/python2.7/dist-packages/')
      import simplejson as json
    except Exception, e:
      print e

    jd = json.loads(lon_lat_position)
    lat = jd['features'][0]['geometry']['coordinates'][1]
    lon = jd['features'][0]['geometry']['coordinates'][0]
    latlon = '%s,%s' % (lat, lon)
    #latlon = '%s,%s' % ('-35.0', '149.0')
    cargs = ['-d%s' % layer, '-b%s' % latlon]

  cmd = ['/usr/bin/python', DIR + 'ts-request.py'] + cargs
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  cmdout = p.communicate()[0]
  out = cmdout

  #out = str(cmd)
  #out = str(sys.path)

  return out

