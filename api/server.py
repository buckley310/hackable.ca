#!/usr/bin/env python3

from motor.motor_asyncio import AsyncIOMotorClient
from itertools import groupby
from collections import defaultdict
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


async def get_challenge_scores():
    return defaultdict(int, [
        (x['title'], x['points'])
        async for x in db.challenges.find()
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
                                                         'solves': 1,
                                                         'username': 1, })
    u['score'] = sum(map(
        (await get_challenge_scores()).get,
        u['solves']
    ))
    return jsonify(u) if u else jsonify(False)


@app.route("/submitflag", methods=['POST'])
async def submitflag():
    username = await get_session_username()
    assert username
    args = await request.get_json(force=True)
    c = await db.challenges.find_one({'flag': args['flag']})
    if not c:
        return jsonify({'ok': False, 'msg': "Unknown flag."})

    if await db.users.find_one({'username': username, 'solves': c['title']}):
        return jsonify({'ok': False, 'msg': "You've already solved that one."})

    await db.users.update_one(
        {'username': username},
        {
            "$set": {"lastSolveTime": int(time())},
            "$push": {"solves": c['title']},
        })

    return jsonify({'ok': True, 'msg': 'Nice job!'})


@app.route("/scoreboard")
async def scoreboard():
    chals = await get_challenge_scores()
    board = defaultdict(lambda: 0)
    async for u in db.users.find():
        board[u['username']] = sum(map(chals.get, u['solves']))

    return jsonify(sorted(board.items(), key=lambda x: 0-x[1])[:10])


@app.route("/challenges")
async def challenges():
    username = await get_session_username()

    chals = defaultdict(list)
    async for chal in db.challenges.find({}, {'_id': 0, 'flag': 0}):
        chal['solves'] = (
            await db.users.count_documents({'solves': chal['title']}))
        chal['solved'] = bool(
            await db.users.find_one({'username': username,
                                     'solves': chal['title'], }))
        cat = chal['category']
        del chal['category']
        chals[cat].append(chal)

    return jsonify([{'title': x, 'chals': chals[x]} for x in chals.keys()])


if __name__ == '__main__':
    app.run(host='0.0.0.0')
