

"""

Laconi.ca interface for Gwibber
SegPhault (Ryan Paul) - 11/15/2008

"""

import urllib2, urllib, base64, re, support, can, simplejson, feedparser

PROTOCOL_INFO = {
  "name": "Laconi.ca",
  "version": 0.1,
  
  "config": [
    "password",
    "username",
    "domain",
    "message_color",
    "receive_enabled",
    "send_enabled",
    "search_enabled",
  ],

  "features": [
    can.SEND,
    can.RECEIVE,
    can.SEARCH,
    can.REPLY,
    can.RESPONSES,
    can.DELETE,
    can.TAG,
    #can.THREAD,
  ],
}

NICK_PARSE = re.compile("\B@([A-Za-z0-9_]+|@[A-Za-z0-9_]$)")
HASH_PARSE = re.compile("\B#([A-Za-z0-9_\-]+|@[A-Za-z0-9_\-]$)")

def _posticon(self, a): self._getContext()["laconica_posticon"] = a["rdf:resource"]
def _has_creator(self, a): self._getContext()["sioc_has_creator"] = a["rdf:resource"]
feedparser._FeedParserMixin._start_laconica_posticon = _posticon
feedparser._FeedParserMixin._start_sioc_has_creator  = _has_creator

class Message:
  def __init__(self, client, data):
    self.client = client
    self.account = client.account
    self.protocol = client.account["protocol"]
    self.username = client.account["username"]
    self.sender = data["user"]["name"]
    self.sender_nick = data["user"]["screen_name"]
    self.sender_id = data["user"]["id"]
    self.time = support.parse_time(data["created_at"])
    self.text = support.xml_escape(data["text"])
    self.image = data["user"]["profile_image_url"]
    self.bgcolor = "message_color"
    self.url = "http://%s/notice/%s" % (self.account["domain"], data["id"])
    self.profile_url = "http://%s/%s" % (self.account["domain"], data["user"]["screen_name"])
    self.html_string = '<span class="text">%s</span>' % \
        HASH_PARSE.sub('#<a class="inlinehash" href="gwibber:tag/\\1">\\1</a>',
        NICK_PARSE.sub('@<a class="inlinenick" href="http://%s/\\1">\\1</a>' % self.account["domain"],
          support.linkify(self.text)))
    self.is_reply = re.compile("@%s[\W]+|@%s$" % (self.username, self.username)).search(self.text)

class SearchResult:
  def __init__(self, client, data, query = None):
    self.client = client
    self.account = client.account
    self.protocol = client.account["protocol"]
    self.username = client.account["username"]
    self.sender = data.author
    self.sender_nick = data.title.split(":")[0]
    self.sender_id = self.sender_nick
    self.time = support.parse_time(data.updated)
    self.text = data.title.split(":", 1)[1].strip()
    self.image = data.laconica_posticon.replace("-96-", "-48-")
    self.bgcolor = "message_color"
    self.url = data.link
    self.profile_url = data.sioc_has_creator
    self.html_string = '<span class="text">%s</span>' % \
        HASH_PARSE.sub('#<a class="inlinehash" href="gwibber:tag/\\1">\\1</a>',
        NICK_PARSE.sub('@<a class="inlinenick" href="http://%s/\\1">\\1</a>' % self.account["domain"],
          support.linkify(self.text)))
    self.is_reply = re.compile("@%s[\W]+|@%s$" % (self.username, self.username)).search(self.text)

class Client:
  def __init__(self, acct):
    self.account = acct

  def get_auth(self):
    return "Basic %s" % base64.encodestring(
      ("%s:%s" % (self.account["username"], self.account["password"]))).strip()

  def connect(self, url, data = None):
    return urllib2.urlopen(urllib2.Request(
      url, data, {"Authorization": self.get_auth()})).read()

  def get_messages(self):
    return simplejson.loads(self.connect(
      "http://%s/api/statuses/friends_timeline.json" % self.account["domain"]))

  def get_responses(self):
    return simplejson.loads(self.connect(
      "http://%s/api/statuses/replies.json" % self.account["domain"]))

  def get_search(self, query):
    return feedparser.parse(urllib2.urlopen(
      urllib2.Request("http://%s/search/notice/rss" % self.account["domain"],
        urllib.urlencode({"q": query}))))["entries"]

  def get_tag(self, query):
    return feedparser.parse(urllib2.urlopen(
      urllib2.Request("http://%s/index.php" % self.account["domain"],
        urllib.urlencode({"action": "tagrss", "tag":
          query}))))["entries"]

  def search(self, query):
    for data in self.get_search(query):
      yield SearchResult(self, data, query)

  def tag(self, query):
    for data in self.get_tag(query):
      yield SearchResult(self, data, query)

  def responses(self):
    for data in self.get_responses():
      yield Message(self, data)

  def receive(self):
    for data in self.get_messages():
      yield Message(self, data)

  def send(self, message):
    return self.connect("http://%s/api/statuses/update.json" % self.account["domain"],
        urllib.urlencode({"status":message}))
