import json
import logging
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from config import CHATROOM_FN
from errbot.backends.xmpp import XMPPBackend, XMPPConnection
from errbot.utils import utf8, REMOVE_EOL, mess_2_embeddablehtml
import re

HIPCHAT_MESSAGE_URL = 'https://api.hipchat.com/v1/rooms/message'

HIPCHAT_FORCE_PRE = re.compile(r'<body>', re.I)
HIPCHAT_FORCE_SLASH_PRE = re.compile(r'</body>', re.I)
HIPCHAT_EOLS = re.compile(r'</p>|</li>', re.I)
HIPCHAT_BOLS = re.compile(r'<p [^>]+>|<li [^>]+>', re.I)


def xhtml2hipchat(xhtml):
    # Hipchat has a really limited html support
    retarded_hipchat_html_plain = REMOVE_EOL.sub('', xhtml)  # Ignore formatting
    # Readd the \n where they probably fit best
    retarded_hipchat_html_plain = HIPCHAT_EOLS.sub('<br/>', retarded_hipchat_html_plain)
    # Zap every tag left
    retarded_hipchat_html_plain = HIPCHAT_BOLS.sub('', retarded_hipchat_html_plain)
    # Fix pre
    retarded_hipchat_html_plain = HIPCHAT_FORCE_PRE.sub('<body><pre>', retarded_hipchat_html_plain)
    # Fix /pre
    retarded_hipchat_html_plain = HIPCHAT_FORCE_SLASH_PRE.sub('</pre></body>', retarded_hipchat_html_plain)
    return retarded_hipchat_html_plain


class HipchatClient(XMPPConnection):
    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token')
        self.debug = kwargs.pop('debug')
        super(HipchatClient, self).__init__(*args, **kwargs)

    def send_api_message(self, room_id, fr, message, message_format='html'):
        base = {'format': 'json', 'auth_token': self.token}
        red_data = {'room_id': room_id, 'from': fr, 'message': utf8(message), 'message_format': message_format}
        req = Request(url=HIPCHAT_MESSAGE_URL + '?' + urlencode(base), data=urlencode(red_data))
        return json.load(urlopen(req))

    def send_message(self, mess):
        if self.token and mess.type == 'groupchat':

            logging.debug('Message intercepted for Hipchat API')
            content, _ = mess_2_embeddablehtml(mess)
            room_jid = mess.to
            self.send_api_message(room_jid.node.split('_')[1], CHATROOM_FN, content)
        else:
            super(HipchatClient, self).send_message(mess)


# It is just a different mode for the moment
class HipchatBackend(XMPPBackend):
    def __init__(self, username, password, token=None):
        self.api_token = token
        self.password = password
        super(HipchatBackend, self).__init__(username, password)

    def create_connection(self):
        return HipchatClient(self.jid, password=self.password, debug=[], token=self.api_token)

    @property
    def mode(self):
        return 'hipchat'
