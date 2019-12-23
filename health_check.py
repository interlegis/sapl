from flask import Flask
import requests
import psycopg2
import json
from sapl.settings import DATABASES, USE_SOLR, SOLR_URL


app = Flask(__name__)


@app.route('/health')
def health():
    try:
        db = DATABASES['default']
        conn = psycopg2.connect(host=db['HOST'],
                                user=db['USER'],
                                password=db['PASSWORD'],
                                database=db['NAME'],
                                port=db['PORT'])
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        resp = {'DATABASE': 'OK'}
    except Exception as e:
        resp = {'DATABASE': 'ERROR'}
    finally:
        if cursor:
            cursor.close()
            conn.close()

    if USE_SOLR:
        r = requests.get(SOLR_URL)
        if r.ok:
            resp.update({'SEARCH_ENGINE': 'OK'})
        else:
            resp.update({'SEARCH_ENGINE': 'ERROR'})

    else:
        resp.update({'SEARCH_ENGINE': 'NOT_ENABLED'})

    return json.dumps(resp)


@app.route('/ping')
def ping():
    return "pong"


if __name__ == '__main__':
    app.run()