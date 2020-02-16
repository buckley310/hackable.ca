#!/usr/bin/env python3

import pymongo

db = pymongo.MongoClient('mongodb://127.0.0.1:27017')['hca']

db['challenges'].insert_many([
    {"title": "kiss", "category": "web", "points": 56, "flag": "a1",
     "text": "find the flag"},

    {"title": "very verbose", "category": "pwn", "points": 67, "flag": "a2",
     "text": "this is a test of a challenge with a really long description vvvvvvvvvvvvvvvvvvvvvvv<br>and manual line-breaks :)"},

    {"title": "user agent", "category": "web", "points": 78, "flag": "a3",
     "text": "change the user-agent"},

    {"title": "too tall", "category": "pwn", "points": 89, "flag": "a4",
     "text": "this<br>challenge<br>description<br>has<br>way<br>way<br>way<br>way<br>way<br>way<br>way<br>too<br>many<br>line<br>breaks"},

    {"title": "this has a long name", "category": "pwn", "points": 90, "flag": "a5",
     "text": "abcd"},
])

db['users'].insert_many([
    {"username": "user1", "email": "user1@example.org", "lastSolveTime": 0},
    {"username": "user2", "email": "user2@example.org", "lastSolveTime": 0},
])
