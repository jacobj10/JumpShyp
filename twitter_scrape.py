from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

import json

CONSUMER_KEY = "NOPE"
CONSUMER_SECRET = "NOPE"
ACCESS_TOKEN = "NOPE"
ACCESS_SECRET = "NOPE"

class StdOutListener(StreamListener):

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.analyzer = kwargs['analyzer']
        self.name = kwargs['track_name']

    def on_status(self, status):
        text = status.text
        vs = self.analyzer.polarity_scores(text)
        print(text + " " + str(vs))

    def on_error(self, status):
        print(status)

class TwitterScraper(object):
    def __init__(self, name):
        self.analyzer = SentimentIntensityAnalyzer()
        self.name = name
        self.stream = self.setup_auth()
        self.queries = self.generate_queries(self.name)
        
        self.stream.filter(track=self.queries, async=True)

    def setup_auth(self):
        
        l = StdOutListener(track_name=self.name, analyzer=self.analyzer)
        auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
        return Stream(auth, l)

    def generate_queries(self, name):
        with_s = name + 's'
        return [name, with_s]

TwitterScraper('hax333r')
