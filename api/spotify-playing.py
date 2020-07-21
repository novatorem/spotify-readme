from flask import Flask, Response, jsonify, render_template
from base64 import b64encode

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import requests
import json
import os
import random

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_SECRET_ID = os.getenv("SPOTIFY_SECRET_ID")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")

# scope user-read-currently-playing/user-read-recently-played
SPOTIFY_URL_REFRESH_TOKEN = "https://accounts.spotify.com/api/token"
SPOTIFY_URL_NOW_PLAYING = "https://api.spotify.com/v1/me/player/currently-playing"
SPOTIFY_URL_RECENTLY_PLAY = "https://api.spotify.com/v1/me/player/recently-played?limit=10"


app = Flask(__name__)


def getAuth():

    return b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_SECRET_ID}".encode()).decode("ascii")


def refreshToken():

    data = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN,
    }

    headers = {"Authorization": "Basic {}".format(getAuth())}

    response = requests.post(SPOTIFY_URL_REFRESH_TOKEN, data=data, headers=headers)
    return response.json()["access_token"]

def get_recently_play():

    token = refreshToken()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(SPOTIFY_URL_RECENTLY_PLAY, headers=headers)

    if response.status_code == 204:
        return {}

    return response.json()

def nowPlaying():

    token = refreshToken()

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(SPOTIFY_URL_NOW_PLAYING, headers=headers)

    if response.status_code == 204:
        return {}

    return response.json()

def barGen(num_bar=85):
    barCSS = ""
    left = 1
    for i in range(1, num_bar + 1):

        anim = random.randint(350, 500)
        barCSS += ".bar:nth-child({})  {{ left: {}px; animation-duration: {}ms; }}".format(
            i, left, anim
        )
        left += 4

    return barCSS

def loadImageB64(url):
    resposne = requests.get(url)
    return b64encode(resposne.content).decode("ascii")

def makeSVG(data):

    height = 445
    num_bar = 85
    content_bar = "".join(["<div class='bar'></div>" for i in range(num_bar)])
    css_bar = barGen(num_bar)

    if data == {}:
        content_bar = ""
        recent_plays = get_recently_play()
        size_recent_play = len(recent_plays["items"])
        idx = random.randint(0, size_recent_play - 1)
        item = recent_plays["items"][idx]["track"]
    else:
        item = data["item"]

    img = loadImageB64(item["album"]["images"][1]["url"])
    artist_name = item["artists"][0]["name"]
    song_name = item["name"]
    url = item["external_urls"]["spotify"]

    rendered_data = {
        "height": height,
        "num_bar": num_bar,
        "content_bar": content_bar,
        "css_bar": css_bar,
        "title_text": title_text,
        "artist_name": artist_name,
        "song_name": song_name,
        "content_bar": content_bar,
        "img": img,
    }

    return render_template("spotify.html.j2", **rendered_data)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):

    data = nowPlaying()
    svg = makeSVG(data)

    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"

    return resp

if __name__ == "__main__":
    app.run(debug=True)
