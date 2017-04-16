from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from textblob import TextBlob
from twilio.rest import Client 
from pymongo import MongoClient

import json
import datetime
import re

CONSUMER_KEY = "nah"
CONSUMER_SECRET = "nah"
ACCESS_TOKEN = "nah-nah"
ACCESS_SECRET = "nah"

TWILIO_ACCOUNT = "nah"
TWILIO_TOKEN = "nah"

CLIENT = Client(TWILIO_ACCOUNT, TWILIO_TOKEN)
MONGO_CLIENT = MongoClient('localhost', 27017)
DATABASE = MONGO_CLIENT['app']

class Target(object):
    def __init__(self, name, abb):
        self.name = name
        self.abbr = abb

        self.vel = 0

        self.pos_thresh_hit = False
        self.neg_thresh_hit = False
        
        self.pos_thresh = 2
        self.neg_thresh = -2

        self.last = datetime.datetime(1, 1, 1, 1, 1, 1)

    def update(self, polarity, time):
        timedelta = (time - self.last).total_seconds()
        self.last = time
        if int(timedelta) == 0:
            timedelta = 1
        inc = 0
        if polarity >= 0.25:
            inc = 1
        elif polarity <= -0.25:
            inc = -1
        self.vel += polarity / (int(timedelta))
        print(self.vel)
        if (self.vel >= self.pos_thresh and not self.pos_thresh_hit):
            self.send_message(1)
            self.pos_thresh_hit = True
        elif (self.vel <= self.neg_thresh and not self.neg_thresh_hit):
            self.send_message(-1)
            self.neg_thresh_hit = True
        if self.vel < self.pos_thresh:
            self.pos_thresh_hit = False
        if self.vel  > self.neg_thresh:
            self.neg_thresh_hit = False

    def send_message(self, mag):
        status = ""
        if mag == 1:
            status = "doing quite well on Twitter" 
        elif mag == -1:
            status = "doing pretty poorly on Twitter"
        url = "http://172.20.44.75:5000/stats/{0}".format(self.abbr + "_" + self.name)
        url = ''.join(url.split(' '))
        msg = "Looks like {0} is {1} with a velocity of {2}.\nSee {3} for more...".format(
                        self.name.upper(),
                        status,
                        "{0:.2f}".format(round(self.vel,2)),
                        url
            )
        for number in DATABASE['companies'].find_one({'company': self.name})['numbers']:
            message = CLIENT.messages.create(to=number, from_="+14403791566",
                             body=msg)

class StdOutListener(StreamListener):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.target = kwargs['target']

    def on_status(self, status):
        text = self.clean_status(status.text)
        polarity = TextBlob(text).sentiment.polarity
        self.target.update(polarity, status.created_at)

    def clean_status(self, status):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", status).split())

    def on_error(self, status):
        print(status)

class TwitterScraper(object):
    def __init__(self, name, abb):
        self.target = Target(name, abb)
        self.stream = self.setup_auth()
        self.queries = self.generate_queries(self.target.name)
        
        self.stream.filter(track=self.queries, async=True)

    def setup_auth(self):
        
        l = StdOutListener(target=self.target)
        auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
        return Stream(auth, l)

    def generate_queries(self, name):
        with_s = name + 's'
        return [name, with_s]
