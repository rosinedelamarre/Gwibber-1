
"""

Pidgin interface for Gwibber
SegPhault (Ryan Paul) - 11/09/2008

"""
from . import gintegration
import dbus
import re
from microblog import can

PROTOCOL_INFO = {
  "name": "Pidgin",
  "version": 0.1,
  
  "config": [
    "send_enabled"
  ],

  "features": [
    can.SEND,
  ],
}

class Client:
  def __init__(self, acct):
    self.account = acct

  def send_enabled(self):
    return self.account["send_enabled"]

  def send(self, message):
    # Strip out leading (!#) !tag and #tag's for pidgin
    message = re.sub(" [\!#]{1}", " ", message)    
    if gintegration.service_is_running("im.pidgin.purple.PurpleService"):
      gintegration.set_pidgin_status_text(message)
