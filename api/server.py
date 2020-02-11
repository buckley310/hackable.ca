#!/usr/bin/env python3

from itertools import groupby
from time import time
from secrets import token_hex
from flask import Flask, jsonify
from flask_cors import CORS
app = Flask(__name__)
CORS(app)


def all_challenges():
    return [{"category": "web",
             "title": "kiss",
             "points": 1,
             "solves": 999,
             "solved": False,
             "text": "find the flag"},

            {"category": "pwn",
             "title": "very verbose",
             "points": 0,
             "solves": 123,
             "solved": False,
             "text": "this is a test of a challenge with a really long description vvvvvvvvvvvvvvvvvvvvvvv<br>and manual line-breaks :)"},

            {"category": "web",
             "title": "user agent",
             "points": 4,
             "solves": 888,
             "solved": True,
             "text": "change the user-agent"},

            {"category": "pwn",
             "title": "too tall",
             "points": 0,
             "solves": 123,
             "solved": False,
             "text": "this<br>challenge<br>description<br>has<br>way<br>way<br>way<br>way<br>way<br>way<br>way<br>too<br>many<br>line<br>breaks"},

            {"category": "pwn",
             "title": "this has a long name",
             "points": 0,
             "solves": 123,
             "solved": False,
             "text": "abcd"}, ]


def without(unwanted):
    def fsub(x):
        x.pop(unwanted)
        return x
    return fsub


def all_challenges_grouped():
    return [
        {
            'title': category,
            'chals': list(map(without('category'), chals))
        }
        for category, chals
        in groupby(
            sorted(all_challenges(), key=lambda x: x['category']),
            key=lambda x: x['category']
        )
    ]


@app.route("/login", methods=['POST'])
def login():
    return jsonify({"ok": True, "sessionToken": token_hex()})


@app.route("/logout")
def logout():
    return jsonify({"ok": True})


@app.route("/userinfo")
def userinfo():
    return jsonify({"ok": True,
                    "username": "buckley310",
                    "email": "a@y.z",
                    "score": 307})


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
    return jsonify(all_challenges_grouped())


if __name__ == '__main__':
    app.run(host='0.0.0.0')
