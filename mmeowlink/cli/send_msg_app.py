from base_mmeowlink_app import BaseMMeowlinkApp

class SendMsgApp(BaseMMeowlinkApp):
  """
  mmeowlink adapter to decocare's SendMsgApp. All actual implementation details
  are handled in MMeowlinkApp and messages in decocare.helpers
  """
  def customize_parser(self, parser):
    parser = super(self.__class__, self).configure_radio_params(parser)
    parser = super(self.__class__, self).customize_parser(parser)

    return parser
