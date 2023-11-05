import os, json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, send_file, request, abort
from flask_sqlalchemy import SQLAlchemy

from summarizer import fileUploadSummarize

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_res.db'
app.secret_key = env.get("APP_SECRET_KEY")

db = SQLAlchemy(app)

class ViewCount(db.Model):
    ArtId = db.Column(db.Integer, primary_key=True)
    VwCnt = db.Column(db.Integer)

class Ratings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Text)
    ArtId = db.Column(db.Text)
    Biased = db.Column(db.Integer)
    Important = db.Column(db.Integer)
    Opinion = db.Column(db.Integer)

idmap = {
    "hb59": 1,
    "hb60": 2,
    "hb61": 3,
    "hb62": 4,
    "hb63": 5,
    "sb58": 6,
    "sb59": 7,
    "sb61": 8,
    "sb62": 9,
    "sb63": 10
}

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

# begin routes for Auth0
# -----------------------
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
# -----------------------


# main route for navigation
@app.route("/")
@app.route("/<var>")
def home(var: str=""):
    if var in ["styles.css", "script.js", "landingpagestyles.css", "user_interaction.js"]:
        return send_file("./Website/" + var)
    
    if var in ["", "home", "home.html", "index", "index.html"]: 
        var = "home.html"
        return render_template(var)
    
    if var in ["summarize"]:
        var = var + ".html"
        return render_template(var)

    t = var.lower().replace(' ', '')
    if t in os.listdir("./summaries"):
        article_id = idmap[t]
        viewcount = ViewCount.query.filter_by(ArtId=article_id).first()
    
        skip = False
        if viewcount is None:
            new_rating = ViewCount(
                VwCnt=1, 
                ArtId=article_id, 
            )
        else:
            viewcount.VwCnt += 1
            skip = True
        
        if not skip: 
            db.session.add(new_rating)
        db.session.commit()
        
        with open("./summaries/" + t + "/summary.txt") as file:
            summary = file.read()

        # Calculate the totals for biases and importance across all users
        ratings_for_art_id = Ratings.query.filter_by(ArtId=article_id).all()

        # Calculate the totals for biases and importance for the specified ArtId
        total_bias = sum(rating.Biased for rating in ratings_for_art_id)
        total_importance = sum(rating.Important for rating in ratings_for_art_id)

        # Display the totals
        importance = f"Importance Rating: {total_importance}"
        bias = f"Bias Rating: {total_bias}"

        return render_template("article.html", articlename=var, title=var, summary=summary, importance=importance, bias=bias)
    abort(404)
    
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

@app.route("/submit_rating", methods=["POST"])
def ratings():
    if not session:
        abort(401)

    src_art = request.referrer[request.referrer.rindex("/")+1:]
    src_art = src_art.replace("%20", "").lower()

    data = json.loads(request.data)

    data = {
        "ArtId": idmap[src_art],
        "UserId": session.get("user")["userinfo"]["sub"],
        "Biased": data["usr_bias"]   == "yes",
        "Important": data["usr_imp"] == "yes",
        "Opinion": data["usr_opin"]  == "yes"
    }

    rating = Ratings.query.filter_by(UserId=data["UserId"], ArtId=data["ArtId"]).first()
    
    skip = False
    if rating is None:
        new_rating = Ratings(
            UserId=data["UserId"], 
            ArtId=data["ArtId"], 
            Biased=data["Biased"], 
            Important=data["Important"], 
            Opinion=data["Opinion"]
        )
    else:
        rating.Biased = data["Biased"]
        rating.Important = data["Important"]
        rating.Opinion = data["Opinion"]
        skip = True
        
    
    if not skip: 
        db.session.add(new_rating)
    db.session.commit()
    
    return ""
        
if __name__ == "__main__":
    app.run(host="localhost", port=env.get("PORT", 3000)) #ssl_context='adhoc'