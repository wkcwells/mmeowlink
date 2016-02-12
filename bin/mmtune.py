#!/usr/bin/env python

import sys
import json
from mmeowlink.mmtune import MMTune
from mmeowlink.vendors.subg_rfspy_link import SubgRfspyLink

if __name__ == '__main__':
  locale = 'US'

  if len(sys.argv) < 3:
    print "Usage: mmtune.py /dev/ttyMFD1 pumpserial [radio_locale]"
    print "Radio locale defaults to 'US'. Set to 'WW' for other countries"
    sys.exit(-1)

  link = SubgRfspyLink(sys.argv[1])
  serial = sys.argv[2]

  if len(sys.argv) >= 4:
    locale = sys.argv[3]

  if locale not in ['US', 'WW']:
    print "Radio locale not supported - must be either 'WW' or 'US'"
    sys.exit(1)

  tuner = MMTune(link, serial, locale)
  output = tuner.run()
  print json.dumps(output, sort_keys=True,indent=4, separators=(',', ': '))
