# -*- coding: cp1252 -*-
from HTMLParser import HTMLParser
import urllib
import urllib2
import twitter
import datetime
import time
import sys
from HTMLParser import HTMLParser  

class MyHTMLParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.tag = False
        self.recording = 0
        self.data = ''
        self.logfile = 'weather_' + str(time.time()) + '.log'

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            for name, value in attrs:
                if name == 'class' and value.startswith('warndescription'):
                    self.tag = True
                    #print name, value
                    #print "Encountered the beginning of a %s tag" % tag 
        if self.tag:
            self.recording += 1

    def handle_endtag(self, tag):
        if self.tag:
            self.recording -= 1
            if self.recording == 0:
                self.tag = False

    def handle_data(self, data):
        if self.tag:
            #data = data.replace('\n', '')
            #data = data.replace('  ', ' ')
            if len(data) > 0:
                self.data += data
                #print data

    def get_data(self):
        return self.data

    def short_url(self, url):
        f = urllib2.urlopen("http://tinyurl.com/api-create.php?url=%s" % url)
        try:
            result = f.read()
            return result
        finally:
            f.close()

    def shorten_message(self, message, url):
        short_message = ''
        i = 0
        while len(short_message) < 140 - (len(url) + 3):
            short_message += message[i]
            i = i + 1
        short_message += '.. ' + url
        return short_message

    def log_summary(self, message, date, warning, duplicate, tweet):
        s = ''
        s += '---------------\n'
        s += 'Tweet summary for ' + date + '\n'
        if warning:
            s += 'Weather warning\n'
        else:
            s += 'No weather warning\n'

        if duplicate:
            s += 'Duplicate\n'

        s += message + ' ' + str(len(message)) + '\n'
        s += str(tweet) + '\n'
        s += '---------------\n'
        f = open(self.logfile, 'a')
        f.write(s)
        f.close()

    def log_exception(self, exception):
        f = open(self.logfile, 'a')
        f.write(exception)
        f.close()

def get_credentials(path):
    f = open(path, 'r')
    for lines in f:
        line = lines.split(' ')
        return line

args = sys.argv
if len(args) != 3:
    print 'USAGE: python Wetterwarnung.py <sleep time> <path to user credentials>'
    exit(1)
print args
sleep_time = float(args[1])
path_to_key = args[2]
[consumer_key, consumer_secret, access_token_key, access_token_secret] = get_credentials(path_to_key)

url = 'http://zamg.ac.at/warnmobil/index.php?type=w0&state=noe&district=Krems+%28Land%29'

keyword = 'district='
i = url.find(keyword) + len(keyword)
region = url[i:]
i = region.find('&')
if i > 0:
    region = region[:i]
region = urllib.unquote_plus(region)
#print region

last_msg = ''
parser = MyHTMLParser()

while True:
    try:
        response = urllib2.urlopen(url)
        headers = response.info()
        data = response.read()
        
        parser.feed(data)
        d = parser.get_data()
        short_url = parser.short_url(url)
        #print result
        
        api = twitter.Api(consumer_key, consumer_secret, access_token_key, access_token_secret)

        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d %H:%M")

        msg = '#ZAMG Warnung: #' + region + ':'
        tweet = False
        if not d.startswith('Keine Warnungen vorhanden.') and len(d) > 0:
            tweet = True
        
        msg += d
        if tweet and msg != last_msg:
            last_msg = msg
        else:
            tweet = False
            

        if (len(msg) + len(short_url)) > 140:
             msg = parser.shorten_message(msg, short_url)
        else:
            msg += short_url

        duplicate = False
        if msg == last_msg:
            duplicate = True
        
        tweeted_tweet = []
        if tweet and msg != last_msg:
            tweeted_tweet =  api.PostUpdate(msg)

        parser.log_summary(msg, date, tweet, duplicate, tweeted_tweet)
        time.sleep(sleep_time)
    except Exception, e:
        parser.log_exception(e)
        time.sleep(sleep_time)
        pass
