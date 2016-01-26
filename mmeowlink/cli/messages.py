from decocare.helpers import messages
from mmeowlink.handlers.stick import Pump
from mmeowlink.link_builder import LinkBuilder
from mmeowlink.vendors.subg_rfspy_radio_config import SubgRfspyRadioConfig

class SendMsgApp (messages.SendMsgApp):
  """
  mmeowlink adapter to decocare's SendMsgApp
  """
  def customize_parser (self, parser):
    parser.add_argument('--radio_type', choices=['mmcommander', 'subg_rfspy'])
    parser.add_argument('--subg_rfspy_radio_locale', default='usa', choices=['usa', 'worldwide'])
    parser.add_argument('--subg_rfspy_radio_rx_channel', choices=['0', '1', '2'])
    parser.add_argument('--subg_rfspy_radio_tx_channel', choices=['0', '1', '2'])

    for register in SubgRfspyRadioConfig.available_registers():
      name = '--subg_rfspy_%s' % register
      parser.add_argument(name)

    parser = super(SendMsgApp, self).customize_parser(parser)
    return parser

  def prelude (self, args):
    radio_config = self.build_radio_config(args)

    self.link = link = LinkBuilder().build(args.radio_type, args.port, radio_config=radio_config)
    link.open()
    # get link
    # drain rx buffer
    self.pump = Pump(self.link, args.serial)
    if args.no_rf_prelude:
      return
    if not args.autoinit:
      if args.init:
        self.pump.power_control(minutes=args.session_life)
    else:
      self.autoinit(args)
    self.sniff_model( )

  def build_radio_config(self, args):
    radio_config = None

    if args.radio_type == 'subg_rfspy':
      radio_config = SubgRfspyRadioConfig()
      # The radio locale is set first, and then individual items are set as
      # overrides, if appropriate
      if args.subg_rfspy_radio_locale:
        method_name = "locale_%s" % args.subg_rfspy_radio_locale
        getattr(radio_config, method_name)()

      # Channels are handled separately from other parameters, since they are
      # used at every send and every receive, rather than necessarily in the
      # base radio settings. However, there is an overall channel
      if args.subg_rfspy_radio_tx_channel:
        radio_config.tx_channel = int(args.subg_rfspy_radio_tx_channel)

      if args.subg_rfspy_radio_rx_channel:
        radio_config.rx_channel = int(args.subg_rfspy_radio_rx_channel)

      # Now try and set any additional radio parameters dynamically, based
      # on the list of configured registers
      for register in SubgRfspyRadioConfig.available_registers():
        arg_name = "subg_rfspy_%s" % register

        val = getattr(args, arg_name)
        if val:
          radio_config.set_register(register, int(val, 16))

    return radio_config

  def postlude (self, args):
    # self.link.close( )
    return
