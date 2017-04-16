import os.path
from flask import Flask, request, render_template
from flask.ext.pymongo import PyMongo
from yahoo_finance import Share

from twitter_scrape import TwitterScraper
import feedparser

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
    return render_template('index.html')

    
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

@app.route('/stats/<info>', methods=['GET',])
def handle_company(info):
    abbr, name = info.split('_')
    toRet = get_stock_info(name, abbr)
    return render_template('company.html', abbr=abbr, price=toRet['price'],
                            change=toRet['change'], color=toRet['color'],
                            entries=toRet['entries'])

def get_stock_info(name, abbr):
    x = Share(abbr)
    x.refresh()
    price = x.get_price()
    change = x.get_percent_change()
    print(change[0] == '-')
    if change[0] == '-':
        color = '#B22222'
    else:
        color = '#006400'
    url = "https://news.google.com/news?q={0}&output=rss".format(name)
    feed = feedparser.parse(url)

    entries = []
    i = 0
    while i < len(feed.entries) and i < 7:
        title = feed.entries[i]['title']
        index = title.index('-')
        author = title[index + 2:]
        title = title[:index -1]
        link = feed.entries[i]['link']
        entries.append({'title': title, 'author': author, 'link': link})
        i += 1
    return {'price': price, 'change': change, 'color': color, 'entries': entries}

@app.before_first_request
def clean():
    mongo.db.companies.remove({})


if __name__ == '__main__':
    
    app.run(host='0.0.0.0')
