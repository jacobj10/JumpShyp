import os.path
from flask import Flask, Response, request
from flask.ext.pymongo import PyMongo

from twitter_scrape import TwitterScraper

app = Flask(__name__, static_url_path='')
mongo = PyMongo(app)

def root_dir():
    return os.path.abspath(os.path.dirname(__file__))


def get_file(filename):
    try:
        src = os.path.join(root_dir(), filename)
        return open(src).read()
    except IOError as exc:
        return str(exc)

@app.route('/')
def main():
    content = get_file('index.html')
    return Response(content, mimetype='text/html')
    
@app.route('/action_submit/', methods=['POST',])
def handle_submit():
    company = request.form['company']
    number = request.form['number']
    abb = request.form['stock']
    if mongo.db.companies.find_one({'company': company}) == None:
        mongo.db.companies.insert_one({'company':company, 'numbers': [number,]})
        TwitterScraper(company, abb)
        return "Updated Company and Number!"
    else:
        print(mongo.db.companies.find_one_and_update({'company': company}, {'$push': {'numbers': number}}))
        return "Updated Number!"

@app.before_first_request
def clean():
    mongo.db.companies.remove({})
