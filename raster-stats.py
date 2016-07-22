#!/usr/bin/env python
#
# extract mean for a polygon over a raster, or find value at a point in raster
# uses a pip package: rasterstats (see http://pythonhosted.org/rasterstats/)
#
# can also run from the commandline eg.
#  fio cat poly.shp | rio zonalstats -r FractCover.V3_0_1.201601.global.005.TotCov_tiled.tiff, OR
#  rio zonalstats poly.geojson -r FractCover.V3_0_1.201601.global.005.TotCov_tiled.tiff
#
###

from rasterstats import zonal_stats, point_query
import rasterio
from netCDF4 import Dataset
from affine import Affine
from glob import glob
import sys, re, os
from netcdftime import utime
from datetime import datetime

###
# Inputs, need a point or polygon, and a raster, or generate a list of rasters to loop through
#fg = '/rdsi/public/data/spatial_other/csiro/smips/SMIPS*.nc'
#fg = '/rdsi/tmp/fc/TotCov/20??/monthly/FractCover.V3_0_1.20*_tiled.tiff'
fg = '/rdsi/tmp/fc/20??/FractCover.V3_0_1.20????.global.005.TotCov.tiff'
gtIn = 'FractCover.V3_0_1.201601.global.005.TotCov_tiled.tiff'
#ncIn = 'SMIPSv05_volSM_forecast_20160629.nc'
ncIn = '/rdsi/public/data/spatial_other/csiro/amsr2/amsr2-soilm-global-monthly.nc'
#fg = ncIn
#polyIn = 'poly2.json'
polyIn = 'ibra7_monaro.geojson'
pt = 'POINT (149.0 -35.0)'

###
# Functions

def extractDate(s):
  # Extract a date from a string - making lots of assumptions
  # start by testing for year.month
  d = re.findall('\.20\d{2}\.\d{2}\.', s)
  if len(d) > 0:
    dt = datetime.strptime(d[0], '.%Y.%m.')
    return dt.strftime('%Y-%m-%d')
  d = re.findall('\.20\d{4}\.', s)
  if len(d) > 0:
    dt = datetime.strptime(d[0], '.%Y%m.')
    return dt.strftime('%Y-%m-%d')
  # then for yearmonthday
  d = re.findall('\.20\d{6}\.', s)
  if len(d) > 0:
    dt = datetime.strptime(d[0], '.%Y%m%d.')
    return dt.strftime('%Y-%m-%d')
  d = re.findall('\_20\d{6}\.', s)
  if len(d) > 0:
    dt = datetime.strptime(d[0], '_%Y%m%d.')
    return dt.strftime('%Y-%m-%d')
  # other formats
  d = re.findall('20\d{2}-\d{2}-\d{2}', s)
  if len(d) > 0:
    dt = datetime.strptime(d[0], '%Y-%m-%d')
    return dt.strftime('%Y-%m-%d')
  # if it gets to here then can't work out date
  print 'Can\'t find a date in %s!' % s
  sys.exit()

def polyGtiff(poly, gt, b):
  stats = (extractDate(gt),)
  bl = b.split(',')
  for i in range(len(bl)):
    if bl[i].isdigit():
      bn = int(bl[i])
    else:
      #bn = bl[i]
      bn = i + 1
    stats += (zonal_stats(poly, gt, band_num=bn, stats=['median'])[0]['median'], )
    #stats += (zonal_stats(poly, gt, band_num=bn, stats='median'), )
  return [stats]

def pointGtiff(pt, gt, b):
  stats = (extractDate(gt),)
  bl = b.split(',')
  for i in range(len(bl)):
    if bl[i].isdigit():
      bn = int(bl[i])
    else:
      #bn = bl[i]
      bn = i + 1
    stats += (point_query(pt, gt, band=bn)[0], )
  #stats = (extractDate(gt), point_query(pt, gt, band=b)[0])
  return [stats]

def polyNetcdf(poly, nc, v):
  ncf = Dataset(nc)
  # affine transform(px width, row rotation, UL x-coord, col rotation, px height, UL y-coord)
  affine = Affine(0.1, 0.0, -180.0, 0.0, -0.1, 90.0)
  ndims = ncf[v].ndim
  if ndims == 2:
    array = ncf[v][:,:]
    ncf.close()
    stats = (extractDate(nc), zonal_stats(poly, array, affine=affine, nodata=-9999.0, stats=['median'])[0]['median'])
    return [stats]
  elif ndims == 3:      # assume it's time/lat/lon
    #print 'N-dims:', ndims
    cdftime = utime(ncf['time'].units)
    stats = []
    for i in range(ncf[v].shape[0]):
      array = ncf[v][i,:,:]
      dt = cdftime.num2date(ncf['time'][i]).strftime('%Y-%m-%d')
      stats.append((dt, zonal_stats(poly, array, affine=affine, nodata=-9999.0, stats=['median'])[0]['median']))
    ncf.close()
    #print stats
    return stats
  else:
    print 'Don\'t know what to do with %s dimensions!' % ndims
    sys.exit()

