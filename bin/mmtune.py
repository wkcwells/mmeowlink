#!/usr/bin/env python

import sys
from decocare.lib import CRC8
from mmeowlink.exceptions import CommsException

from mmeowlink.vendors.subg_rfspy_link import SubgRfspyLink

class MMTune:
  def __init__(self, path, pumpserial):
    self.link = SubgRfspyLink(path)
    self.pumpserial = pumpserial

  def run(self):
    print "scanning..."
    self.link.update_register(SubgRfspyLink.REG_MDMCFG4, 0xd9)

    # Pump in free space
    self.link.set_base_freq(916.630)

    # Sometimes getting lower ber with 0x07 here (default is 0x03)
    self.link.update_register(SubgRfspyLink.REG_AGCCTRL2, 0x07)

    self.link.update_register(SubgRfspyLink.REG_AGCCTRL1, 0x40)

    # With rx bw > 101kzHZ, this should be 0xB6, otherwise 0x56
    self.link.update_register(SubgRfspyLink.REG_FREND1, 0x56)

    # default (0x91) seems to work best
    #self.link.update_register(SubgRfspyLink.REG_AGCCTRL0, 0x91)

    self.wakeup

    results = scan_over_freq(916.5, 916.9, 20)
    if results[0][1] > 0:
      print "Setting to best freq of #{results[0][0]}"
      best = results[0][0].to_f
      self.link.set_base_freq(best)
      continuous_trial
    else:
      self.link.set_base_freq(916.630)


  def send_packet(self, data, tx_count=1, msec_repeat_delay=0):
    buf = bytearray()
    buf.extend(data.decode('hex'))
    buf.extend([CRC8.compute(buf)])
    self.link.write(buf, tx_count, msec_repeat_delay)

  def get_packet(self, timeout=0):
    return self.link.read(timeout)

  def wakeup(self):
    awake = False
    for i in xrange(3):
      self.send_packet("a7" + self.pumpserial + "8d00")
      try:
        packet = self.get_packet(0.08)
      except CommsException: 
        packet = None
        print "No response..."
        pass
      if packet:
        print "Woke up pump: " + packet
        awake = True
        break

    if awake != True:
      # Send 200 wake-up packets
      self.send_packet("a7" + self.pumpserial + "5d00", 200)
      try:
        wake_ack = self.get_packet(9) # wait 9 s for response
      except CommsException:
        wake_ack = None
        print "No response..."
        pass

      if wake_ack:
        print "wake ack: " + wake_ack
      else:
        print "Pump not responding"


if __name__ == '__main__':
  if len(sys.argv) < 3:
    print "Usage: mmtune.py /dev/ttyMFD1 pumpserial"
    sys.exit(-1)

  tuner = MMTune(sys.argv[1], sys.argv[2])
  tuner.run()

