
from decocare import session, lib, commands
from .. packets.rf import Packet
from .. exceptions import InvalidPacketReceived, CommsException

import sys
import logging
import time
import traceback

import logging

logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
io  = logging.getLogger( )
log = io.getChild(__name__)

class Sender (object):
  STANDARD_RETRY_COUNT = 3
  RETRY_BACKOFF = 1

  sent_params = False
  def __init__ (self, link):
    self.link = link
    self.frames = [ ]
    self.ack_for_more_data = False
    self.received_ack = False

  def send_params (self):
    command = self.command
    params = self.command.params
    payload = bytearray([len(params)]) + bytearray(params)
    missing = [ ]
    missing = bytearray([0x00]) * (64 - len(params))
    payload = payload + missing
    pkt = Packet.fromCommand(command, payload=payload, serial=command.serial)
    pkt = pkt.update(payload)
    buf = pkt.assemble( )
    self.sent_params = True
    try:
      buf = self.link.write_and_read(buf)
      resp = Packet.fromBuffer(buf)
      self.respond(resp)
    except AttributeError:
      self.link.write(buf)

  def ack (self, listen=False):
    null = bytearray([0x00])
    pkt = Packet.fromCommand(self.command, payload=null, serial=self.command.serial)
    pkt = pkt._replace(payload=null, op=0x06)
    buf = pkt.assemble( )
    if listen:
      buf = self.link.write_and_read(buf, timeout=0.1)
      return Packet.fromBuffer(buf)
    else:
      self.link.write(buf)

  def unframe (self, resp):
    if self.command.bytesPerRecord * self.command.maxRecords > 64:
      self.ack_for_more_data = True
      num, payload = resp.payload[0], resp.payload[1:]
      self.frames.append((num, resp.payload))
    else:
      self.ack_for_more_data = False
      payload = resp.payload[1:]

    self.command.respond(payload)


  def done (self):
    needs_params = self.command.params and len(self.command.params) > 0 or False
    if needs_params and not self.sent_params:
      return False
    return self.command.done( )

  def respond (self, resp):
    if resp.valid and resp.serial == self.command.serial:
      if resp.op == 0x06 and self.sent_params:
        self.command.respond(bytearray(64))
      elif resp.op == self.command.code:
        self.unframe(resp)

  def wait_for_ack (self, timeout=.500):
    link = self.link

    while not self.done( ):
      buf = link.read( timeout=timeout )
      resp = Packet.fromBuffer(buf)
      if self.responds_to(resp):
        if resp.op == 0x06:
          return

  def responds_to (self, resp):
    return resp.valid and resp.serial == self.command.serial

  def wait_response (self):
    link = self.link
    buf = link.read( )
    resp = Packet.fromBuffer(buf)
    if self.responds_to(resp):
      return resp

  def prelude (self, timeout=None):
    link = self.link
    command = self.command
    log.debug("*** Sending prelude for command %d" % command.code)

    payload = bytearray([0])
    self.pkt = Packet.fromCommand(command, payload=payload, serial=command.serial)
    self.pkt = self.pkt.update(payload)
    buf = self.pkt.assemble( )
    try:
      buf = self.link.write_and_read(buf, timeout=timeout)
      if len(buf) == 0:
        log.error("Prelude: zero length response received")
        raise (CommsException("Prelude: zero length response received"))    # Kind of a hack for now
      resp = Packet.fromBuffer(buf)
      if self.responds_to(resp):
        if resp.op == 0x06:
          self.received_ack = True
        else:
          self.respond(resp)
    except AttributeError as e:
      log.error("AttributeError exception in mmeowlink.stick.prelude - %s" % str(e))
      self.link.write(buf)      # Why do this? Kinda strange?
    except CommsException as e:
      log.error("Comms Exception in mmeowlink.stick.prelude - %s" % str(e))
      raise (CommsException("Comms Exception in mmeowlink.stick.prelude - %s" % str(e)))  # Kind of a hack for now
    except InvalidPacketReceived as e:
      log.error("Invalid Packet Received in mmeowlink.stick.prelude - %s" % str(e))
      raise (InvalidPacketReceived("Invalid pump packet received in mmeowlink.stick.prelude - %s" % str(e)))
    except Exception as e:
      log.error("Unexpected Exception in mmeowlink.stick.prelude - %s (%s)" % (str(e), type(e)))
      raise (Exception("Unexpected Exception in mmeowlink.stick.prelude - %s (%s)" % (str(e), type(e))))      # Kind of a hack for now

  def upload (self):
    params = self.command.params
    log.debug("len(params)  == %d" % len(params))

    should_send = len(params) > 0
    if should_send:
      if not self.received_ack:
        self.wait_for_ack( )
      self.send_params( )

  def restart_command( self ):
    # This is a bit of a hack; would be nice if decocare explicitly supported a command reset
    self.command.data = bytearray()
    self.command.responded = False

  def __call__ (self, command, retries=None):
    self.command = command
    if retries is None:
      retries=self.STANDARD_RETRY_COUNT
    for retry_count in range(retries):
      try:
        self.prelude()
        self.upload()

        while not self.done( ):
          if self.ack_for_more_data:
            try:
              resp = self.ack(listen=True)
            except AttributeError:
              self.ack(listen=False)
              resp = self.wait_response( )
          else:
            resp = self.wait_response( )
          if resp:
            self.respond(resp)

        return command
      # We are doing very similar error processing in several places - combine...
      except InvalidPacketReceived as e:
        log.error("Invalid Packet Received - '%s' - retrying: %s of %s" % (e, retry_count + 1, retries))
        traceback.print_exc()
        if (retry_count >= retries - 1):
          raise InvalidPacketReceived("*** Invalid pump packet received: " + str(e))  # Not available until Python 3: 'from e'    # Needs testing
        else:
          self.restart_command()
          time.sleep(self.RETRY_BACKOFF * retry_count)
          continue
      except CommsException as e:
        log.error("Timed out or other comms error - %s - retrying: %s of %s" % (e, retry_count + 1, retries))
        traceback.print_exc()
        if (retry_count >= retries - 1):
          raise CommsException("*** Pump comm error: " + str(e))  # from e                        # Needs testing - pyloop has some special processing for this exception
          #  Note this avoids the final timeout wait as a beneficial side effect
          #  Also note: this only captures the final error, not all the attempts...
        else:
          self.restart_command()
          time.sleep(self.RETRY_BACKOFF * retry_count)
          continue
      log.error("SHOULD NEVER GET HERE")    # Do we need a generic exception catch??

