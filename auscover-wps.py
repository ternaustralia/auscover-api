# -*- coding: utf-8 -*-
#
# Author : Matt Nethery
#
#
#####
import zoo
import subprocess
from simplejson import loads, dump
import sys, os
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
        point = 'POINT(%s %s)' % (lon, lat)
      elif lon_lat_position[0].upper() == 'P':    #then it's a POINT
        point = lon_lat_position       
      else:		# lon,lat specified
        lat = lon_lat_position.split(',')[1]
        lon = lon_lat_position.split(',')[0]
        point = 'POINT(%s %s)' % (lon, lat)
    
      if 'NULL' in variables:
        vs = '-vdefault'
      else:
        vs = '-v%s' % variables

      #latlon = '%s,%s' % (lat, lon)
      #latlon = '%s,%s' % ('-35.0', '149.0')
      cargs = ['-d%s' % layer, '-p%s' % point] + [vs]

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

def timeSeriesPoly(conf, inputs, outputs):
  DIR = '/var/rs/auscover-api/'
  cacheFile = ''
  layer = inputs["layer"]["value"]
  #lon_lat_position = urllib.unquote(inputs["lon_lat_position"]["value"])
  polygon = urllib.unquote(inputs["polygon"]["value"])
  variables = urllib.unquote(inputs["variables"]["value"])
  #print layer, lon_lat_position  
  if layer == 'NULL':
    cargs = ['-l']
  else:
    if polygon == 'NULL':
      cargs = ['-l%s' % layer]
    else:
      if polygon[0] == '{':	#then it's json
        jd = loads(polygon)
        from datetime import datetime
        # save to temp file
        cacheFile = '/var/cache/auscover/tmpPoly-%s.geojson' % datetime.now().strftime('%Y%m%dT%H%M%S')
        with open(cacheFile, 'w') as jf:
          dump(jd, jf)
      else:		# lon,lat specified
        print 'timeSeriesPoly: Error - can\'t determine polygon!'
        sys.exit(1)

      if 'NULL' in variables:
        vs = '-vdefault'
      else:
        vs = '-v%s' % variables

      cargs = ['-d%s' % layer, '-p%s' % cacheFile] + [vs]

  cmd = ['/usr/bin/python', DIR + 'ts-request.py'] + cargs

  cmdout = ''
  #p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  cmdout += subprocess.check_output(cmd)

  # for debug
  #cmdout += 'Layer: %s; Polygon: %s; Variables: %s \n' % (layer, cacheFile, vs)
  cmdout += ' '.join(cmd)

  # cleanup
  #if os.path.exists(cacheFile): os.remove(cacheFile)

  #outputs["Result"]["value"] = "Layer selected: " + inputs["layer"]["value"] + ",Finished!"
  outputs["Result"]["value"] = cmdout

  return zoo.SERVICE_SUCCEEDED
#####

