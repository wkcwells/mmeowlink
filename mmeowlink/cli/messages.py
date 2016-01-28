from decocare.helpers import messages
from mmeowlink.handlers.stick import Pump
from mmeowlink.link_builder import LinkBuilder
from mmeowlink.radio_config_builder import RadioConfigBuilder
from mmeowlink.vendors.subg_rfspy_radio_params import SubgRfspyRadioParams

class SendMsgApp (messages.SendMsgApp):
  """
  mmeowlink adapter to decocare's SendMsgApp
  """
  def customize_parser (self, parser):
    parser.add_argument('--radio_type', choices=['mmcommander', 'subg_rfspy'])
    SubgRfspyRadioParams.add_arguments(parser)

    parser = super(SendMsgApp, self).customize_parser(parser)
    return parser

  def prelude (self, args):
    radio_config = RadioConfigBuilder.build(args.radio_type, args)

    self.link = link = LinkBuilder().build(args.radio_type, args.port, radio_config)
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

  def postlude (self, args):
    # self.link.close( )
    return
