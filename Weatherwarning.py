# -*- coding: cp1252 -*-
from HTMLParser import HTMLParser
import urllib
import urllib2
import twitter
import datetime
import time
import sys
import smtplib
from email.mime.text import MIMEText  

class MyHTMLParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.tag = False
        self.recording = 0
        self.data = ''
        self.logfile = 'weather_' + str(time.time()) + '.log'
        self.entries = []

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            for name, value in attrs:
                if name == 'class' and value.startswith('warndescription'):
                    self.tag = True
                    self.data += value[16:]
                    #print name, value
                    #print "Encountered the beginning of a %s tag" % tag 
        if self.tag:
            self.recording += 1

    def handle_endtag(self, tag):
        if self.tag:
            self.recording -= 1
            if self.recording == 0:
                self.tag = False
                self.data = self.data[:-1]
                self.entries.append(self.data)
                self.data = ''

    def handle_data(self, data):
        if self.tag:
            #data = data.replace('\n', '')
            #data = data.replace('  ', ' ')
            if len(data) > 0:
                self.data += data
                #print data

    def get_data(self):
        current_entries = self.entries
        self.entries = []
        return current_entries

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
            s += 'Weather warning tweeted\n'
        else:
            s += 'No weather warning tweeted\n'

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
        f.write(exception + '\n')
        f.close()

def get_credentials(path):
    f = open(path, 'r')
    for lines in f:
        line = lines.split(' ')
        return line

def send_mail(data, emails, url, sender_mail):
    level_translation = {'yellow' : 'Gelb',
                         'orange' : 'Orange',
                         'red' : 'Rot'}
    body = data.split('\n', 1)[1]
    body += "\n" + url
    level = level_translation[data.split('\n')[0]]
    for receiver in emails:
        msg = MIMEText(body)
        msg['Subject'] = 'ZAMG Wetterwarnung: Warnstufe %s' % level
        msg['From'] = sender_mail
        msg['To'] = receiver
        try:
            s = smtplib.SMTP('localhost')
            s.sendmail(sender_mail, receiver, msg.as_string())
            s.quit()
            print "Sent warning to", receiver
        except Exception, e:
            print "Could not send email to", receiver
            print type(e), e
            pass

args = sys.argv
if len(args) < 3:
    print 'USAGE: python Weatherwarning.py <sleep time> <path to user credentials> (optional:<comma seperated list of email addresses> optonal:<sender of email>)'
    exit(1)
print args
sleep_time = float(args[1])
path_to_key = args[2]
[consumer_key, consumer_secret, access_token_key, access_token_secret] = get_credentials(path_to_key)
api = twitter.Api(consumer_key, consumer_secret, access_token_key, access_token_secret)
mailing_list = []
sender ='weatherwarning@example.com'
try:
    mailing_list = args[3].split(',')
    sender = args[4]
except:
    pass

url = 'http://zamg.ac.at/warnmobil/index.php?type=w0&state=noe&district=Krems+%28Land%29'

keyword = 'district='
i = url.find(keyword) + len(keyword)
region = url[i:]
i = region.find('&')
if i > 0:
    region = region[:i]
region = urllib.unquote_plus(region)
#print region

last_data = ''
parser = MyHTMLParser()

while True:
    try:
        response = urllib2.urlopen(url)
        headers = response.info()
        data = response.read()
        
        parser.feed(data)
        entries = parser.get_data()
        short_url = parser.short_url(url)

        duplicate = False
        if entries == last_data:
            duplicate = True
        else:
            last_data = entries
        
        for d in entries:            
            now = datetime.datetime.now()
            date = now.strftime("%Y-%m-%d %H:%M")

            msg = '#ZAMG Warnung: #' + region + ':'
            tweet = False
            if not d.startswith('Keine Warnungen vorhanden.') and len(d) > 0:
                tweet = True
            
            # ignore warning type and add to message
            msg += d.split('\n', 1)[1]

            if tweet and not duplicate:
                send_mail(d, mailing_list, short_url, sender)
            else:
                tweet = False
                
            if (len(msg) + len(short_url)) > 140:
                 msg = parser.shorten_message(msg, short_url)
            else:
                msg += short_url
            
            tweeted_tweet = []
            if tweet and not duplicate:
                tweeted_tweet =  api.PostUpdate(msg)
                time.sleep(5)
            parser.log_summary(msg, date, tweet, duplicate, tweeted_tweet)
        
        time.sleep(sleep_time)
    except Exception, e:
        parser.log_exception(str(type(e)) + ":\t" + str(e))
        time.sleep(sleep_time)
        pass
