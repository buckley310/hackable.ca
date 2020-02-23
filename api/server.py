#!/usr/bin/env python3

from motor.motor_asyncio import AsyncIOMotorClient
from itertools import groupby
from time import time
from secrets import token_hex
from quart import Quart, jsonify, request
from quart_cors import cors

app = Quart(__name__)
cors(app)


@app.before_first_request
async def start_db():
    global db
    db = AsyncIOMotorClient('mongodb://127.0.0.1:27017')['hca']


async def get_session_username():
    if 'X-Sesid' in request.headers:
        r = await db.sessions.find_one({'sesid': request.headers['X-Sesid']})
        if r:
            return r['username']
    return None


async def all_challenges(username):
    chals = await db.challenges.find(
        {}, {'_id': 0, 'flag': 0}
    ).to_list(length=None)

    for c in chals:
        c['solves'] = await db.solves.count_documents(
            {'challenge': c['title']})

    for c in chals:
        c['solved'] = bool(
            await db.solves.find_one({'username': username,
                                      'challenge': c['title'], }))
    return chals


async def all_challenges_grouped(username):
    def getCat(x):
        return x['category']

    def removeCat(x):
        del x['category']
        return x

    return [
        {'title': category, 'chals': list(map(removeCat, chals))}
        for category, chals in
        groupby(sorted(await all_challenges(username), key=getCat), key=getCat)
    ]


async def getUserScore(username):
    return sum([
        (await db.challenges.find_one({'title': x['challenge']}))['points']
        for x
        in await db.solves.find({'username': username}).to_list(length=None)
    ])


@app.route("/login", methods=['POST'])
async def login():
    args = await request.get_json(force=True)
    if not await db.users.find_one({'username': args['username']}):
        return jsonify(False)
    t = token_hex()
    await db.sessions.insert_one({'username': args['username'], 'sesid': t})
    return jsonify({"sesid": t})


@app.route("/logout")
async def logout():
    sesid = request.headers['X-Sesid']
    return jsonify({
        'ok': bool(
            (await db.sessions.delete_one({'sesid': sesid})).deleted_count
        )
    })


@app.route("/userinfo")
async def userinfo():
    username = await get_session_username()
    if not username:
        return jsonify(False)
    u = await db.users.find_one({'username': username}, {'_id': 0,
                                                         'email': 1,
                                                         'username': 1, })
    u['score'] = await getUserScore(u['username'])
    return jsonify(u) if u else jsonify(False)


@app.route("/submitflag", methods=['POST'])
async def submitflag():
    username = await get_session_username()
    assert username
    args = request.get_json(force=True)
    c = await db.challenges.find_one({'flag': args['flag']})
    if not c:
        return jsonify({'ok': False, 'msg': "Unknown flag."})

    entry = {'username': username, 'challenge': c['title']}

    if await db.solves.find_one(entry):
        return jsonify({'ok': False, 'msg': "You've already solved that one."})

    await db.solves.insert_one(entry)

    await db.users.update_one({'username': username},
                              {"$set": {"lastSolveTime": int(time())}})

    return jsonify({'ok': True, 'msg': 'Nice job!'})


@app.route("/scoreboard")
async def scoreboard():
    return jsonify([
        [x[2], x[0]] for x in
        sorted([
            [
                await getUserScore(u['username']),
                0-u['lastSolveTime'],
                u['username'],
            ]
            for u in await db.users.find().to_list(length=None)
        ], reverse=True)
    ])


@app.route("/challenges")
async def challenges():
    return jsonify(await all_challenges_grouped(await get_session_username()))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
