import json
from errbot import botcmd, BotPlugin

class JabberzacMagic(BotPlugin)
  min_err_version = '1.6.0'

  def callback_message(self, conn, mess):
    phrase = None;

    if mess.getBody().find('world cup') != -1:
      phrase = "o======<0♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫"
    elif mess.getBody().find('love') != -1:
      phrase = "baby don't hurt me"
    elif mess.getBody().find('the meaning of life') != -1:
      phrase = "42"
    elif mess.getBody() == "the air speed velocity of an unladen swallow":
      phrase = "what do you mean, an African or European Swallow?"
    elif mess.getBody().find('what is') != -1:
      phrase = self.calculateChance(
        {"No idea, why dont you google it, fuck": 0.9, 
        mess.getBody().replace('what is','http://www.lmgtfy.com/?q='): 0.1}
      )
    elif mess.getBody().find('girlfriend') != -1:
      phrase = self.calculateChance({self.lang.ugettext('MY GIRLFRIEND'): 0.2, ':cloricus:': 0.1})
    elif mess.getBody().find('awesome') != -1:
      chance = {':awesome:': 0.1, ':awesomelon:': 0.05}
      phrase = self.calculateChance(chance)
    elif mess.getBody().find(':hfive:') != -1:
      chance = {':hfive:': 0.99, ':awesome::hf::awesomelon:': 0.01}
      phrase = self.calculateChance(chance)
    elif mess.getBody().find('alot') != -1:
      chance = {':eng101: "a lot"': 0.9, ':argh:': 0.1}
      phrase = self.calculateChance(chance)
    elif mess.getBody().find('bad') != -1:
      chance = {self.lang.ugettext('mlyp'): 0.2}
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
            chance = self.calculateChance({'yeah' : 0.05, 'nah' : 0.05})
            if chance is not None:
                random.seed()
                random.choice("things")


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
