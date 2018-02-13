#!/usr/local/bin/python2.7

import urllib, urllib2
import sys
import json
from docopt import docopt
from ntlm import HTTPNtlmAuthHandler

# Get element from JSON path
def xpath_get(mydict, path):
  elem = mydict
  try:
    for x in path.strip("/").split("/"):
      try:
        x = int(x)
        elem = elem[x]
      except ValueError:
        elem = elem.get(x)
  except:
    pass

  return elem

def main():

  usage="""
  
Usage:
  zbxjson -u <url> -p <path> [-U <username>] [-P <password>] [-m <GET|POST>] [-d <data>] [-a <basic|ntlm>]
  
Options:
  -u, --url <url>                       The URL to the web service endpoint
  -p, --path <path>                     The path to the JSON element to get. Expects /element1, /array1 or /array1/2/element3...
  -U, --username <username>             The username if authentication is required
  -P, --password <password>             The password if authentication is required
  -m, --method <GET|POST>               The HTTP method to use (GET|POST). [default: get]
  -d, --data <data>                     The POST data to send, if required. Expects --data "key1=value1,key2=value2,..."
  -a, --authentication <basic|ntlm>     The authentication method to use (basic, ntml) [default: ntlm]

"""
  args = docopt(usage, version="0.1")
 
  # Set authentication if required
  if args["--authentication"]:
    authinfo = urllib2.HTTPPasswordMgrWithDefaultRealm()
    authinfo.add_password(None, args["--url"], args["--username"], args["--password"])
    
    if args["--authentication"] == "basic":
      auth = urllib2.HTTPBasicAuthHandler(authinfo)   
    elif args["--authentication"] == "ntlm":
      auth = HTTPNtlmAuthHandler.HTTPNtlmAuthHandler(authinfo)
      
    opener = urllib2.build_opener(auth)
    urllib2.install_opener(opener)
  
  # Handle POST data
  if args["--data"]:
    data = urllib.urlencode(dict([arg.split('=') for arg in args["--data"].split(',')]))
  else:
    data = "None"
  
  # Create HTTP request
  req = urllib2.Request(args["--url"], data = data)
  req.add_header('User-Agent', 'Zabbix Monitoring')
  req.add_header('Content-Type', 'application/json' )
  
  # Handle the HTTP method
  if args["--method"]:
    method = args["--method"]  
    req.get_method = lambda: method
  
  try:
    connection = opener.open(req)
  except urllib2.HTTPError,e:
    print e
    sys.exit(1)
  except urllib2.URLError, e:
    print e
    sys.exit(1)

  # Exit if the HTTP response code != 200
  if connection.code != 200:
    print "HTTP response code is %d" % connection.code
    sys.exit(1)

  # Load the response as a JSON object   
  try:
    obj = json.load(connection)
  except:
    print "Cannot extract the JSON response"
    sys.exit(1)

  # Get the element referenced by the specified path
  element = xpath_get(obj, args["--path"])
  
  if isinstance(element, unicode) or isinstance(element, bool): # the element is a unicode string
    print element
  elif isinstance(element, list): # the element is an array
    output = []
    # format it as an LLD JSON object
    for index, item in enumerate(element, start=0):
      props = { "{#JSON%s}" % k.upper(): v  for k, v in item.items() }
      props["{#JSONPATH}"] = "%s/%d" % (args["--path"], index)
      output.append(dict(props))
    print json.dumps({ 'data': output}, indent=2)
  elif isinstance(element, dict): # the element is dictionary
    # format it as an LLD JSON object  
    props = { "{#JSON%s}" % k.upper(): v  for k, v in element.items() }
    props["{#JSONPATH}"] = args["--path"]
    print json.dumps({ 'data': props}, indent=2)

  sys.exit(0)

if __name__ == '__main__':
    main()

