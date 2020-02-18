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
    def challengeSolveCount(chal):
        chal['solves'] = db['solves'].count_documents(
            {'challenge': chal['title']})
        return chal

    def checkIfUserSolved(chal):
        chal['solved'] = bool(
            db['solves'].find_one({'username': username,
                                   'challenge': chal['title'], }))
        return chal

    return map(checkIfUserSolved,
               map(challengeSolveCount,
                   db['challenges'].find({}, {'_id': 0, 'flag': 0})))


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


def getUserScore(username):
    return sum([
        db['challenges'].find_one({'title': x['challenge']})['points']
        for x in db['solves'].find({'username': username})
    ])


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
    u = db['users'].find_one({'username': username}, {'_id': 0,
                                                      'email': 1,
                                                      'username': 1, })
    u['score'] = getUserScore(u['username'])
    return jsonify(u) if u else jsonify(False)


@app.route("/submitflag", methods=['POST'])
def submitflag():
    username = get_session_username()
    assert username
    args = request.get_json(force=True)
    c = db.challenges.find_one({'flag': args['flag']})
    if not c:
        return jsonify({'ok': False, 'msg': "Unknown flag."})

    entry = {'username': username, 'challenge': c['title']}

    if db['solves'].find_one(entry):
        return jsonify({'ok': False, 'msg': "You've already solved that one."})

    db['solves'].insert_one(entry)

    db['users'].update_one({'username': username},
                           {"$set": {"lastSolveTime": int(time())}})

    return jsonify({'ok': True, 'msg': 'Nice job!'})


@app.route("/scoreboard")
def scoreboard():
    return jsonify([
        [x[2], x[0]] for x in
        sorted([
            [
                getUserScore(u['username']),
                0-u['lastSolveTime'],
                u['username'],
            ]
            for u in db['users'].find()
        ], reverse=True)
    ])


@app.route("/challenges")
def challenges():
    return jsonify(all_challenges_grouped(get_session_username()))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
