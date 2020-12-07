import json
import os
import uuid

from decouple import config
from flask import Flask, redirect, request, session, url_for, render_template
from flask.json import jsonify
from requests_oauthlib import OAuth2Session

app = Flask(__name__)


# This information is obtained upon registration of a new todoist OAuth
# application here: https://todoist.com/

TODOIST_CLIENT_ID = config("TODOIST_CLIENT_ID")
TODOIST_CLIENT_SECRET = config("TODOIST_CLIENT_SECRET")

redirect_uri = "http://localhost:5000"
scope = ["task:add", "data:read", "data:read_write", "data:delete", "project:delete"]
# scope = ["data:read"]

authorization_base_url = "https://todoist.com/oauth/authorize"
token_url = "https://todoist.com/oauth/access_token"


@app.route("/")
def home():
    """
    Step 1: User Authorization.

    Redirect the user/resource owner to the OAuth provider (i.e. Todoist)
    using an URL with a few key OAuth parameters.
    """
    todoist = OAuth2Session(
        TODOIST_CLIENT_ID, redirect_uri=redirect_uri, scope=",".join(scope)
    )
    authorization_url, state = todoist.authorization_url(
        authorization_base_url,
    )
    # State is used to prevent CSRF, keep this for later.
    session["oauth_state"] = state
    return redirect(authorization_url)


# Step 2: User authorization, this happens on the provider.


@app.route("/callback", methods=["GET"])
def callback():
    """
    Step 3: Retrieving an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """
    todoist = OAuth2Session(TODOIST_CLIENT_ID, state=session["oauth_state"])
    token = todoist.fetch_token(
        token_url,
        client_secret=TODOIST_CLIENT_SECRET,
        authorization_response=request.url,
        include_client_id=True,
    )
    # lets save the token for future use
    session["oauth_token"] = token
    return redirect(url_for(".access_token"))


@app.route("/access-token", methods=["GET"])
def access_token():
    return jsonify(session["oauth_token"])


@app.route("/all-todo-resources", methods=["GET"])
def all_todo_resources():
    """Fetching a protected resource using an OAuth 2 token."""
    data = {
        "token": session["oauth_token"],
        "sync_token": "*",
        "resource_types": '["all"]',
    }
    todoist = OAuth2Session(TODOIST_CLIENT_ID, token=session["oauth_token"])
    response = todoist.post("https://api.todoist.com/sync/v8/sync", data=data).json()
    return jsonify(response)


@app.route("/add-project", methods=["GET", "POST"])
def add_project():
    """Fetching a protected resource using an OAuth 2 token."""
    if request.method == "GET":
        return render_template("add_project.html")
    else:
        project_name = request.form.get("project_name")
        commands = [
            {
                "type": "project_add",
                "temp_id": str(uuid.uuid4()),
                "uuid": str(uuid.uuid4()),
                "args": {"name": project_name},
            }
        ]
        data = {
            "commands": json.dumps(commands),
        }
        todoist = OAuth2Session(TODOIST_CLIENT_ID, token=session["oauth_token"])
        response = todoist.post(
            "https://api.todoist.com/sync/v8/sync", data=data
        ).json()
        return jsonify(response)


@app.route("/update-project", methods=["GET", "POST"])
def update_project():
    """Fetching a protected resource using an OAuth 2 token."""
    if request.method == "GET":
        data = {
            "token": session["oauth_token"],
            "sync_token": "*",
            "resource_types": '["projects"]',
        }
        todoist = OAuth2Session(TODOIST_CLIENT_ID, token=session["oauth_token"])
        projects = todoist.post(
            "https://api.todoist.com/sync/v8/sync", data=data
        ).json()
        return render_template("update_project.html", projects=projects.get("projects"))
    else:
        project_name = request.form.get("project_name")
        project_id = request.form.get("project_id")
        commands = [
            {
                "type": "project_update",
                "uuid": str(uuid.uuid4()),
                "args": {"id": project_id, "name": project_name},
            }
        ]
        data = {
            "commands": json.dumps(commands),
        }
        todoist = OAuth2Session(TODOIST_CLIENT_ID, token=session["oauth_token"])
        response = todoist.post(
            "https://api.todoist.com/sync/v8/sync", data=data
        ).json()
        return jsonify(response)


@app.route("/delete-project", methods=["GET", "POST"])
def delete_project():
    """Fetching a protected resource using an OAuth 2 token."""
    if request.method == "GET":
        data = {
            "token": session["oauth_token"],
            "sync_token": "*",
            "resource_types": '["projects"]',
        }
        todoist = OAuth2Session(TODOIST_CLIENT_ID, token=session["oauth_token"])
        projects = todoist.post(
            "https://api.todoist.com/sync/v8/sync", data=data
        ).json()
        return render_template("delete_project.html", projects=projects.get("projects"))
    else:
        project_id = request.form.get("project_id")
        commands = [
            {
                "type": "project_delete",
                "uuid": str(uuid.uuid4()),
                "args": {"id": project_id},
            }
        ]
        data = {
            "commands": json.dumps(commands),
        }
        todoist = OAuth2Session(TODOIST_CLIENT_ID, token=session["oauth_token"])
        response = todoist.post(
            "https://api.todoist.com/sync/v8/sync", data=data
        ).json()
        return jsonify(response)


if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    app.secret_key = os.urandom(24)
    app.run(debug=True)
