""" initial import of DungarMarkov, it don't work """


class DungarMarkov

    def markov_getPowerHourTrigger(self):
        now = time.time()
        maxTriggerAge = now - 60*60
        dbconn = MySQLdb.connect(host=dbhost, db=database, user=dbuser, passwd=dbpass)
        c = dbconn.cursor()
        c.execute('SELECT word2 FROM (SELECT DISTINCT word2 FROM markov WHERE created > %(maxage)s) AS markov_distinct ORDER BY rand() LIMIT 1', {'maxage': maxTriggerAge});
        rows = []
        for row in c.fetchall():
            rows.append(row)
        if len(rows) > 0:
            row = rows[0];
            word = row[0]
        else:
            word = 'buttes'
        dbconn.close()        
        return word
    
    def markov_getRandomEmoticon(self):
        word = 'buttes'
        dbconn = MySQLdb.connect(host=dbhost, db=database, user=dbuser, passwd=dbpass)
        try:
            c = dbconn.cursor()
            c.execute('SELECT word2 FROM (SELECT DISTINCT word2 FROM markov WHERE word2 LIKE \':%:\') AS markov_distinct ORDER BY rand() LIMIT 1');
            rows = []
            for row in c.fetchall():
                rows.append(row)
            if len(rows) > 0:
                row = rows[0];
                word = row[0]
        except:
            None
        dbconn.close()        
        return word

    def markov_populateRandomWordBuffer(self):
        '''Keep the random word buffer full'''
        buffer_size = 10
        while True:
            dbconn = MySQLdb.connect(host=dbhost, db=database, user=dbuser, passwd=dbpass)
            try:
                c = dbconn.cursor()
                c.execute('SELECT word2 FROM (SELECT DISTINCT word2 FROM markov) AS markov_distinct ORDER BY rand() LIMIT 1');
                rows = []
                for row in c.fetchall():
                    rows.append(row)
                if len(rows) > 0:
                    row = rows[0]
                    word = row[0]
                else:
                    return
            except:
                return
            finally:
                dbconn.close()
            self.markov_randomWordCondition.acquire()
            while len(self.markov_randomWordBuffer) >= buffer_size:
                self.markov_randomWordCondition.wait()
            self.markov_randomWordBuffer.append(word)
            self.markov_randomWordCondition.notify()
            self.markov_randomWordCondition.release()

    def markov_getRandomWord(self):
        '''Return a randomly selected word from the markov table'''
        self.markov_randomWordCondition.acquire()
        while len(self.markov_randomWordBuffer) == 0:
            self.markov_randomWordCondition.wait()
        word = self.markov_randomWordBuffer.pop(0)
        self.markov_randomWordCondition.notify()
        self.markov_randomWordCondition.release()
        return word
        
    def getMarkov(self, chosenWord, maxChainAge):
        result = ""
        dbconn = MySQLdb.connect(host=dbhost, db=database, user=dbuser, passwd=dbpass)
        try:
            c = dbconn.cursor()
            c.execute('SELECT word1,word2,word3 FROM markov WHERE word2 = %(word2)s AND created > %(maxage)s ORDER BY rand() LIMIT 1', {'word2': chosenWord, 'maxage': maxChainAge})
            rows = []
            for row in c.fetchall():
                rows.append(row)
            if len(rows) > 0:
                chosenRow = rows[0]
                result = chosenRow[1]
                last = chosenRow[1]
                secondLast = chosenRow[0]
                while chosenRow[0] != '':
                    result = chosenRow[0] + " " + result
                    c.execute('SELECT word1,word2,word3 FROM markov WHERE word2 = %(word2)s AND word3 = %(word3)s AND created > %(maxage)s ORDER BY rand() LIMIT 1', {'word2':chosenRow[0],'word3':chosenRow[1], 'maxage': maxChainAge})
                    prevrows = []
                    for prevrow in c.fetchall():
                        prevrows.append(prevrow)
                    chosenRow = prevrows[0]
                c.execute('SELECT word1,word2,word3 FROM markov WHERE word1 = %(word1)s AND word2 = %(word2)s AND created > %(maxage)s ORDER BY rand() LIMIT 1', {'word1': secondLast, 'word2':last, 'maxage': maxChainAge})
                nextrows = []
                for nextrow in c.fetchall():
                    nextrows.append(nextrow)
                chosenRow = nextrows[0]
                while chosenRow[2] != '':
                    result = result + " " + chosenRow[2]
                    c.execute('SELECT word1,word2,word3 FROM markov WHERE word1 = %(word1)s AND word2 = %(word2)s AND created > %(maxage)s ORDER BY rand() LIMIT 1', {'word1':chosenRow[1],'word2':chosenRow[2], 'maxage': maxChainAge})
                    nextrows = []
                    for nextrow in c.fetchall():
                        nextrows.append(nextrow)
                    chosenRow = nextrows[0]
        except Exception, e:
            print "Error while reading markov: ", e
            result = ''
        dbconn.close()
        try:
            return unicode(result, 'utf-8')
        except:
            return None
