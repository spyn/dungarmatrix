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

    
  @botcmd



    
    elif mess.getBody().find('bad') != -1:
      chance = {'mlyp': 0.2}
      phrase = self.calculateChance(chance)

    # url matches
    elif mess.getBody().find('http') != -1:
        url = mess.getBody().group('url')
        if url.find('imgurl') != -1:
            phrase = self.calculateChance({'Jesus Christ :nws: that shit'): 0.01, 'thanks asshole i just got fired :mad:': 0.01, 'OMG hawt': 0.01})
        elif mess.getBody().find('vidid') != -1:
            vidid = mess.getBody().match.group('vidid')
            rnd = random.random()
            if rnd < 0.1:
                phrase = self.getRandomYoutubeComment(vidid)
        else 
            phrase = self.calculateChance({'pro-click zone': 0.05, 'not clicking that': 0.05, 'more like'+' http://bacolicio.us/'+url+' amirite'): 0.01 })
    
    else
        # chance of saying a random thing after someone types something... chance of chances
        chance = self.calculateChance({True: 0.05})
        if chance is not None:
            c = 0.005
            choice = {'welp': c,
                      'guys, let\'s move to syndicate': c,
                      'remedial saw me as a young version of himself!': c,
                      'I joined triumvirate': c,
                      ':dungar:': c,
                      'yeah i dont think ill get that machariel back :(': c,
                      'check out all these gistii a-types i just farmed': c,
                      'i joined PL mainly because they fit my playstyle and level of talent': c,
                      'triumvirate died :(': c,
                      "Man I'm so close to finishing Cloaking V for those new blackops BSes. I can't wait.": c,
                      'That angel bird has pictures of herself on the forums and if I wasn\'t so sure she\'s insane I\'d probably hit that :)' : c,
                      #bencos
                      'duke nukem came out when i was born i played the shit out of duke nukem 3d tho': c,
                      'print spoolers get stuck every 2nd print': c,
                      'do cows die of sound overdose ': c,
                      'i have too much shit from when i was like 8 years old': c,
                      'i think i need a keyboard with red switches or browns': c,
                      'php is pretty good without libraries i\'ll give it that': c,
                      'i dont know why people like beetroot it doesnt taste good + stains ur clothes': c,
                      'you should be able to take electives for kernel and language design. you can likely take some from other unis too and still get credit': c,
                      '2014-05-12T04:20:00+0100 who formats datetime like this :mad:': c,
                      'time to nerd out about space all day': c,
                      'what kind of tumblr administrator cant even upload a gif': c,
                      'http://41.media.tumblr.com/b35323f9e355fc5db9c874bd35d8fb31/tumblr_n71fa6dLsv1tcu7e6o1_1280.jpg': c,
                      '$6 shirt marked down to $4 cause of my sweet business contacts': c,
                      'benco, pro code detective: no code is out of reach': c,
                      'benco, coding illusionist: my ability to code is merely an illusion': c,
            }
            phrase = self.calculateChance(chance)

        # make shit happen
        if phrase is not None: 
            self.send(mess.getFrom(), phrase, message_type=mess.getType())







    @botcmd
    def goonball(self, mess, args):
        """The magic goon ball"""
        chance = {'As I see it, yes. Furthermore,': 0.05,
                  'Ask again when your daughter is legal': 0.05,
                  'Can\'t talk, deadtear will ban me': 0.05,
                  'Can\'t talk, solo will ban me': 0.05,
                  'Can\'t talk, lux will pink text me': 0.05,
                  'Concentrate and ask again faggot': 0.05,
                  'My sources say: "You are a faggot"': 0.05,
                  'Do fatties like ham?': 0.05,
                  'Do fatties like candy?': 0.05,
                  'About a likely as the forums going down. Again.': 0.05,
                  'My reply is rofl': 0.05,
                  'My sources say send Urcher 1B ISK for an answer': 0.05,
                  'Outlook better than thunderbird': 0.05,
                  'Outlook not so good, mlyp': 0.05,
                  'Reply hazy, kill yourself': 0.05,
                  'Signs point to your mothers house, because that is the worlds most common destination :iceburn:': 0.05,
                  'Only if CCP can keep the servers going for 24 *consecutive* hours': 0.05,
                  'Only if Solo can keep the servers going for 24 *consecutive* hours': 0.05,
                  'no u': 0.05,
                  'Yes - faggot': 0.05,
                  'Cute question. ISK sent': 0.05}
        #?? self.send(mess.getFrom(), self.calculateChance(chance), message_type=mess.getType())
        return self.calculateChance(chance)

""" These functions are pulled from dungarmatic """
      # Imported function from jabber.py
    def calculateChance(self, chance):
        """chance should be a dictionary with the keys being a number like 0.25
            and the value a string to return, the keys should sum to a maximum 
            of <= 1.0"""
        random.seed()
        rnd = random.random()
        t = 0
        for message in chance.keys():
            c = chance[message];
            m = t
            t = t + c
            if rnd < t and rnd >= m:
                return message
        return None

    def getRandomYoutubeComment(self, vidid):
        commentstream = urllib.urlopen("http://gdata.youtube.com/feeds/api/videos/"+vidid+"/comments")
        response = commentstream.read()
        dom = xml.dom.minidom.parseString(response)
        entries = dom.getElementsByTagName("content")
        rand_index =  random.randint(11, 20)
        if(len(entries) >= rand_index):
            comment = ''
            entry = entries[rand_index]
            for node in entry.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    comment = comment+node.data
            return comment
        return None
