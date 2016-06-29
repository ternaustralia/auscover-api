# -*- coding: utf-8 -*-
#
# Author : Matt Nethery
#
#
#####
import zoo
import subprocess
from simplejson import loads
import sys
import urllib
#####
def timeSeries(conf, inputs, outputs):
  DIR = '/var/rs/auscover-api/'
  layer = inputs["layer"]["value"]
  lon_lat_position = urllib.unquote(inputs["lon_lat_position"]["value"])
  variables = urllib.unquote(inputs["variables"]["value"])
  #print layer, lon_lat_position  
  if layer == 'NULL':
    cargs = ['-l']
  else:
    if lon_lat_position == 'NULL':
      cargs = ['-l%s' % layer]
    else:
      if lon_lat_position[0] == '{':	#then it's json
        jd = loads(lon_lat_position)
        lat = jd['features'][0]['geometry']['coordinates'][1]
        lon = jd['features'][0]['geometry']['coordinates'][0]
      else:		# lon,lat specified
        lat = lon_lat_position.split(',')[1]
        lon = lon_lat_position.split(',')[0]
    
      if 'NULL' in variables:
        vs = '-vdefault'
      else:
        vs = '-v%s' % variables

      latlon = '%s,%s' % (lat, lon)
      #latlon = '%s,%s' % ('-35.0', '149.0')
      cargs = ['-d%s' % layer, '-b%s' % latlon] + [vs]

  cmd = ['/usr/bin/python', DIR + 'ts-request.py'] + cargs

  cmdout = ''
  # for debug
  #cmdout = 'Layer: %s; LonLatPos: %s; Variables: %s \n' % (layer, lon_lat_position, vs)
  #cmdout = ' '.join(cmd)

  p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  cmdout += p.communicate()[0]

  #outputs["Result"]["value"] = "Layer selected: " + inputs["layer"]["value"] + ",Finished!"
  outputs["Result"]["value"] = cmdout

  return zoo.SERVICE_SUCCEEDED
#####

