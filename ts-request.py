#!/bin/env python
#
# ts-request.py: Part of AusCover-API suite
#   request a timeseries for a point/polygon from a data layer
#

### Modules ###
import os, sys, re
import yaml
from pprint import pprint
from collections import OrderedDict as OD
#from subprocess import call as spc
#from subprocess import check_output
import subprocess as sp
from datetime import datetime

### Globals ###
Version = 'AusCover-API v0.1'
CacheDir = '/var/cache/auscover/'
YamlDir = '/var/rs/auscover-api/'
tmpncfile = ''

### Functions ###

def readYaml():
  """Read a file into a yaml list/dict object """
  yf = YamlDir + 'auscover-products.yaml'
  yd = [ OD() ]
  with open(yf, 'r') as fin:
    yd = yaml.safe_load(fin)
    #yd = yaml.safe_load(fin, Loader=yamlordereddictloader.Loader)
  return yd
#---

def listAllDatasets(yd):
  # field length - for printing
  flen = 50

  #print 'Contains %d items of %s' % (len(yd), type(yd))
  print ''
  #print 'ID  Layer/Product         Location'
  print '%3s' % 'ID', 'Layer/Product'.ljust(flen)[:flen], 'Type'.ljust(flen-40), 'Description'.ljust(flen+20)[:flen+20]
  print '%3s' % '--', '-------------'.ljust(flen)[:flen], '----'.ljust(flen-40), '-----------'.ljust(flen+20)[:flen+20]
  for i in range(len(yd)):
    print "%3s" % str(i+1), yd[i]['name'].ljust(flen)[:flen], yd[i]['type'].ljust(flen-40), yd[i]['description'].ljust(flen+40)[:flen+40]
#--- 

def listDatasetID(ds):
  #pprint(ds, indent=2, width=80)
  print ''
  print 'Description    : %s' % ds['description']
  print 'Type           : %s' % ds['type']
  print 'Location       : %s' % ds['location']
  print 'Variables      : %s' % ds['variables']
  print 'Temporal Extent: %s ... %s' % (ds['temporal_extent']['start'], ds['temporal_extent']['end'])
  print 'CRS            : %s' % ds['crs']
  print 'Spatial Extent : %s (upper-left) ... %s (lower-right)' % (ds['spatial_extent']['ul'], ds['spatial_extent']['lr'])
  print ''
#--- 

def errorParams(p):
  print 'This argument <%s> requires a value!' % p
  usage()
#--- 

def findNameinDict(d, n):
  i = 1
  m = 0
  for l in d:
    if l['name'] == n:
      m = i
      break
    i += 1
  return m
#--- 

def pointOrPoly(pp):
  #if p[0] == '{':
  if os.path.exists(pp):	# is it a filename that has been passed in
    ext = os.path.splitext(pp)[1]
    if ext.lower() == '.json' or ext.lower() == '.geojson':
      from json import load
      with open(pp) as jf:
        jd = load(jf)
        #if jd['features'][0]['geometry']['type'] == 'Polygon':
        if 'Polygon' in jd['features'][0]['geometry']['type']:
          return 'poly'
        elif jd['features'][0]['geometry']['type'] == 'Point':
          return 'point'
    elif ext.lower() == '.shp':
      return 'poly'
  else:
    if re.search('polygon', pp, re.I):
      return 'poly'
    #elif p[0] == 'P':
    elif re.search('point', pp, re.I):
      return 'point'
    else:
      print 'pointOrPoly: Unknown data type!'
      sys.exit(1)
#---

def extractLatLon(pp):
  #print pp
  m = re.match('^.*\((.*)\).*$', pp)
  if m:
    lat = m.group(1).split(' ')[1]
    lon = m.group(1).split(' ')[0]
    ll = '%s,%s' % (lat, lon)
    return ll
  else:
    print 'extractLatLon: can\'t extract location!'
    sys.exit(1)
#---

