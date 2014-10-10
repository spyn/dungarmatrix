import json
# You will need err-markovbot and pymarkovchain
from pymarkovchain import MarkovChain
from errbot.plugin import BotPlugin
from errbot import botcmd
import httplib2

class jzacMarkov(BotPlugin)
  min_err_version = '1.6.0'

  def __init__(self):
    super(MarkovBot, self).__init__()
    self.sentenceSep = None
    self.markov = MarkovChain(dbFilePath='./markovdb')

  def callback_message(self, conn, mess):
    phrase = None
    text = mess.getBody()
    if self.sentenceSep:
      result = self.markov.generateDatabase(args, self.sentenceSep)
    else:
      result = self.markov.generateDatabase(args)

