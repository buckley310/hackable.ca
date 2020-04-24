#!/usr/bin/env python3

import os
import jwt
import bcrypt
import bisect
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
from collections import deque, Counter
from time import time
from quart import Quart, jsonify, request
from quart_cors import cors
from threading import Lock

app = Quart(__name__)
cors(app)
rateLimit = deque(maxlen=64)
jwt_secret = os.urandom(32)
statsLock = Lock()


@app.before_first_request
async def start_db():
    global db
    db = AsyncIOMotorClient('mongodb://127.0.0.1:27017')['hca']
    await calcStats()


def checkStr(*argv):
    for s in argv:
        assert isinstance(s, str)
        assert len(s)


async def calcStats():
    global solveCounts
    global scoreboard

    print("RECALCULATING STATS")

    with statsLock:
        solveCounts = dict([
            (
                str(chal['_id']),
                await db.users.count_documents({'solves': str(chal['_id'])})
            )
            async for chal in db.challenges.find()
        ])

        cscores = await get_challenge_scores()
        board = []
        async for u in db.users.find():
            score = sum(cscores.get(x, 0) for x in u['solves'])
            bisect.insort(board, (-score, u['lastSolveTime'], u['username']))
            while len(board) > 10 and board[-1][0] != board[-2][0]:
                board.pop()
        scoreboard = [(n, -s) for s, _, n in board]


async def get_user_record():
    try:
        auth = jwt.decode(request.headers['X-Sesid'],
                          jwt_secret,
                          algorithms=['HS256'])
    except:
        return None
    return await db.users.find_one({'_id': ObjectId(auth['userid'])})


async def get_challenge_scores():
    return dict([
        (str(x['_id']), x['points'])
        async for x in db.challenges.find()
    ])


@app.route("/login", methods=['POST'])
async def login():
    args = await request.get_json()
    checkStr(args['username'], args['password'])

    # block brute force \/
    stamp = int(time()/10)
    rateLimit.append((stamp, args['username']))
    rateLimit.append((stamp, request.remote_addr))
    limitStats = Counter(rateLimit)
    if (limitStats[(stamp, args['username'])] > 5 or
            limitStats[(stamp, request.remote_addr)] > 5):
        return jsonify({'txt': 'Slow down, jeez'})
    # block brute force /\

    u = await db.users.find_one({'username': args['username']})

    if not u:
        bcrypt.hashpw(b'no timing attacks', bcrypt.gensalt())
        return jsonify({'txt': 'Incorrect'})

    if not bcrypt.checkpw(args['password'].encode('utf8'),
                          u['password'].encode('utf8')):
        return jsonify({'txt': 'Incorrect'})

    token = jwt.encode({'userid': str(u['_id'])},
                       jwt_secret,
                       algorithm='HS256')

    return jsonify({"sesid": token.decode('utf8')})


@app.route("/userinfo")
async def userinfo():
    u = await get_user_record()
    if not u:
        return jsonify(False)
    u['_id'] = str(u['_id'])
    del u['password']
    cscores = await get_challenge_scores()
    u['score'] = sum(cscores.get(x, 0) for x in u['solves'])
    return jsonify(u)


@app.route("/setpassword", methods=['POST'])
async def setpassword():
    u = await get_user_record()
    assert u

    args = await request.get_json()
    checkStr(args['oldpass'], args['newpass'])

    if not bcrypt.checkpw(args['oldpass'].encode('utf8'),
                          u['password'].encode('utf8')):
        return jsonify({'ok': False, 'txt': 'Incorrect old password'})

    newhash = bcrypt.hashpw(args['newpass'].encode('utf8'), bcrypt.gensalt())
    await db.users.update_one(
        {'_id': u['_id']},
        {"$set": {"password": newhash.decode('utf8')}}
    )
    return jsonify({'ok': True})


@app.route("/setemail", methods=['POST'])
async def setemail():
    u = await get_user_record()
    assert u

    args = await request.get_json()
    checkStr(args['password'], args['email'])

    if not bcrypt.checkpw(args['password'].encode('utf8'),
                          u['password'].encode('utf8')):
        return jsonify({'ok': False, 'txt': 'Incorrect password'})

    await db.users.update_one(
        {'_id': u['_id']},
        {"$set": {"email": args['email']}}
    )
    return jsonify({'ok': True})


@app.route("/submitflag", methods=['POST'])
async def submitflag():
    u = await get_user_record()
    assert u

    args = await request.get_json()
    checkStr(args['flag'])

    c = await db.challenges.find_one({'flag': args['flag']})
    if not c:
        return jsonify({'ok': False, 'msg': "Unknown flag."})

    if str(c['_id']) in u['solves']:
        return jsonify({'ok': False, 'msg': "You've already solved that one."})

    await db.users.update_one(
        {'_id': u['_id']},
        {
            "$set": {"lastSolveTime": int(time())},
            "$push": {"solves": str(c['_id'])},
        })

    await calcStats()
    return jsonify({'ok': True, 'msg': 'Nice job!'})


@app.route("/scoreboard")
async def getScoreboard():
    return jsonify(scoreboard)


@app.route("/newaccount", methods=['POST'])
async def newaccount():
    args = await request.get_json()
    checkStr(args['username'], args['password'])

    if len(args['username']) > 32:
        return jsonify({'ok': False, 'txt': 'Shorter name please'})

    if await db.users.find_one({'username': args['username']}):
        return jsonify({'ok': False, 'txt': 'Username already taken'})

    hashed = bcrypt.hashpw(args['password'].encode('utf8'), bcrypt.gensalt())

    db.users.insert_one({
        'username': args['username'],
        'password': hashed.decode('utf8'),
        'lastSolveTime': 0, 'solves': [],
    })
    return jsonify({'ok': True})


@app.route("/challenges")
async def challenges():
    u = await get_user_record()
    chals = []
    async for chal in db.challenges.find({}, {'flag': 0}):
        chal['solves'] = solveCounts.get(str(chal['_id']), 0)
        chal['solved'] = (str(chal['_id']) in u['solves']) if u else False
        del chal['_id']
        chals.append(chal)
    return jsonify(chals)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