def parseArgs(args):
  #print args, type(args), len(args)
  #allArgs = ' '.join(args)
  #print allArgs, type(allArgs), len(allArgs)    
  # now resplit on ' ' ( '-' causes a problem for -ve latlons)
  #splitArgs = allArgs.split(' ')
  splitArgs = args
  #print splitArgs
  pargs = []
  for s in splitArgs:
    #ss = s.split(' ')
    #print ss
    # remove last item if blank
    #if s[-1] == '': s.pop(-1)
    #if len(s) == 0:
      #ignore
    #  pass
    
    #strip leading '-'
    if s[0] == '-': s = s.lstrip('-')

    #now insert args into list
    if len(s) == 1:
      pargs.append((s))
      #print 'arg: %s' % (ss[0])
    elif len(s) >= 2:
      pargs.append((s[0],s[1:]))
      #print 'arg: %s,  value: %s' % (ss[0], ss[1])
    else:
      print 'Unknown arguments', s
      usage()

  #print 'pargs: ', pargs
  # read in dict of available datasets
  yd = readYaml()

  dsid = 0
  var = pp = trange = ''
  fmt = 'csv'

  # now process the args
  freq = True
  for p in pargs:
    if p[0] == 'l':
      freq = False
      if len(p) == 1: 
        print 'List available datasets:'
        listAllDatasets(yd)
        break
      else:
        if re.match('\d+', p[1]):		# it's a number
          dsid = int(p[1]) 
        else:
          dsid = findNameinDict(yd, p[1])
        if dsid == 0:
          print 'Dataset not found: ', dsid
          sys.exit(1)
        #dsid = int(p[1])
        print 'Details for dataset <%d>: %s' % (dsid, yd[dsid - 1]['name'])
        listDatasetID(yd[dsid - 1]) 
        break
    if p[0] == 'd':
      if len(p) != 2: errorParams(p[0])
      #print 'Dataset chosen <%s>: %s' % ( p[1], yd[int(p[1]) -1]['name'] )
      if re.match('\d+', p[1]):		# it's a number
        dsid = int(p[1]) 
      else:
        dsid = findNameinDict(yd, p[1])
      if dsid == 0:
        print 'Dataset not found: ', dsid
        sys.exit(1)
    if p[0] == 'v':
      if len(p) != 2: errorParams(p[0])
      #print 'Variable chosen: ', p[1]
      var = p[1]
    if p[0] == 'p':
      if len(p) != 2: errorParams(p[0])
      #print 'Bounding box: ', p[1]
      pp = p[1]
    if p[0] == 't':
      if len(p) != 2: errorParams(p[0])
      #print 'Time range: ', p[1]
      trange = p[1]
    if p[0] == 'f':
      if len(p) != 2: errorParams(p[0])
      #print 'Time range: ', p[1]
      fmt = p[1]
    if p[0] == 's':
      freq = False
      #print 'Time-series csv ...'
      if len(p) > 1:
        fname = p[1]
        timeSeries(fname, var)
      else:
        timeSeries()
      break

  if freq:
    ds = yd[dsid - 1]
    if not var: var = ds['variables']
    if var == 'default': var = ds['variables']
    # is a point or polygon request
    if pointOrPoly(pp) == 'point':
      if ds['type'].lower() == 'file':
        cmd = ['/usr/bin/python', YamlDir + 'raster-stats.py', '%s' % ds['location'], pp, var]
        p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
        out, err = p.communicate()
        print out
        # for debugging
        #print '\nOut: %s\nErr: %s\n' % (out, err)

      else:
        ll = extractLatLon(pp)
        formRequest(ds, ll, var, trange, fmt)

    elif pointOrPoly(pp) == 'poly':
      if ds['type'].lower() != 'file':
        print 'Error: Can\'t use %s dataset type for a polygon search!' % ds['type']
        sys.exit(1)

      cmd = ['python', YamlDir + 'raster-stats.py', '%s' % ds['location'], pp, var]
      p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
      out, err = p.communicate()
      print out
      # for debugging
      #print '\nOut: %s\nErr: %s\n' % (out, err)

    else:
      print 'Error: can\'t determine if point or polygon!'
      sys.exit(1)

  # now formulate request for a point location
  #if freq: formRequest(yd[int(dsid -1)], ll, var, trange, fmt)
#--- 

