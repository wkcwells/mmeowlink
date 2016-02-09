#!/usr/bin/env python

import sys
import json
from decocare.lib import CRC8
from mmeowlink.exceptions import CommsException,InvalidPacketReceived

from mmeowlink.vendors.subg_rfspy_link import SubgRfspyLink

class MMTune:
  DEFAULT_FREQ = 916.630

  def __init__(self, path, pumpserial):
    self.link = SubgRfspyLink(path)
    self.pumpserial = pumpserial

  def run(self):
    self.link.update_register(SubgRfspyLink.REG_MDMCFG4, 0xd9)

    # Pump in free space
    self.link.set_base_freq(self.DEFAULT_FREQ)

    # Sometimes getting lower ber with 0x07 here (default is 0x03)
    self.link.update_register(SubgRfspyLink.REG_AGCCTRL2, 0x07)

    self.link.update_register(SubgRfspyLink.REG_AGCCTRL1, 0x40)

    # With rx bw > 101kzHZ, this should be 0xB6, otherwise 0x56
    self.link.update_register(SubgRfspyLink.REG_FREND1, 0x56)

    # default (0x91) seems to work best
    #self.link.update_register(SubgRfspyLink.REG_AGCCTRL0, 0x91)

    #print "waking..."
    self.wakeup()

    #print "scanning..."
    results = self.scan_over_freq(916.5, 916.9, 20)
    results_sorted = list(reversed(sorted(results, key=lambda x: x[1:])))
    set_freq = self.DEFAULT_FREQ
    used_default = True
    if results_sorted[0][1] > 0:
      used_default = False
      set_freq = float(results_sorted[0][0])
    self.link.set_base_freq(set_freq)
    output = {'scanDetails': results, 'setFreq': set_freq, 'usedDefault': used_default}
    print json.dumps(output, sort_keys=True,indent=4, separators=(',', ': '))

  def run_trial(self, var):
    sample_size = 5
    success_count = 0
    error_count = 0
    rssi_readings = []
    for i in xrange(sample_size):
      self.send_packet("a7" + self.pumpserial + "8d00") # Get Model
      try: 
        packet = self.get_packet(0.080)
        success_count += 1
        rssi_readings.append(packet["rssi"])
      except (CommsException,InvalidPacketReceived):
        error_count += 1
        rssi_readings.append(-99)
  
    avg_rssi = sum(rssi_readings)/len(rssi_readings)
    
    #print "%s, %d, rssi:%0.1f" % (var, error_count, avg_rssi)
    return [var, success_count, avg_rssi]


  def scan_over_freq(self, start_freq, end_freq, steps):
    step_size = (end_freq - start_freq) / steps
    cur_freq = start_freq
    results = []
    while cur_freq < end_freq:
      self.link.set_base_freq(cur_freq)
      results.append(self.run_trial("%0.3f" % cur_freq))
      cur_freq += step_size
    return results

  def send_packet(self, data, tx_count=1, msec_repeat_delay=0):
    buf = bytearray()
    buf.extend(data.decode('hex'))
    buf.extend([CRC8.compute(buf)])
    self.link.write(buf, tx_count, msec_repeat_delay)

  def get_packet(self, timeout=0):
    return self.link.get_packet(timeout)

  def wakeup(self):
    awake = False
    for i in xrange(3):
      self.send_packet("a7" + self.pumpserial + "8d00")
      try:
        packet = self.get_packet(0.08)
        #print "packet = " + str(packet)
      except CommsException: 
        packet = None
        #print "No response..."
        pass
      if packet:
        #print "Woke up pump: " + str(packet)
        awake = True
        break

    if awake != True:
      # Send 200 wake-up packets
      self.send_packet("a7" + self.pumpserial + "5d00", 200)
      try:
        wake_ack = self.get_packet(9) # wait 9 s for response
      except (CommsException, InvalidPacketReceived):
        wake_ack = None
        #print "No response..."
        pass

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print "Usage: mmtune.py /dev/ttyMFD1 pumpserial"
    sys.exit(-1)

  tuner = MMTune(sys.argv[1], sys.argv[2])
  tuner.run()