# Used to send a command repeatedly - e.g. to wakeup pump
# KW TODO: key question is whether you have to be sending continuously for the pump to catch it and wakeup??
class Repeater (Sender):


  def __call__ (self, command, repetitions=None, ack_wait_seconds=None):
    self.command = command

    start = time.time()
    pkt = Packet.fromCommand(self.command, serial=self.command.serial)
    buf = pkt.assemble( )
    log.warning('Sending repeated message %s, %d times, at time: %s' % (str(buf).encode('hex'), repetitions, time.time()))

    self.link.write(buf, repetitions=repetitions)

    # The radio takes a while to send all the packets, so wait for a bit before
    # trying to talk to the radio, otherwise we can interrupt it.
    #
    # This multiplication factor is based on
    # testing, which shows that it takes 8.04 seconds to send 500 packets
    # (8.04/500 =~ 0.016 packets per second).
    # We don't want to miss the reply, so take off a bit:
    log.warning('Sleeping at time: %f' % (time.time() - start))
    time.sleep((repetitions * 0.016) - 2.2)

    # Sometimes the first packet received will be mangled by the simultaneous
    # transmission of a CGMS and the pump. We thus retry on invalid packets
    # being received. Note how ever that we do *not* retry on timeouts, since
    # our wait period is typically very long here, which would lead to long
    # waits with no activity. It's better to fail and retry externally
    log.warning('First ack wait at time: %f' % (time.time() - start))
    while (time.time() <= start + ack_wait_seconds):
      try:
        self.wait_for_ack()
        log.error("Ack received at %f" % (time.time() - start))
        return True
      except CommsException as e:
        log.error("Repeater Comm exception waiting for response - %s - retrying at %f" % (str(e), time.time() - start))
      except InvalidPacketReceived as e:
        log.error("Repeater invalid packet exception waiting for response - %s - retrying at %f" % (str(e), time.time() - start))
      except IOError as e:
        log.error("Repeater IOError exception waiting for response - %s - retrying at %f" % (str(e), time.time() - start))

    return False

class Pump (session.Pump):
  STANDARD_RETRY_COUNT = 3
  MAX_SESSION_DURATION = 5      # Time in minutes before trying the pump wakeup sequence again

  pump = None   # Attempt to cache the pump object

  def __init__ (self, link, serial):
    self.link = link
    self.serial = serial
    self.last_command_time = 0     # Time of the last command in seconds

  def set_last_command_time(self, time):
    self.last_command_time = time

  def get_model(self):    # Duplicates code elsewhere - see session.py in decocare
    self.command = commands.ReadPumpModel(**dict(serial=self.serial))    # Don't know that we need to setup the dict this way - don't think minutes is required - is serial?
    sender = Sender(self.link)          # would like to try this just once??
    single_status = False
    try:
      single_status = sender(self.command, retries=1)
    except CommsException as e:
      log.warning("Exception raised on single wake up transmission: %s" % str(e))
    if single_status:     # Can this be false or None with no exception?  If not, just move the 'return True' up to after the send
      return self.command.getData();
      # return model
    else:
      # Else pump is not awake??  is this possible? Or will it always raise exception?
      log.warning("get_model(): Pump is not awake")



  def power_control (self, minutes=None):
    """ Control Pumping """   # Bad comment
    log.warning('BEGIN POWER CONTROL %s' % self.serial)

    current_time = time.time()
    if current_time < self.last_command_time + (60 * self.MAX_SESSION_DURATION):
      log.warning("Power control: Expecting that pump is still awake.")
      return self.model

    model = self.get_model()
    if model is not None:
      log.warning("Pump is already awake.  Model = " + model)
      return model

    self.command = commands.PowerControl(**dict(minutes=minutes, serial=self.serial))    # Don't know that we need to setup the dict this way - just legacy
    repeater = Repeater(self.link)

    status = repeater(self.command, repetitions=500, ack_wait_seconds=20)

    if status:
      model = self.get_model()
      if model is not None:
        return model
      # Else what?
    else:
      raise CommsException("Failed to wakeup pump.")

  def execute (self, command):
    command.serial = self.serial
    sender = Sender(self.link)
    return sender(command)

    # for retry_count in range(self.STANDARD_RETRY_COUNT):
    #   try:
    #       sender = Sender(self.link)
    #       return sender(command)
    #   except (CommsException, AssertionError) as e:
    #       log.error("Timed out or other comms exception - %s - retrying: %s of %s" % (e, retry_count, self.STANDARD_RETRY_COUNT))
    #       time.sleep(self.RETRY_BACKOFF * retry_count)
