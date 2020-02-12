#!/usr/bin/env python3

from pymongo import MongoClient
from itertools import groupby
from time import time
from secrets import token_hex
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
db = MongoClient('mongodb://127.0.0.1:27017')['hca']


def get_session_username():
    if 'X-Sesid' in request.headers:
        r = db['sessions'].find_one({'sesid': request.headers['X-Sesid']})
        if r:
            return r['username']
    return None


def all_challenges(username):
    def solve_count(chal):
        chal['solves'] = db['solves'].count_documents(
            {'challenge': chal['title']}
        )
        return chal

    def user_solved(chal):
        chal['solved'] = bool(
            db['solves'].find_one({'username': username,
                                   'challenge': chal['title']
                                   }))
        return chal

    return map(user_solved,
               map(solve_count,
                   db['challenges'].find({}, {'_id': 0,
                                              'text': 1,
                                              'title': 1,
                                              'points': 1,
                                              'category': 1, })))


def all_challenges_grouped(username):
    def getCat(x):
        return x['category']

    def removeCat(x):
        del x['category']
        return x

    return [
        {'title': category, 'chals': list(map(removeCat, chals))}
        for category, chals
        in groupby(sorted(all_challenges(username), key=getCat), key=getCat)
    ]


@app.route("/login", methods=['POST'])
def login():
    args = request.get_json(force=True)
    if not db['users'].find_one({'username': args['username']}):
        return jsonify(False)
    t = token_hex()
    db['sessions'].insert_one({'username': args['username'], 'sesid': t})
    return jsonify({"sesid": t})


@app.route("/logout")
def logout():
    return jsonify({'ok': True})


@app.route("/userinfo")
def userinfo():
    username = get_session_username()
    if not username:
        return jsonify(False)
    return jsonify({"username": username,
                    "email": "user@example.org",
                    "score": 1337})


@app.route("/scoreboard")
def scoreboard():
    return jsonify([
        ["21",  "buckley310",      "307"],
        ["593", "GabrieleDuchi",   "307"],
        ["32",  "Xio",             "277"],
        ["45",  "veganjay",        "277"],
        ["67",  "dodo",            "277"],
        ["47",  "hueh",            "269"],
        ["237", "FeDEX",           "233"],
        ["138", "viki",            "232"],
        ["254", "quicksilver0x01", "217"],
        ["139", "c_u_r_l_y",       "192"]
    ])


@app.route("/challenges")
def challenges():
    return jsonify(all_challenges_grouped(get_session_username()))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
