import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, send_file, request, abort

from summarizer import fileUploadSummarize

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

def getArticleName(articleid):
    name = "placeholder"
    return name

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.route("/")
@app.route("/<var>")
def home(var=""):
    if var in ["styles.css", "script.js", "landingpagestyles.css"]:
        return send_file("./Website/" + var)
    
    if var in ["", "home", "home.html", "index", "index.html"]: 
        var = "home.html"
        return render_template(var)
    
    if var in ["summarize"]:
        var = var + ".html"
        return render_template(var)

    try:
        id = int(var)
    except:
        abort(404)

    if id == None:
        abort(404)
    return render_template("article.html", articlename=getArticleName(id))
    
    

@app.route("/upload", methods=["POST"])
def upload():
    if len(session) == 0: 
        return "No user logged in"
    
    try:
        file = request.files['file']
    except:
        return "No File Provided"
    
    file = file.read().decode("utf-8")

    response = {
        "Description": fileUploadSummarize(file)
    }

    return response

if __name__ == "__main__":
    app.run(host="localhost", port=env.get("PORT", 3000)) #ssl_context='adhoc'