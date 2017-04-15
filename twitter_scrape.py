from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from twilio.rest import Client 
from pymongo import MongoClient

import json
import datetime


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
    def __init__(self, name):
        self.name = name

        self.vel = 0

        self.pos_thresh_hit = False
        self.neg_thresh_hit = False
        
        self.pos_thresh = 1
        self.neg_thresh = -1

        self.last = datetime.datetime(1, 1, 1, 1, 1, 1)

    def update(self, vs, time):
        timedelta = (time - self.last).total_seconds()
        self.last = time
        sentiment = vs['compound']
        incr = 0
        if sentiment >= 0.5:
            incr = vs['pos']
        elif sentiment <= -0.5:
            incr = vs['neg']
        if int(timedelta) == 0:
            timedelta = 1
        self.vel += incr / int(timedelta)
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
            msg = "Looks like {0} is {1} with a velocity of {2}".format(
                            self.name,
                            "doing quite well on Twitter" if mag == 1 else "is doing pretty poorly on Twitter",
                            str(self.vel)
                )
            for number in DATABASE['companies'].find_one({'company': self.name})['numbers']:
                message = CLIENT.messages.create(to=number, from_="+14403791566",
                                 body=msg)
            print("sent")

class StdOutListener(StreamListener):

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.analyzer = kwargs['analyzer']
        self.target = kwargs['target']
        self.history = []

    def on_status(self, status):
        text = status.text
        vs = self.analyzer.polarity_scores(text)
        self.target.update(vs, status.created_at)

    def on_error(self, status):
        print(status)

class TwitterScraper(object):
    def __init__(self, name):
        self.analyzer = SentimentIntensityAnalyzer()
        self.target = Target(name)
        self.stream = self.setup_auth()
        self.queries = self.generate_queries(self.target.name)
        
        self.stream.filter(track=self.queries, async=True)

    def setup_auth(self):
        
        l = StdOutListener(target=self.target, analyzer=self.analyzer)
        auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
        return Stream(auth, l)

    def generate_queries(self, name):
        with_s = name + 's'
        return [name, with_s]
