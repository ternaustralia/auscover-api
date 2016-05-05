from geoserver.wps import process
#from com.vividsolutions.jts.geom import Geometry
import subprocess
import sys

#####

@process(
  title='mntest',
  description='A WPS test',
  inputs={
    'arg1': (str, 'First arg'),
    'arg2': (str,'Second arg')
  },
  outputs={
    'result': (str, 'Output from mntest')
  }
)
def run(arg1, arg2):
  #out = 'Arg1: %s  and Arg2: %s\n\n' % (arg1, arg2)
  #cmdout = subprocess.check_output(['cat', '/etc/motd'])
  #DIR = 'webapps/geoserver-dev/data/scripts/wps/'
  DIR = '/var/rs/auscover-api/'
  cmd = ['cat', DIR + 'soilm-ts.csv']
  #cmd = ['ls', '-l', 'webapps/geoserver-dev/data/scripts/wps']
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  #out = p.communicate()[0].split(' ')
  out = p.communicate()[0]
  #out = out.replace(' ', '\n')
  #out = cmdout
  #out = 'blah\nblah\nblah'
  #print out
  #out += cmdout
  #out += ','.join(sys.path)
  #out += sys.version
  return out

