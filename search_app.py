from flask import Flask, request
from markupsafe import escape
from flask import render_template
from elasticsearch import Elasticsearch
import math

ELASTIC_PASSWORD = ""

es = Elasticsearch("https://localhost:9200", http_auth=("elastic", ELASTIC_PASSWORD), verify_certs=False)
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def check_info(data):
    if(data == "null" or data == "This edition doesn't have a description yet. Can you add one?"):
        return "undefined"
    elif(data == '2x'):
        return "./static/img/noimg.png"
    else:
        return data

app.jinja_env.globals.update(check_info = check_info) 


@app.route('/search')
def search():

    page_size = 10
    keyword = request.args.get('keyword')
    if request.args.get('page'):
        page_no = int(request.args.get('page'))
    else:
        page_no = 1

    body = {
        'size': page_size,
        'from': page_size * (page_no-1),
        'query': {
            'multi_match': {
                'query': keyword,
                'type' : "most_fields",
                'fuzziness': "auto",
                'fuzzy_transpositions': "true",
                'slop': 12,
                'auto_generate_synonyms_phrase_query': "true",
                'zero_terms_query':"none",
                'fields': ['title', 'author','description','public_date']
            }
        }
    }

    res = es.search(index='books',body=body)
    value = res['hits']['total']['value']
    # calcuate last page
    last_page = 0
    for i in range(value):
        if(i < page_no * 10):
            last_page+=1

    # calculate first page
    first_page = page_no - 1
    first_page = (first_page*page_size)+1

    hits = [{'title': doc['_source']['title'], 'author': doc['_source']['author'], 
    'public_date': doc['_source']['public_date'],'image-src': doc['_source']['image-src'],
    'description':doc['_source']['description'],'web-scraper-start-url':doc['_source']['web-scraper-start-url'],
    'rating':doc['_source']['rating'],'score':doc['_score']} for doc in res['hits']['hits']]
    page_total = math.ceil(res['hits']['total']['value']/page_size)
    return render_template('search.html',keyword=keyword, hits=hits, page_no=page_no, page_total=page_total,value=value,last_page=last_page,first_page=first_page)