#        return result

    def processor_markov_manic_minute(self, mess):
        '''Start manic minutes and update stale trigger words'''
        if mess.getFrom().getResource() == self.resource:
            return
        message = mess.getBody().encode('utf-8')
        words = message.split()
        now = time.time()
        if len(words) == 0:
            return
        try:
            self.markov_lock.acquire()
            if self.powerHourTrigger == "" or self.powerHourStarted < now - 60*60:
                #change stale trigger words
                self.powerHourTrigger = self.markov_getPowerHourTrigger()
                #self.updateTwitter("The power hour trigger in "+self.channel+" is now "+self.powerHourTrigger)
                print("The power hour trigger in "+self.channel+" is now "+self.powerHourTrigger)

                self.powerHourStarted = now
                return

            if self.powerHourTrigger in words and not self.isPowerHour:
                #start a manic minute when trigger word is said
                self.powerHourStarted = now
                self.isPowerHour = True
                self.chanceOfMarkov = 0.8
                return mess.getFrom().getResource().encode('utf-8') + " "+self.lang.ugettext("just said")+" '"+unicode(self.powerHourTrigger, 'utf-8')+"' "+self.lang.ugettext("and triggered a %(name)s MANIC MINUTE") % {'name':self.resource.upper()}
        finally:
            self.markov_lock.release()

    def loop_markov_manic_minute(self):
        '''Respond during and end manic minutes'''
        now = time.time()
        maxChainAge = now - 30*24*60*60
        if not self.markov_lock.acquire(False):
            return
        try:
            if self.isPowerHour:
                if now > self.powerHourStarted + 60:                
                    self.powerHourTrigger = self.markov_getPowerHourTrigger()
                    print("The power hour trigger in "+self.channel+" is now "+self.powerHourTrigger)
                    self.isPowerHour = False
                    self.chanceOfMarkov = 0.02
                    return self.lang.ugettext("The %(name)s manic minute is over.") % {'name':self.resource}
            if self.isPowerHour and self.timeSinceLastMessage > 10:
                return self.getMarkov(self.markov_getRandomWord(), maxChainAge)
        finally:
            self.markov_lock.release()
            

    def processor_markov(self, mess):
        '''Respond with a markov'''
        if mess.getFrom().getResource() == self.resource:
            return
        message = mess.getBody().encode('utf-8')
        words = message.split()
        if len(words) == 0:
            return
                    
        for i in range(1,len(self.history)):
            try:
                if message == self.history[i].encode('utf-8'):
                    return
            except UnicodeDecodeError, e:
                if hasattr(e, 'code'):
                    print 'We failed with error code - %s.' % e.code
                elif hasattr(e, 'reason'):
                    print "The error object has the following 'reason' attribute :"
                    print e.reason
                return
        now = time.time()
        maxChainAge = now - 30*24*60*60
        chosenWord = words[random.randint(0, len(words)-1)]
        if random.random() < self.chanceOfMarkov:
            return self.getMarkov(chosenWord, maxChainAge)

    def processor_markov_learning_dungar(self, mess):
        '''Write everything that is said into the markov database'''
        if mess.getFrom().getResource() == self.resource:
            return
        message = mess.getBody().encode('utf-8')
        words = message.split()
        if len(words) <= 1:
            return
        now = time.time()
                    
        for i in range(1,len(self.history)):
            try:
                if message == self.history[i].encode('utf-8'):
                    return
            except UnicodeDecodeError, e:
                if hasattr(e, 'code'):
                    print 'We failed with error code - %s.' % e.code
                elif hasattr(e, 'reason'):
                    print "The error object has the following 'reason' attribute :"
                    print e.reason
                return

        counts = {}
        is_spam = False
        for word in words:
            if not word in counts:
                counts[word] = 1
            else:
                counts[word] = counts[word]+1
        last_value = None
        most_common_val = 0
        highest_count = 0
        highest_val = 0
        vals = counts.values()
        vals.sort()
        for value in vals:
            if value != last_value:
                count_this_val = 1
            else:
                count_this_val = count_this_val + 1
            if count_this_val > highest_count:
                highest_count = count_this_val
                most_common_val = value
            if value > highest_val:
                highest_val = value
            last_value = value
        if most_common_val != 1:
            print "spam check 1"
            is_spam = True
        if highest_val  > 1 + len(words)/4:
            print "spam check 2"
            is_spam = True
        if sum(counts.values())/len(counts.values()) >= 2:
            print "spam check 3"
            is_spam = True
                
        if is_spam:
            print "SPAM DETECTED: "+message
            return

        dbconn = MySQLdb.connect(host=dbhost, db=database, user=dbuser, passwd=dbpass)
        try:
            i=0
            while i<len(words):
                insert = {}
                insert['now']=now
                if i==0:
                    insert['word1']=u''
                else:
                    insert['word1']=unicode(words[i-1], 'utf-8')
                insert['word2']=unicode(words[i], 'utf-8')
                if i+1 > len(words)-1:
                    insert['word3']=u''
                else:
                    insert['word3']=unicode(words[i+1], 'utf-8')
                dbconn.cursor().execute('INSERT INTO markov (word1,word2,word3,created) VALUES (%(word1)s,%(word2)s,%(word3)s,%(now)s)', insert)
                i=i+1
            dbconn.commit()
        except Exception, e:
            self.log("Error while writing to db in processor_markov_learning_dungar: "+str(e))
        dbconn.close()
