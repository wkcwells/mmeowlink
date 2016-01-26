
# Based on decoding-carelink/decocare/link.py

import array
import binascii
import logging
import time

from decocare.lib import hexdump, CRC8

from .. fourbysix import FourBySix
from .. exceptions import InvalidPacketReceived, CommsException

from serial_interface import SerialInterface
from serial_rf_spy import SerialRfSpy
from subg_rfspy_radio_config import SubgRfspyRadioConfig

io  = logging.getLogger( )
log = io.getChild(__name__)

class SubgRfspyLink(SerialInterface):
  TIMEOUT = 1
  REPETITION_DELAY = 0
  MAX_REPETITION_BATCHSIZE = 250

  def __init__(self, device, radio_config=None):
    self.timeout = 1
    self.device = device
    self.speed = 19200
    self.radio_config = radio_config

    self.open()
    self.init_radio()

  def check_setup(self):
    self.serial_rf_spy = SerialRfSpy(self.serial)

    self.serial_rf_spy.sync()

    # Check it's a SerialRfSpy device by retrieving the firmware version
    self.serial_rf_spy.send_command(self.serial_rf_spy.CMD_GET_VERSION, timeout=1)
    version = self.serial_rf_spy.get_response(timeout=1)

    log.debug( 'serial_rf_spy Firmare version: %s' % version)

  def init_radio(self):
    for register in SubgRfspyRadioConfig.available_registers():
      id = SubgRfspyRadioConfig.REGISTERS[register]["reg"]
      value = self.radio_config.get_register(register)

      print("Setting radio register %s (0x%x) to %x" % (register, id, value))
      resp = self.serial_rf_spy.do_command(SerialRfSpy.CMD_UPDATE_REGISTER, chr(id) + chr(value))

      if ord(resp) != 1:
        raise NotImplementedError("Cannot set register %s (0x%x) - received response of %i" % (register, id, ord(resp)))

  def write( self, string, repetitions=1, repetition_delay=0, timeout=None ):
    rf_spy = self.serial_rf_spy

    remaining_messages = repetitions
    while remaining_messages > 0:
      if remaining_messages < self.MAX_REPETITION_BATCHSIZE:
        transmissions = remaining_messages
      else:
        transmissions = self.MAX_REPETITION_BATCHSIZE
      remaining_messages = remaining_messages - transmissions

      crc = CRC8.compute(string)

      channel = self.radio_config.tx_channel
      print "TXing on channel %s" % channel

      message = chr(channel) + chr(transmissions - 1) + chr(repetition_delay) + FourBySix.encode(string)

      rf_spy.do_command(rf_spy.CMD_SEND_PACKET, message, timeout=timeout)

  def read( self, timeout=None ):
    rf_spy = self.serial_rf_spy

    if timeout is None:
      timeout = self.timeout

    timeout_ms = timeout * 1000
    timeout_ms_high = int(timeout_ms / 256)
    timeout_ms_low = int(timeout_ms - (timeout_ms_high * 256))

    channel = self.radio_config.rx_channel
    print "RXing on channel %s" % channel

    resp = rf_spy.do_command(SerialRfSpy.CMD_GET_PACKET, chr(channel) + chr(timeout_ms_high) + chr(timeout_ms_low), timeout=timeout + 1)
    if not resp:
      raise CommsException("Did not get a response")

    decoded = FourBySix.decode(resp[2:])

    return decoded
