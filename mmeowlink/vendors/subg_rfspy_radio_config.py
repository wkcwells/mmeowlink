# Radio Parameters for subg_rfspy parameters
import sys
import copy

class SubgRfspyRadioConfig(object):
  # This list needs to exactly match the register numbers in the cmd_update_register
  # procedure in the subg_rfspy commands.c file, so that the correct values are
  # set in the radio
  REGISTERS = {
    "sync1":      { "reg": 0x00, "default": 0xFF },
    "sync0":      { "reg": 0x01, "default": 0x00 },
    "pktlen":     { "reg": 0x02, "default": 0xFF },
    "pktctrl1":   { "reg": 0x03, "default": 0x00 },
    "pktctrl0":   { "reg": 0x04, "default": 0x00 },
    "addr":       { "reg": 0x05, "default": 0x00 },
    # channr is set differently for tx and rx, so we don't allow you to set it
    # via the registers as it'd lead to unnecessary confusion
    # "channr":     { "reg": 0x06, "default": 0x00 },
    "fsctrl1":    { "reg": 0x07, "default": 0x06 },
    "fsctrl0":    { "reg": 0x08, "default": 0x00 },
    "freq2":      { "reg": 0x09, "default": 0x24 },
    "freq1":      { "reg": 0x0A, "default": 0x2E },
    "freq0":      { "reg": 0x0B, "default": 0x38 },
    "mdmcfg4":    { "reg": 0x0C, "default": 0x99 },
    "mdmcfg3":    { "reg": 0x0D, "default": 0x66 },
    "mdmcfg2":    { "reg": 0x0E, "default": 0x33 },
    "mdmcfg1":    { "reg": 0x0F, "default": 0x61 },
    "mdmcfg0":    { "reg": 0x10, "default": 0x7E },
    "deviatn":    { "reg": 0x11, "default": 0x15 },
    "mcsm2":      { "reg": 0x12, "default": 0x07 },
    "mcsm1":      { "reg": 0x13, "default": 0x30 },
    "mcsm0":      { "reg": 0x14, "default": 0x18 },
    "foccfg":     { "reg": 0x15, "default": 0x17 },
    # We don't ever change bscfg, and I don't know what it
    # is at reset, so I'm leaving it as an error for now
    # "bscfg":     { "reg": 0x16, "default": -1 },
    "agcctrl2":   { "reg": 0x17, "default": 0x07 },
    "agcctrl1":   { "reg": 0x18, "default": 0x00 },
    "agcctrl0":   { "reg": 0x19, "default": 0x91 },
    "frend1":     { "reg": 0x1A, "default": 0xB6 },
    "frend0":     { "reg": 0x1B, "default": 0x11 },
    "fscal3":     { "reg": 0x1C, "default": 0xE9 },
    "fscal2":     { "reg": 0x1D, "default": 0x2A },
    "fscal1":     { "reg": 0x1E, "default": 0x00 },
    "fscal0":     { "reg": 0x1F, "default": 0x1F },
    # Not currently settable:
    #   test1
    #   test0
    #   pa_table0
    #   pa_table1
    #   agcctrl2
    #   agcctrl1
    #   agcctrl0
  }

  @classmethod
  def available_registers(cls):
    return sorted(cls.REGISTERS.keys())

  def __init__(self):
    self.tx_channel = 0
    self.rx_channel = 2

    self.registers = {}
    for register in self.__class__.available_registers():
      self.registers[register] = copy.copy(self.__class__.REGISTERS[register]["default"])

  def locale_usa(self):
    self.registers['freq2'] = 0x26; # 916.541MHz is midpoint between freq of pump in free space,
    self.registers['freq1'] = 0x30; # and pump held close to the body.
    self.registers['freq0'] = 0x70;
    self.registers['channr'] = 0x02; # channel number
    # self.pa_table1 = 0xC0; # pa power setting 10 dBm

  def locale_worldwide(self):
    self.registers['freq2'] = 0x24;
    self.registers['freq1'] = 0x2E;
    self.registers['freq0'] = 0x38;
    self.registers['channr'] = 0x00;
    # self.pa_table1 = 0x50; # Max configurable power output at this frequency is 0x50

  def set_register(self, register, value):
    if register not in self.registers:
      raise NotImplementedError("Supplied radio parameter register %s is not supported" % register)

    print("Radio config: %s=0x%x" % (register, value))
    self.registers[register] = value

  def get_register(self, register):
    if register not in self.registers:
      raise NotImplementedError("Supplied radio parameter register %s is not supported" % register)
    val = self.registers[register]
    print("Getting register %s -> 0x%x" % (register, val))
    return val