def pointNetcdf(pt, nc, v):
  ncf = Dataset(nc)
  # affine transform(px width, row rotation, UL x-coord, col rotation, px height, UL y-coord)
  affine = Affine(0.1, 0.0, -180.0, 0.0, -0.1, 90.0)
  ndims = ncf[v].ndim
  if ndims == 2:
    array = ncf[v][:,:]
    ncf.close()
    stats = (extractDate(nc), point_query(pt, array, affine=affine, nodata=-9999.0)[0])
    return [stats]
  elif ndims == 3:	# assume it's time/lat/lon
    #print 'N-dims:', ndims
    cdftime = utime(ncf['time'].units)
    stats = []
    for i in range(ncf[v].shape[0]):
      array = ncf[v][i,:,:]
      dt = cdftime.num2date(ncf['time'][i]).strftime('%Y-%m-%d')
      stats.append((dt, point_query(pt, array, affine=affine, nodata=-9999.0)[0]))
    ncf.close()
    #print stats
    return stats
  else:
    print 'Don\'t know what to do with %s dimensions!' % ndims
    sys.exit()

def pointOrPoly(pp):
  #if p[0] == '{':
  if os.path.exists(pp):
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
      print 'Unknown data type!'
      sys.exit()

def getInputs():
  # get commandline inputs
  fileGlob = p = v = ''
  b = '1'
  if len(sys.argv) < 2:
    print 'Usage:  raster-stats <file-glob> <point-or-poly> [<variable(s)-or-bandnum(s)>]'
    print ''
    sys.exit()
  elif len(sys.argv) >= 2:
    fileGlob = sys.argv[1]
    if len(sys.argv) >= 3:
      p = sys.argv[2]
    if len(sys.argv) >= 4:
      v = sys.argv[3]
      b = v
      #if v[0].isdigit():
      #  b = v
      #else:
      #  b = '1'
    return fileGlob, p, v, b

def getFiles(fg):
  # get list of files to loop over
  fileList = sorted(glob(fg))
  #fileList = [ncIn]
  if 'nc' in (fileList[-1].split('.')[-1]):
    fmt = 'netcdf'
  elif 'tif' in (fileList[-1].split('.')[-1]):
    fmt = 'gtiff'
  else:
    print 'getFiles: Can\'t work out file format!'
    sys.exit()
  return fileList, fmt

def timeSeries(fl, fmt, p, porp, v='', b='1'):
  # loop through files and produce time series
  tsStats = []
  for f in fl:
    if fmt == 'gtiff':
      if porp == 'poly':
        #tsStats.append(polyGtiff(p, f))
        tsStats += polyGtiff(p, f, b)
      elif porp == 'point':
        #tsStats.append(pointGtiff(p, f))
        tsStats += pointGtiff(p, f, b)
    elif fmt == 'netcdf':
      if porp == 'poly':
        #tsStats.append(polyNetcdf(p, f, v))
        tsStats += polyNetcdf(p, f, v)
      elif porp == 'point':
        #tsStats.append(pointNetcdf(p, f, v))
        tsStats += pointNetcdf(p, f, v)

  # output
  head = 'Datetime,'
  if v != '': head += v
  else: head += 'Band:' + b
  # special case for fract cover
  fc = False
  if re.search('fractcover', fl[0], re.I):
    fc = True
    head += ',Total_Cover'
  print head
  for dv in tsStats:
    #print '%s,%s' % dv
    line = dv[0]
    # special case for fract cover
    if fc and len(dv) == 4:
      if dv[3] is None:
        dv = dv[:-1] + (0.0,)   # because it's a tuple
      for i in range(len(dv) -1):
        line += ',' + str(dv[i+1])
      line += ',' + str(dv[2] + dv[3])
    else:
      for i in range(len(dv) -1):
        line += ',' + str(dv[i+1])
    print line

#
## 
### MAIN ###

# get commandline inputs
fileGlob, p, v, b = getInputs()
#fileGlob = fg
#p = pt
#p = polyIn
#v = 'soilm'
#v = ''
#b = '1,2,3'
#b = '1'

#print fileGlob, p, v, b
#sys.exit()

# get list of files to loop over
fileList, fmt = getFiles(fileGlob)
#fileList = [ncIn]
#fileList = [gtIn]
#fmt = 'netcdf'
#fmt = 'gtiff'

# determine if we are dealing with a point or polygon
porp = pointOrPoly(p)

# get the time series
timeSeries(fileList, fmt, p, porp, v, b)

### END ###
##
#
