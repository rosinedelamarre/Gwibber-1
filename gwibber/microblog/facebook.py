
"""
Facebook interface for Gwibber
SegPhault (Ryan Paul) - 12/22/2007
"""

import urllib2, urllib, re, support
from xml.dom import minidom

CONFIG = ["message_color", "feed_url", "receive_enabled", "send_enabled"]
APP_KEY = "71b85c6d8cb5bbb9f1a3f8bbdcdd4b05"
SECRET_KEY = "41e43c90f429a21e55c7ff67aa0dc201"
LINK_PARSE =  re.compile("<a[^>]+href=\"(https?://[^\"]+)\">[^<]+</a>")

def sanitize_text(t):
  return LINK_PARSE.sub("\\1", t.strip()).replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

class Message:
  def __init__(self, client, data):
    self.client = client
    self.account = client.account
    self.protocol = client.account["protocol"]
    self.username = client.account["username"]
    self.data = data
    self.sender = data.getElementsByTagName("author")[0].firstChild.nodeValue
    self.sender_nick = self.sender
    self.sender_id = self.sender.replace(" ","_")
    self.time = support.parse_time(data.getElementsByTagName("pubDate")[0].firstChild.nodeValue)
    self.text = sanitize_text(data.getElementsByTagName("title")[0].firstChild.nodeValue)

    if self.text.startswith(self.sender):
      self.text = self.text[len(self.sender)+1:]

    self.url = data.getElementsByTagName("link")[0].firstChild.nodeValue
    self.bgcolor = "message_color"
    
    if self.client.profile_images.has_key(self.sender):
      self.image = self.client.profile_images[self.sender]
    else: self.image = "http://digg.com/img/udl.png"

    self.profile_url = "http://www.facebook.com"

class Client:
  def __init__(self, acct):
    self.account = acct
    self.profile_images = {}
    
    self.facebook = support.facelib.Facebook(APP_KEY, SECRET_KEY)
    self.facebook.session_key = self.account["session_key"]
    self.facebook.secret = self.account["secret_key"]

  def get_images(self):
    friends = self.facebook.users.getInfo(self.facebook.friends.get(), ['name', 'pic_square'])
    return dict((f["name"], f["pic_square"]) for f in friends if f["pic_square"])

  def can_send(self): return True
  def can_receive(self): return True

  def send_enabled(self):
    return self.account["send_enabled"] and \
      self.account["session_key"] != None and \
      self.account["secret_key"] != None

  def receive_enabled(self):
    return self.account["receive_enabled"] and \
      self.account["feed_url"] != None

  def connect(self, url, data = None):
    return urllib2.urlopen(urllib2.Request(url, data)).read()

  def get_data(self):
    return minidom.parseString(self.connect(
      self.account["feed_url"])).getElementsByTagName("item")

  def get_messages(self):
    self.profile_images = self.get_images()
    for data in self.get_data():
      yield Message(self, data)

  def transmit_status(self, message):
    self.facebook.users.setStatus(message, False)