def formRequest(ds, ll, var='', trange='', fmt='csv'):
  """Formulate request based on layer type."""
  global tmpncfile
  #print ds

  cmd = []

  #tmpncfile = 'tmp-xxx.nc' 
  tmpncfile = CacheDir + 'tmp-' + datetime.now().strftime('%Y%m%dT%H%M%S') + '.nc'

  #split bbox into lat/lon components
  lat = float(ll.split(',')[0])
  lon = float(ll.split(',')[1])
  delta = 0.10
  # and time range into start and end
  if trange != '':
    tstart = trange.split(',')[0]
    tend = trange.split(',')[1]
    ncssTsubset = '&time_start=%s' % tstart + '&time_end=%s' % tend + '&timeStride=1&accept=netcdf'
  else:
    tstart = ds['temporal_extent']['start']
    tend = ds['temporal_extent']['end']
    ncssTsubset = '&temporal=all' 
  # if var not specified pick default
  if var == 'default' or var == '':
    var = ds['variables'].split(',')[0]

  wcsTsubset = '&subset=time(\"%s\",\"%s\")' % (tstart, tend)
  #ncssTsubset = '&time_start=%s' % tstart + '&time_end=%s' % tend + '&timeStride=1&accept=netcdf'
  # according to docs can also use "temporal=all" in place of above

  # select query command based on type of data
  if ds['type'].lower() == 'netcdf':
    #print 'use ncks or gdallocationinfo'
    cmd = ['ncks', '-v' + var, '-d' + ll, ds['location']] 
  elif ds['type'].lower() == 'geotiff':
    #print 'use gdallocationinfo (not sure about time series)'
    cmd = ['gdallocationinfo', '-geoloc', ll, ds['location']] 
  elif ds['type'].lower() == 'wcs':
    #print 'use curl'
    #url = ds['location'] + '&time=%s' % trange + '&bbox=%s' % bbox
    #url = ds['location'] + '&format=application/x-netcdf' + '&subset=Lat(-34.5,-34.4)' + '&subset=Long(140.5,140.6)' + '&subset=time(\"2015-01-01T00:00:00.000Z\",\"2015-12-31T00:00:00.000Z\")'
    url = ds['location'] + '&format=application/x-netcdf' + \
          '&subset=Lat(%s,%s)' % (lat, lat + delta) + \
          '&subset=Long(%s,%s)' % (lon, lon + delta) + wcsTsubset
          #'&subset=time(\"%s\",\"%s\")' % (tstart, tend)
    #print url
    cmd = ['curl', '-s', url, '-o', tmpncfile] 
  elif ds['type'].lower() == 'ncss':
    #print 'use curl'
    #url = ds['location'] + '&time=%s' % trange + '&bbox=%s' % bbox
    #url = ds['location'] + '&north=-35.005' + '&west=140.005' + '&east=140.015' + '&south=-35.015' + '&disableProjSubset=on&horizStride=1' + '&time_start=2012-08-31T00%3A00%3A00Z' + '&time_end=2016-02-29T00%3A00%3A00Z' + '&timeStride=1&accept=netcdf'
    url = ds['location'] + '?var=%s' % (var) + '&disableProjSubset=on&horizStride=1' + \
          '&latitude=%s' % (lat) + \
          '&longitude=%s' % (lon) + \
          ncssTsubset + '&accept=netcdf'
          #'&north=%s' % (lat + delta) + \
          #'&west=%s' % (lon - delta) + \
          #'&east=%s' % (lon + delta) + \
          #'&south=%s' % (lat - delta) + ncssTsubset
          #'&time_start=%s' % tstart + '&time_end=%s' % tend + '&timeStride=1&accept=netcdf'
    #cmd = ['curl', '"%s"' % url, '-o %s' % tmpncfile] 
    cmd = ['curl', '-s', url, '-o', tmpncfile] 
  else:
    print ds['type'], ': don\'t know what to do with this type'
    sys.exit(1)

  # now run the command
  #print ''
  #print 'Running subset request ...'
  #print cmd
  #sys.exit(1)
  if sp.call(cmd):
    print 'Error in command: %s' % cmd
    sys.exit(1)

  # and generate the csv time-series
  #cmd = ['python', 'ts-out.py', tmpncfile, var]
  #print 'Generate csv ...'
  #print ''
  timeSeries(tmpncfile, var, fmt, ds, ll, trange)
  #if spc(cmd):
  #  print 'Error in command: %s' % cmd
  #  sys.exit(1)
 
   
