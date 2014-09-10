# -*- coding: utf-8 -*-
import jabber
#import twitter
import random
import time
import re
import MySQLdb
import dungarmatic_config as config
import urllib2
import urllib
import os
import xml.dom.minidom
import math
import threading
from heapq import heappush, heappop
import traceback

COOKIEFILE = 'cookies.lwp'
database = config.config['database']
dbhost = config.config['dbhost']
dbuser = config.config['dbuser']
dbpass = config.config['dbpass']
#twitterauth = config.config['twitter']['account']
#twitterapi = twitter.Api(**twitterauth)

# the path and filename to save dungar's cookies in
"""
@class: EveBot
@extends: jabber.Bot
@summary: A basic eve bot that remembers API keys and tries to answer questions about eve
"""
class EveBot (jabber.Bot):
    def initBot(self):
        self.initEve()
        
    def initEve (self):
        self.nickRegex = self.resource
        self.addressRegex = r"(:| :|,)\s*"
        self.toMe = r"^\s*" + self.nickRegex + self.addressRegex
        
        self.addHandler([self.toMe + r".*\?\Z"],self.handler_question)
        self.addHandler([self.toMe + r"kick\s+(?P<user>.*)"],self.handler_kick)
        self.banned_words = set()
        self.banned_regex = None
        self.addHandler([self.toMe + r"add banned word (?P<word>.*)"],self.handler_add_banned_word)
        self.addHandler([self.toMe + r"(?:remove|delete) banned word (?P<word>.*)"],self.handler_remove_banned_word)
        self.addHandler([self.toMe + r"clear banned words?(?: list)?"],self.handler_clear_banned_words)
        self.addHandler([self.toMe + r"list banned words"],self.handler_list_banned_words)
        self.addProcessor(self.processor_banned_words)
        self.reminders = []
        self.addHandler([self.toMe + r'remind\s+(?P<to>.*)\s+to\s+(?P<reminder>.*)\s+in\s+(?P<duration>.*)'],self.handler_reminder)
        self.addLoop(self.loop_reminder)
        self.addHandler([r"\b(world\s+cup|vuvuzela)\b"],self.handler_world_cup)
        self.addHandler([r"\bliterally\b"],self.handler_literally)

    def handler_literally(self, mess, match):
        return self.calculateChance({'I think you mean figuratively':0.05,
                                     'seriously literally?':0.05})

    def handler_world_cup(self, mess, match):
        return self.calculateChance({
                'BZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZT': 0.05,
                'o======<0♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫♪♫': 0.05})

    def parse_duration(self, duration):
        '''Parse a string representing a duration, return number of seconds'''
        #unit to multiplier for converting to seconds
        units = {'second':1.0,
                 'seconds':1.0,
                 's':1.0,
                 'minute':60.0,
                 'minutes':60.0,
                 'm':60.0,
                 'min':60.0,
                 'hour':60.0*60.0,
                 'hours':60.0*60.0,
                 'h':60.0*60.0,
                 'day':24.0*60.0*60.0,
                 'days':24.0*60.0*60.0,
                 'd':24.0*60.0*60.0
                 }
        ret = 0.0
        subdurations = re.findall(r'(?P<amount>[0-9]+(?:\.[0-9]+)?)\s*(?P<unit>[a-z]+)',duration, re.IGNORECASE)
        for subduration in subdurations:
            amount = subduration[0]
            unit = subduration[1]
            ret += float(amount) * units[unit]
        return ret
        
    def handler_reminder(self, mess, match):
        if mess.getFrom().getResource() == self.resource:
            return
        now = time.time()
        reminder = match.group('reminder').strip()
        duration = match.group('duration').strip()
        to = match.group('to').strip()
        try:
            time_s = self.parse_duration(duration)
        except:
            return '%s: Sorry, I didn\'t understand that duration :('%mess.getFrom().getResource()
        if time_s == 0:
            return '%s: Sorry, I didn\'t understand that duration :('%mess.getFrom().getResource()
        if to == 'me':
            to = mess.getFrom().getResource()
            reminder = re.sub(r'\bmy\b', 'your', reminder)
        else:
            reminder = re.sub(r'\bmy\b', mess.getFrom().getResource()+'\'s', reminder)
        reminder = re.sub(r'\bme\b', mess.getFrom().getResource(), reminder)
        data = {'from':mess.getFrom().getResource(),
                'to':to,
                'reminder':reminder,
                'duration':time_s}
        heappush(self.reminders, (now+time_s, data))
        
        if data['to'] == data['from']:
            return '%(from)s: ok I\'ll remind you to %(reminder)s in %(duration)is'%data
        return '%(from)s: ok I\'ll remind %(to)s to %(reminder)s in %(duration)is'%data

    def loop_reminder(self):
        now = time.time()
        if len(self.reminders) > 0 and now > self.reminders[0][0]:
            reminder = heappop(self.reminders)[1]
            if reminder['from'] == reminder['to']:
                return '%(to)s: you asked me to remind you to %(reminder)s'%reminder
            return '%(to)s: %(from)s asked me to remind you to %(reminder)s'%reminder
        
    def handler_kick(self, mess, match):
        if self.resource not in self.channelModerators:
            return mess.getFrom().getResource()+': I can\'t. I\'m not a mod :smith:'
        kicker = mess.getFrom().getResource()
        if kicker not in self.channelModerators:
            self.kick(kicker, reason='Only mods may kick')
            return
        nick = match.group("user")
        if nick in self.channelModerators:
            return '%s: Not kicking a mod :mad:'%(kicker)
        if nick in self.channelRoster:
            #print 'kicking %s, requested by %s'%(nick,kicker)
            self.kick(nick, reason='kick requested by %s'%(kicker))
            return '%s: ok. i\'ve kicked %s for you'%(kicker,nick)
        else:
            return '%s: who?'%(kicker)
        
    def handler_add_banned_word(self, mess, match):
        banner = mess.getFrom().getResource()
        if self.resource not in self.channelModerators:
            return '%s: I\'m not a mod, so there are no banned words'%(banner)
        if banner not in self.channelModerators:
            self.kick(banner, reason='Only mods may add banned words')
            return
        word = match.group('word')
        if word in self.banned_words:
            return "%s: '%s' is already banned"%(banner,word)
        self.banned_words.add(word)
        self.build_banned_word_regex()
        #print 'Banned words: %s added \'%s\''%(banner,word)
        return "%s: Banned word '%s' added"%(banner,word)
        
    def handler_remove_banned_word(self, mess, match):
        banner = mess.getFrom().getResource()
        if self.resource not in self.channelModerators:
            return '%s: I\'m not a mod, so there are no banned words'%(banner)
        if banner not in self.channelModerators:
            self.kick(banner, reason='Only mods may remove banned words')
            return
        word = match.group('word')
        if not word in self.banned_words:
            return "%s: '%s' is not banned"%(banner,word)
        self.banned_words.remove(word)
        self.build_banned_word_regex()
        #print 'Banned words: %s removed \'%s\''%(banner,word)
        return "%s: Banned word '%s' removed"%(banner,word)
        
    def handler_clear_banned_words(self, mess, match):
        banner = mess.getFrom().getResource()
        if self.resource not in self.channelModerators:
            return '%s: I\'m not a mod, so there are no banned words'%(banner)
        if banner not in self.channelModerators:
            self.kick(banner, reason='Only mods may clear the banned words list')
            return
        if len(self.banned_words) == 0:
            return "%s: There are no banned words"%(banner)
        self.banned_words = set()
        self.build_banned_word_regex()
        #print "Banned words: %s cleared the banned word list"%(banner)
        return "%s: Banned words list cleared"%(banner)
        
    def handler_list_banned_words(self, mess, match):
        if self.resource not in self.channelModerators:
            return mess.getFrom().getResource()+': I\'m not a mod, so there are no banned words'
        if len(self.banned_words) == 0:
            return '%s: There are no banned words'%(mess.getFrom().getResource())
        wordlist = ""
        for word in sorted(self.banned_words):
            wordlist+="'%s', "%word
        wordlist=wordlist[0:-2]
        return '%s: The banned words are: %s'%(mess.getFrom().getResource(),wordlist)

    def build_banned_word_regex(self):
        if len(self.banned_words) == 0:
            self.banned_regex = None
            return
        banned_regex=r'^(?:.*\s+)?(?P<word>'
        for word in self.banned_words:
            banned_regex+=re.escape(word)+"|"
        banned_regex=banned_regex[0:-1]
        banned_regex+=r')(?:\s+.*)?$'
        self.banned_regex = re.compile(banned_regex, re.IGNORECASE)

    def processor_banned_words(self, mess):
        if self.resource not in self.channelModerators:
            return
        if not self.banned_regex:
            return
        if mess.getFrom().getResource() in self.channelModerators:
            return
        match = self.banned_regex.search(mess.getBody())
        if match:
            #print 'Banned words: kicking %s for saying \'%s\''%(mess.getFrom().getResource(),match.group('word'))
            self.kick(mess.getFrom().getResource(),reason='%s is a banned word'%(match.group('word')))
        
    def bot_8ball (self, mess, args):
        """The magic 8 ball"""
        chance = {self.lang.ugettext('As I see it, yes'): 0.05,
                  self.lang.ugettext('Ask again later'): 0.05,
                  self.lang.ugettext('Better not tell you now'): 0.05,
                  self.lang.ugettext('Cannot predict now'): 0.05,
                  self.lang.ugettext('Concentrate and ask again'): 0.05,
                  self.lang.ugettext('Don\'t count on it'): 0.05,
                  self.lang.ugettext('It is certain'): 0.05,
                  self.lang.ugettext('It is decidedly so'): 0.05,
                  self.lang.ugettext('Most likely'): 0.05,
                  self.lang.ugettext('My reply is no'): 0.05,
                  self.lang.ugettext('My sources say no'): 0.05,
                  self.lang.ugettext('Outlook good'): 0.05,
                  self.lang.ugettext('Outlook not so good'): 0.05,
                  self.lang.ugettext('Reply hazy, try again'): 0.05,
                  self.lang.ugettext('Signs point to yes'): 0.05,
                  self.lang.ugettext('Very doubtful'): 0.05,
                  self.lang.ugettext('Without a doubt'): 0.05,
                  self.lang.ugettext('Yes'): 0.05,
                  self.lang.ugettext('Yes - definitely'): 0.05,
                  self.lang.ugettext('You may rely on it'): 0.05}
        return mess.getFrom().getResource() + ": " + self.calculateChance(chance)
    def bot_goonball (self, mess, args):
        """The magic goon ball"""
        chance = {self.lang.ugettext('As I see it, yes. Furthermore,'): 0.05,
                  self.lang.ugettext('Ask again when your daughter is legal'): 0.05,
                  self.lang.ugettext('Can\'t talk, deadtear will ban me'): 0.05,
                  self.lang.ugettext('Can\'t talk, solo will ban me'): 0.05,
                  self.lang.ugettext('Can\'t talk, lux will pink text me'): 0.05,
                  self.lang.ugettext('Concentrate and ask again faggot'): 0.05,
                  self.lang.ugettext('My sources say: "You are a faggot"'): 0.05,
                  self.lang.ugettext('Do fatties like ham?'): 0.05,
                  self.lang.ugettext('Do fatties like candy?'): 0.05,
                  self.lang.ugettext('About a likely as the forums going down. Again.'): 0.05,
                  self.lang.ugettext('My reply is rofl'): 0.05,
                  self.lang.ugettext('My sources say send Urcher 1B ISK for an answer'): 0.05,
                  self.lang.ugettext('Outlook better than thunderbird'): 0.05,
                  self.lang.ugettext('Outlook not so good, mlyp'): 0.05,
                  self.lang.ugettext('Reply hazy, kill yourself'): 0.05,
                  self.lang.ugettext('Signs point to your mothers house, because that is the worlds most common destination :iceburn:'): 0.05,
                  self.lang.ugettext('Only if CCP can keep the servers going for 24 *consecutive* hours'): 0.05,
                  self.lang.ugettext('Only if Solo can keep the servers going for 24 *consecutive* hours'): 0.05,
                  self.lang.ugettext('no u'): 0.05,
                  self.lang.ugettext('Yes - faggot'): 0.05,
                  self.lang.ugettext('Cute question. ISK sent'): 0.05}
        return mess.getFrom().getResource() + ": " + self.calculateChance(chance)
    
    def getDomText(self, element):
        text = ""
        for node in element.childNodes:
            if node.nodeType == node.TEXT_NODE:
                text = text + node.data
            else:
                text = text + self.getDomText(node)
        return text
    
    def findParagraph(self, node):
        if (node.localName == 'p'):
            return node
        if (node.localName == 'table'):
            return None
        for child in node.childNodes:
            paragraph = self.findParagraph(child)
            if paragraph:
                return paragraph
        

    def getDescription (self, phrase):
        """Gets a description from wikipedia"""
        phrase = phrase.encode('utf-8')
        if phrase == "love":
            return "baby don't hurt me"
        if phrase == "the meaning of life, the universe and everything" or phrase == "the meaning of life" or phrase == "the meaning of life the universe and everything":
            return "42"
        if phrase == "the air speed velocity of an unladen swallow":
            return "what do you mean, an African or European Swallow?"
        if phrase == 'best in life' or phrase == 'the best in life':
            return self.calculateChance({'To crush your enemies, see them driven before you, and to hear the lamentation of their women':0.99,
                                         'To crush you biscuits, see them dunked in your tea, and hear the conversation of your auntie':0.01})
        
        url = self.lang.ugettext('http://en.wikipedia.org/wiki/%s').encode('utf-8') % phrase.replace(" ","_")
        urlopen = urllib2.urlopen
        Request = urllib2.Request
        txheaders =  {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
        txdata = urllib.urlencode({})
        try:
            self.httpRequest = Request(url, txdata, txheaders)
            handle = urlopen(self.httpRequest)
        except urllib2.HTTPError:
            return self.calculateChance({"No idea, why dont you google it, fuck": 0.9,
                                         "http://www.lmgtfy.com/?q="+urllib.quote_plus(phrase): 0.1})
        except:
            traceback.print_exc()
            return self.calculateChance({"No idea, why dont you google it, fuck": 0.9,
                                         "http://www.lmgtfy.com/?q="+urllib.quote_plus(phrase): 0.1})
        else:
            handle.readline()
            response = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'+handle.read()
            try:
                dom = xml.dom.minidom.parseString(response)
            except Exception:
                traceback.print_exc()
                return "No fucking idea"

        divs = dom.getElementsByTagName("div")
        paragraph = None
        for div in divs:
            if div.getAttribute('id') == "bodyContent":
                paragraph = self.findParagraph(div)
            if paragraph:
                break
        desc = self.getDomText(paragraph)
        return desc

    def handler_question (self, mess, match):
        """Ask a stupid question, get a stupid answer"""
        text = mess.getBody()
        
        #Who is <nick>?
        regex = self.toMe + self.lang.ugettext("REGEX_WHOIS")
        regex = re.compile(regex, re.IGNORECASE)
        m = regex.search(text)
        if m:
            nick = m.group("nick")
            query = m.group("query")
            if nick in self.channelRoster and self.channelRoster[nick]:
                return mess.getFrom().getResource() + ": " + nick + " "+query+" "+str(self.channelRoster[nick])
        
        #What is?
        regex = self.toMe + self.lang.ugettext("REGEX_WHAT_IS")
        regex = re.compile(regex, re.IGNORECASE)
        m = regex.search(text)
        if m:
            phrase = m.group("phrase")
            reply = self.getDescription(phrase)
            if reply:
                return mess.getFrom().getResource() + ": " + reply

        #What do you think about <word>?
        regex = self.toMe + self.lang.ugettext("REGEX_WHAT_DO_YOU_THINK_ABOUT")
        regex = re.compile(regex, re.IGNORECASE)
        m = regex.search(text)        
        if m:
            phrase = m.group("phrase")
            reply = self.getMarkov(phrase, 0)
            if reply:
                return mess.getFrom().getResource() + ": " + reply
        
        regex = self.toMe + self.lang.ugettext("REGEX_HOW_MANY")
        regex = re.compile(regex, re.IGNORECASE)
        m = regex.search(text)
        if m:
            return mess.getFrom().getResource() + ": " + self.calculateChance({str(random.randint(0,10)): 0.99,
                                                                               str(random.randint(11,1000000)): 0.01})
        
        regex = self.toMe + self.lang.ugettext("REGEX_WHEN")
        regex = re.compile(regex, re.IGNORECASE)
        m = regex.search(text)
        if m:
            return self.handler_when(mess, m)
        
        regex = self.toMe + self.lang.ugettext("REGEX_OPTIONS")
        regex = re.compile(regex, re.IGNORECASE)
        m = regex.search(text)
        if m:
            return self.handler_options(mess, m)

        return self.calculateChance({self.bot_8ball(mess, ""): 0.9,
                  self.bot_goonball(mess, ""): 0.1})  

    def handler_when(self, mess, match):
        now = time.time()
        laterlong = now + random.randint(1,60*60*24)
        latershort = now + random.randint(1,60*60*24*7)
        ret = mess.getFrom().getResource() + ": " 
        if re.search(self.lang.ugettext("REGEX_WEED"), mess.getBody()):
            return 'At 4:20 :420::420::420:'
        return ret + self.calculateChance({'In '+self.calcTimeLeft(laterlong): 0.45,
                                           'In '+self.calcTimeLeft(latershort): 0.45,
                                           'At 4:20 :420::420::420:': 0.05,
                                           'Never': 0.05})

    def handler_options (self, mess, match):
        """[img-timeline]"""
        options = match.group('options')
        options = re.split(self.lang.ugettext("REGEX_OR"), options)
        choice = {'checkbox, voted all': 0.005,
                  "not checkbox, didn't vote": 0.005}
        for option in options:
            choice[option] = 0.99/len(options)
        ret = mess.getFrom().getResource() + ": " 
        return ret  + self.calculateChance(choice)
        


"""
@class: GoonFleetBot
@extends: EveBot
@summary: LOL z0r mlyp booya didn't want that titan anyway get out faggot :condi:
"""
class GoonFleetBot (EveBot):    
    def initBot(self):
        self.initEve()
        self.initGoonFleet()
        self.youtubes = []
        self.images = []
        
    def initGoonFleet(self):           
        self.wordAssociations = {};
        self.z0rStarted = False
        self.z0rCompleted = False
        self.recentLinks = []
        self.z0rs = 0
        self.nextz0rStart = random.randint(15*60, 120*60)
        self.nextRandomComment = random.randint(15*60, 120*60)
        #self.addServerLoop('update_routes',self.loop_routesUpdate)
        
        
        """Handlers test if a regex matches in the message, 
        pass an array of regexes and a callback function for great justice"""
        mlyp = [self.lang.ugettext("REGEX_MLYP")]
        self.addHandler(mlyp,self.handler_mlyp)
        
        self.addHandler([r"awesome(?:|!|.)*\Z"],self.handler_awesome)
        self.addHandler([self.toMe+r".*?:hfive:\Z"],self.handler_highfive)
        self.addHandler([r"(?:\s|\A)alot(?:\s|\Z)"],self.handler_alot)
        
        self.addHandler([r"(?:\s|\A)dungar(?:\s|\Z)"],self.handler_dungar)
        self.addHandler([self.lang.ugettext("REGEX_C_D")],self.handler_cd)
        self.addHandler([r"\Amajor crimes(?:|\?|!|\.)*\Z"], self.handler_sheeeeeeeeeit)
        self.addHandler([r"\b(?P<url>(https?|ftp)://[-A-Z0-9+&@#/%?=~_|!:,.;]+)\b"],self.handler_imgtimeline)     
        self.addHandler([r"\b(?P<url>http://[\w\.]*youtube\.com/[\w\?&]*v=(?P<vidid>[\w-]*))"],self.handler_youtube)
        self.addHandler([r"\b(?P<url>(https?|ftp)://[-A-Z0-9+&@#/%?=~_|!:,.;]*[-A-Z0-9+&@#/%=~_|]\.(?:jpg|png|gif))\b"],self.handler_img)  
        self.addHandler([r"\b(?P<url>(https?|ftp)://[-A-Z0-9+&@#/%?=~_|!:,.;]*[-A-Z0-9+&@#/%=~_|])\b"],self.handler_url)                
        self.addHandler([self.lang.ugettext("REGEX_MY_GIRLFRIEND")],self.handler_MYGIRLFRIEND)
        
        
        
        
        """Processors handle every incoming message, check the mess object or
            self.history for messages. 
            return None to do nothing and pass control to the next processor"""
        self.addProcessor(self.processor_words)
        self.addProcessor(self.processor_z0r)
        #self.addProcessor(self.processor_magical_learning_dungar)
        
        
        """Loops run once a second, even when no messages have been received"""
        self.addLoop(self.loop_z0rStarter)
        self.addLoop(self.loop_randomComments)
             
    
    """------------------- CALLBACK FUNCTIONS START HERE BOOYA -------------------"""
    def processor_words(self, mess):
        reply = None
        if(len(mess.getBody()) > 400):
            c = 0.05
            chance = {':words:': c,
                      self.lang.ugettext('holy shit')+' :words:': c,
                      self.lang.ugettext('tl;dr'): c,
                      ':getoutfag:': c,
                      self.lang.ugettext('lol, wut'): c,
                      self.lang.ugettext('hurf blurf'): c}
            reply = self.calculateChance(chance)
        return reply

    def processor_magical_learning_dungar(self, mess):
        chanceOfResponding = 0.1
        if mess.getFrom().getResource() == self.resource:
            return
        #Add associations for the previous messages
        now = time.time()
        for j, recentMess in enumerate(self.history):
            i = 11 - j
            i *= i
            if recentMess == mess.getBody():
                continue
            if not recentMess in self.wordAssociations: #Create a new association array
                associations = [[mess.getBody(), i, now]]
                self.wordAssociations[recentMess] = associations
            else:
                found = False
                associations = self.wordAssociations[recentMess]
                for association in associations:
                    if association[0] == mess.getBody(): #Add to existing association
                        association[1] += i
                        association[2] = now
                        found = True
                        break
                if not found: #Add a new association to the array
                    associations.append([mess.getBody(), i, now])
        #Find associations for the current message
        if mess.getBody() in self.wordAssociations:
            associations = self.wordAssociations[mess.getBody()]
            totalPoints = 0
            for association in associations:
                totalPoints += association[1]
            responses = {}
            for association in associations:
                responses[association[0]] = 1.0*association[1]/totalPoints
            response = self.calculateChance(responses)
            if response:
                self.log("Association for "+mess.getBody()+": "+response)
            return self.calculateChance({response: chanceOfResponding})
        return None
        
    def loop_randomComments(self):
        if self.timeSinceLastMessage > self.nextRandomComment and self.timeSinceLastOwnMessage > self.timeSinceLastMessage:
            self.nextRandomComment = random.randint(15*60, 120*60)
            self.timeSinceLastMessage = 0
            massPing = ''
            for nick in sorted(self.channelRoster):
                if nick == self.resource:
                    continue
                massPing += nick
                massPing += ', '
            massPing = massPing[0:-2]
            massPing += ': hi'
            randFact = ':eng101: '+self.getDescription('Special:Random')
            chance = {randFact: 0.999,
                      massPing: 0.001}
            return self.calculateChance(chance)  
     
    def processor_z0r (self,mess):
        """z0rz0rz0rz0rz0rz0rz0rz0rz0r"""
        if mess.getFrom().getResource() == self.resource:
            return
        if len(self.history)>0 and (self.history[0]=='z' or self.history[0]=='0' or self.history[0]=='r'):
            desireToContinue = 0.1 #Chance of continuing a z0r chain, increases with the length of the chain
            currentPosition = self.history[0] #message being examined
            validChain = False #Are we currently part of a valid z0r chain

            if self.history[0] == 'z':
                validChain = True
            if self.history[0] == 'z' or self.history[0] == 'r':
                self.z0rstarted = False

            for i in range(1,len(self.history)):
                if self.history[i] == 'z' and currentPosition == '0':
                    validChain = True
                    desireToContinue = desireToContinue + 0.1
                elif self.history[i] == '0' and currentPosition == 'r':
                    desireToContinue = desireToContinue + 0.1
                elif self.history[i] == 'r' and currentPosition == 'z':
                    desireToContinue = desireToContinue + 0.1
                else:
                    break
                currentPosition = self.history[i]
            if not validChain or self.z0rstarted:
                return
            if self.history[0]=='z':
                return self.calculateChance({'0': desireToContinue,
                                             self.lang.ugettext('shut up faggot'): 0.01,
                                             self.lang.ugettext('fuck you and the z0r you rode in on'): 0.01})
            if self.history[0]=='0':
                return self.calculateChance({'r': desireToContinue})
            if self.history[0]=='r':
                reply = self.calculateChance({'z': desireToContinue})
                if reply:
                    self.z0rstarted = True
                return reply
        else:
            self.z0rstarted = False
    
    def loop_z0rStarter (self):        
        if self.timeSinceLastMessage > self.nextz0rStart and self.timeSinceLastOwnMessage > self.timeSinceLastMessage and len(self.history) > 0 and self.history[0] != 'z' and self.history[0] != '0':
            self.nextz0rStart = random.randint(15*60, 120*60)
            #if self.debug:
                #self.log('attempting to start z0r chain')
            reply = self.calculateChance({'z': 0.001})
            if reply:
                self.z0rstarted = True
            return reply
        else:
            return None
        
    def handler_dungar (self, mess, match):
        """The automatic dungar"""
        c = 0.005
        chance = {self.lang.ugettext('welp'): c,
                  self.lang.ugettext('My sister has been looking pretty good lately'): c,
                  self.lang.ugettext('guys, let\'s move to syndicate'): c,
                  self.lang.ugettext('My dad is dead'): c,
                  self.lang.ugettext('remedial saw me as a young version of himself!'): c,
                  self.lang.ugettext('I joined triumvirate'): c,
                  self.lang.ugettext(':dungar:'): c,
                  self.lang.ugettext('yeah i dont think ill get that machariel back :('): c,
                  self.lang.ugettext('check out all these gistii a-types i just farmed'): c,
                  self.lang.ugettext('i joined PL mainly because they fit my playstyle and level of talent'): c,
                  self.lang.ugettext('triumvirate died :('): c,
                  self.lang.ugettext("Man I'm so close to finishing Cloaking V for those new blackops BSes. I can't wait."): c,
                  self.lang.ugettext('That angel bird has pictures of herself on the forums and if I wasn\'t so sure she\'s insane I\'d probably hit that :)') : c}
        return self.calculateChance(chance)
    
    def handler_cd (self, mess, match):
        """this bot is shit c/d?"""
        chance = {self.lang.ugettext('c'): 0.5,                  
                  self.lang.ugettext('d'): 0.5}
        return self.calculateChance(chance)
    
    def handler_MYGIRLFRIEND(self, mess, match):
        """MY GIRLFRIEND"""
        return self.calculateChance({self.lang.ugettext('MY GIRLFRIEND'): 0.2, ':cloricus:': 0.1})
 
    def handler_sheeeeeeeeeit (self, mess, match):
        """major crimes?"""
        rnd = random.random()
        ees = rnd * 50
        if ees < 18:
            ees = 12
        if ees > 45:
            ees = rnd * 100
                
        ret = "sh"
        ret += "e"*int(ees)
        ret += "it"
            
        return self.calculateChance({ret: 0.2})

   
    def handler_mlyp (self, mess, match):
        """much like your posting"""
        chance = {self.lang.ugettext('mlyp'): 0.2}
        return self.calculateChance(chance)

    def handler_imgtimeline (self, mess, match):
        """[img-timeline]"""
        url = match.group('url') 
        if url not in self.recentLinks:
            if len(self.recentLinks) > 10:
                self.recentLinks.pop()           
            self.recentLinks.insert(0,url)
        else:
            return self.calculateChance({self.lang.ugettext('img-timeline'): 0.6,'[img-timeline]': 0.4})
    
    def handler_img (self, mess, match):
        """pro-click zone"""
        url = match.group('url')       
        if url not in self.images:
            self.images.append(url)
        return self.calculateChance(
            {self.lang.ugettext('Jesus Christ :nws: that shit'): 0.01,
             self.lang.ugettext('thanks asshole i just got fired :mad:'): 0.01,
             self.lang.ugettext('OMG hawt'): 0.01})
    
    def handler_youtube (self, mess, match):
        """youtube videos"""
        vidid = match.group('vidid')
        if vidid not in self.youtubes:
            self.youtubes.append(vidid)
        rnd = random.random()
        if rnd < 0.1:
            return self.getRandomYoutubeComment(vidid) 

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
        

    def handler_url (self, mess, match):
        """pro-click zone"""
        if mess.getFrom().getResource() == self.resource:
            return
        url = match.group('url')
        return self.calculateChance(
            {self.lang.ugettext('pro-click zone'): 0.05,
             self.lang.ugettext('not clicking that'): 0.05,
             self.lang.ugettext('more like')+' http://bacolicio.us/'+url+' '+self.lang.ugettext('amirite'): 0.01})
        
    def handler_awesome (self, mess, match):
        """:awesome:"""
        chance = {':awesome:': 0.1, ':awesomelon:': 0.05}
        return self.calculateChance(chance)    
    
    def handler_highfive (self, mess, match):
        """:hfive:"""
        regex = re.compile(r":hfive:")
        if len(self.history) < 3 or not regex.search(self.history[2]):
            chance = {':hfive:': 0.99, ':awesome::hf::awesomelon:': 0.01}
            return self.calculateChance(chance)
        return None

    def handler_alot (self, mess, match):
        """alot"""
        chance = {':eng101: "a lot"': 0.9, ':argh:': 0.1}
        return mess.getFrom().getResource() + ": " + self.calculateChance(chance)

"""
@class: Jabberzac
@extends: GoonFleetBot
@summary: Anzac squad is the best squad
"""
class Jabberzac (GoonFleetBot):
    def initBot(self):
        self.initEve()
        self.initGoonFleet()
        self.initJabberzac()
        
    def initJabberzac(self):
        #self.addOnJoin(['.*'],self.onjoin_christmas)
        None
        
    def onjoin_christmas(self, pres):
        return self.lang.ugettext('Merry Christmas')+' '+pres.getFrom().getResource()
    
class MarkovBot (Jabberzac):
    debugMode = False

    def initBot(self):
        random.seed()
        now = time.time()
        
        self.allOps = []
        self.nextOp = None
        self.currentOp = None
        self.nextOpHasBeenSaid = False

        delay = random.randint(60*60*1, 60*60*4)
        self.nextTwitterUpdate = now + delay
        self.nextTwitterSearch = now + (delay * 12)

        print ("Next Tweet in: %d" % delay)

        self.markov_lock = threading.Lock()
        self.markov_randomWordBuffer = []
        self.markov_randomWordCondition = threading.Condition()
        randomWordThread = threading.Thread(target = self.markov_populateRandomWordBuffer)
        randomWordThread.setName('%s populate random word buffer thread'%self.channel)
        randomWordThread.setDaemon(True)
        randomWordThread.start()
        self.nextOpUpdate = 0
        self.chanceOfMarkov = 0.02
        self.isPowerHour = False
        self.powerHourTrigger = ""
        self.powerHourStarted = now
        self.addProcessor(self.processor_markov_learning_dungar)
        #self.addProcessor(self.processor_markov_manic_minute)
        #self.addLoop(self.loop_markov_manic_minute)
        self.addProcessor(self.processor_markov)

        self.repliedTweets = []
        self.tweetedLinks = []
        self.youtubes = []
        self.images = []
            
        self.addLoop(self.loop_twitterSearch)
        
        self.initEve()
        self.initGoonFleet()
        self.initJabberzac()
        if not self.debugMode:
            self.addServerLoop('twitter',self.loop_twitterUpdate)
            
        os.environ['TZ'] = 'UTC'
        time.tzset()
    
    def calcTimeLeft(self,end):
        t = time.time()
        if t > end:
            ret = "-"
            diff = t - end
        else:
            ret = ""
            diff = end - t
            
        if diff < 60:
            ret += str(diff) + " seconds"
        
        if diff > 86400:
            days = int(diff / 86400)
            diff = diff % 86400
            ret += str(days) + " days "
        
        if diff > 3600:
            hours = int(diff / 3600)
            diff = diff % 3600
            ret += str(hours) + " hrs "
        
        if diff > 60:
            mins = int(diff / 60)            
            ret += str(mins) + " mins"
        
        if ret == "-" or ret == "":
            ret = self.lang.ugettext("any second now")   
            
        return ret
    
    def loop_twitterUpdate(self):
        now = time.time()
        if self.nextTwitterUpdate <= now:
            rnd = random.random() 
            delay = 0
            if (rnd < 0.9): #short delay to next tweet
                delay = 60*random.randint(15, 120)
            else: #long delay to next tweet
                delay = 60*random.randint(4*60, 16*60)
            self.nextTwitterUpdate = now + delay
            #Let's update twitter!
            rnd = random.random()
            if rnd < 0.5:
                #New status
                word = self.markov_getRandomWord()
                status = self.getMarkov(word, 0)
                if status:
                    self.updateTwitter(status)
            elif rnd < 0.6:
                #Let's reply to a random person about something literally random
                word = self.markov_getRandomWord()
                entry = self.searchTwitterRandom(word)
                if entry:
                    if entry['status'] not in self.repliedTweets:
                        markov = self.getMarkov(word,0)
                        if markov:
                            status = "@%s %s" % (entry['author'],markov)
                            self.repliedTweets.append(entry['status'])
                            self.updateTwitter(status)
            elif rnd < 0.7 and len(self.youtubes) > 0:
                #Let's post a youtube linki
                rnd = random.random()
                index = int(math.floor(rnd * (len(self.youtubes)-1)))
                youtube = self.youtubes[index]
                url = "http://www.youtube.com/watch?v=%s" % (youtube)
                if url not in self.tweetedLinks:
                    self.tweetedLinks.append(url)
                    comment = self.getRandomYoutubeComment(youtube)
                    status = "%s %s" % (comment,url)
                    self.updateTwitter(status)
            elif rnd < 0.8 and len(self.images) > 0:
                #Let's post an image
                rnd = random.random()
                index = int(math.floor(rnd * (len(self.images)-1)))
                url = self.images[index]
                if url not in self.tweetedLinks:
                    self.tweetedLinks.append(url)
                    self.updateTwitter(url)
            else:
                #Let's reply to someone about eve!
                entry = self.searchTwitterRandom("#eveonline")
                if entry:
                    status = entry['status']
                    if status not in self.repliedTweets:
                        words = status.split(" ")
                        goodWords = []
                        for word in words:
                            if len(word) > 4 and not word.startswith("@") and not word.startswith("#"):
                                goodWords.append(word)
                        if len(goodWords) > 0:
                            index = int(math.floor(rnd * len(goodWords)))
                            theWord = goodWords[index]
                            markov = self.getMarkov(theWord,0)
                            if markov:
                                self.repliedTweets.append(entry['status'])
                                status = "@%s %s" % (entry['author'],markov)
                                self.updateTwitter(status)
                        

    def updateTwitter(self,status):
        print("Twitter: %s" % status)
#        data = urllib.urlencode({"status" : status.encode('utf-8')})
#        urllib.urlopen("http://dungarmatic:abutteamirite@twitter.com/statuses/update.xml", data)
#        twitterapi.PostUpdate(status)
                  
    def searchTwitter(self, query):
        if query:
            query = query.replace("#","%23") 
            url = "http://search.twitter.com/search.atom?q=" + query
            try:
                tweetstream = urllib2.urlopen(url)
            except urllib2.HTTPError:
                return None
            response = tweetstream.read()
            dom = xml.dom.minidom.parseString(response)       
            entries = dom.getElementsByTagName("entry")
            if(len(entries) > 0):
                data = []
                for entry in entries:
                    authorNodes = entry.getElementsByTagName("name")
                    if len(authorNodes) > 0:
                        authorNode = authorNodes[0]
                        author = authorNode.childNodes[0].data
                        s = author.partition(' ')
                        author = s[0]
                    else:
                        author = ""
                    titleNodes = entry.getElementsByTagName("title")
                    if len(titleNodes) > 0:
                        title = titleNodes[0]
                        status = title.childNodes[0].data
                    else:
                        status = ""
                    data.append({'author':author,'status':status})
                return data
            else:
                return None

    def searchTwitterRandom(self,query):
        #Searches twitter and returns a random result
        entries = self.searchTwitter(query)
        if entries:
            random.seed()
            rnd = random.random()
            index = int(math.floor(rnd * len(entries)))
            entry = entries[index]
            return entry
      
    def loop_twitterSearch(self):
        now = time.time()
        if self.nextTwitterSearch <= now:            
            delay = random.randint(1, 7*60*60*24)
            
            self.nextTwitterSearch = now + delay 
            
            query = "#fwp" 
            if query:      
                entry = self.searchTwitterRandom(query)     
                #Don't repeat dungar's own tweets
                if entry['author'] != 'dungarmatic':
                    return "%s (http://twitter.com/%s)" % (entry['status'],entry['author'])
                else:
                    return None
            else:
                return None
        else:
            return None

