import json

from flask import jsonify, session
from requests_oauthlib import OAuth2Session

from settings import TODOIST_CLIENT_ID, TODOIST_CLIENT_SECRET


def get_resources(resource_types: list = ["all"]):
    data = {
        "token": session["oauth_token"],
        "sync_token": "*",
        "resource_types": json.dumps(resource_types),
    }
    todoist = OAuth2Session(TODOIST_CLIENT_ID, token=session["oauth_token"])
    resources = todoist.post("https://api.todoist.com/sync/v8/sync", data=data).json()
    return resources


def process_commands(commands: dict):
    data = {
        "commands": json.dumps(commands),
    }
    todoist = OAuth2Session(TODOIST_CLIENT_ID, token=session["oauth_token"])
    response = todoist.post("https://api.todoist.com/sync/v8/sync", data=data).json()
    return jsonify(response)
