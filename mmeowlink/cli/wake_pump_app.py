from base_mmeowlink_app import BaseMMeowlinkApp
from mmeowlink.link_builder import LinkBuilder

class WakePumpApp(BaseMMeowlinkApp):
  """
  Wake up the pump
  """
  def customize_parser(self, parser):
    parser = super(self.__class__, self).configure_radio_params(parser)
    return parser

  def prelude(self, args):
    args.init = True
    if args.frequency is not None:
      # Stolen from base_mmeowlink_app.  And is totally repetitious becasue we need to set the freq before letting the base app do its thing...
      port = args.port
      builder = LinkBuilder()
      if port == 'scan':
        port = builder.scan()
      self.link = LinkBuilder().build(args.radio_type, port)
      # Stolen from KW pyloop.py
      print("Attempting to set stick frequency to: " + str(args.frequency))
      try:
        self.link.set_base_freq(float(args.frequency))
        self.link.close()
      except Exception as e:
        print("Failed to set stick frequency: " + str(e))
        exit(-1)
    try:
      super(WakePumpApp, self).prelude(args)
    except Exception as e:
      print("Unexpected exception raised waking up pump: " + str(e))

  def main(self, args):
    try:
      print("Pump model is: " + str(self.pump.model))
    except AttributeError:
      print("FAILED TO WAKE PUMP")