#--- 

def timeSeries(infile=tmpncfile, var='default', fmt='csv', ds='default', latlon='default', trange='default'):
  """Produce a time series csv output from an NC file.
     Defaults to tmp-xxx input file and first variable found.
  """
  #####
  from netCDF4 import Dataset
  from netcdftime import utime
  from datetime import datetime
  from collections import OrderedDict
  import json
  from copy import copy
  #####

  filin = infile
  #print filin
  if not os.path.exists(filin):
    print ''
    print 'Cannot find file: %s !!!' % filin
    print ''
    sys.exit(1)

  ncf = Dataset(filin, 'r')
  cdftime = utime(ncf['time'].units)

  if var == 'default':
    #pick first variable in dataset
    #var = ncf.variables.keys()[0]
    mvars = ds['variables'].split(',')
  else:
    mvars = var.split(',')

  # formulate result into a dict
  result = OrderedDict()
  result['Version'] = Version
  if ds == 'default':
    result['Datasetname'] = filin
  else:
    result['Datasetname'] = ds['name']
  result['Variable'] = ','.join(mvars)
  result['LatLon'] = latlon
  result['TimeRange'] = trange
  result['Data'] = []
  ld = OrderedDict()
  #ld['Datetime'] = 'Datetime'
  #ld['Value'] = 'Value'
  #result['Data'].append(ld)
  for i in range(len(ncf['time'])):
    ld1 = copy(ld)
    ld1['Datetime'] = cdftime.num2date(ncf['time'][i]).strftime('%Y-%m-%d')
    #ld1['Value'] = format(ncf[var][i,0,0], '.2f')
    #ld1['Value'] = format(ncf[var][i,], '.2f')
    for j in range(len(mvars)):
      #ld1[mvars[j]] = format(ncf[mvars[j]][i,], '.2f')
      if ncf[mvars[j]].ndim == 1:
        ld1[mvars[j]] = str(ncf[mvars[j]][i,])
      elif ncf[mvars[j]].ndim == 2:
        ld1[mvars[j]] = str(ncf[mvars[j]][i,0,])
      elif ncf[mvars[j]].ndim == 3:
        ld1[mvars[j]] = str(ncf[mvars[j]][i,0,0])
      else:
        print 'Error: more than 3 ndims!'
        sys.exit(1)
    #print i, ld
    result['Data'].append(ld1)

  #print var
  #print result
  if fmt == 'json':
    print json.dumps(result, indent=2)
  else:
    print '%s,%s' % ('Datetime', result['Variable'])
    for r in result['Data']:
      #print '%s,%s' % (r['Datetime'], r['Value'])
      line = r['Datetime']
      for j in range(len(mvars)):
        line += ',' + r[mvars[j]]
      print line
  ncf.close()

#--- 

def usage():
  print ''
  print main.__doc__
  sys.exit(1)
#--- 

### MAIN ###
def main(*args):
  """
  USAGE: ts-request.py [ -l[dataset] -d<dataset> -v<variable> -b<bbox> -t<time_range> -f<output_format> -s[file-name] ]

  WHERE:
         -l[dataset] = list all available datasets (or specified dataset)
         -d<dataset> = dataset number
         -v<variable> = variable identifier
         -p<point/polygon> = POINT(lon lat) or GeoJSON object
         -t(time_range) = (start-time, end-time)
         -f<output_format> = [csv], json, nc, tif ...
         -s[file-name] = produce time-series from NC file (also requires -v<variable>)
  """

  #print ''
  #print '----------------------------'
  #print ' AusCover API - Dev Ver 0.1'
  #print '----------------------------'
  #print ''

  if len(args[0]) == 1:
      print ''
      print 'Program name: ', args[0][0]
      usage()
      #print main.__doc__
  else:
      parseArgs(args[0][1:])

  print ''
  #print '--- DONE ---'
  #print ''

  # clean up
  if os.path.exists(tmpncfile): os.remove(tmpncfile)

#---

# flush print buffer immediately
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

if __name__ == "__main__":
  #main(sys.argv[1:])
  main(sys.argv)

### END ###

