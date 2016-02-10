#!/usr/bin/env python

import sys
import json
from mmeowlink.mmtune import MMTune
from mmeowlink.vendors.subg_rfspy_link import SubgRfspyLink

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print "Usage: mmtune.py /dev/ttyMFD1 pumpserial"
    sys.exit(-1)

  link = SubgRfspyLink(sys.argv[1])
  tuner = MMTune(link, sys.argv[2])
  output = tuner.run()
  print json.dumps(output, sort_keys=True,indent=4, separators=(',', ': '))  

