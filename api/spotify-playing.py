from flask import Flask, Response, jsonify
from base64 import b64encode

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

import requests
import json
import os
import random

"""
Inspired from https://github.com/natemoo-re
"""

print("Starting Server")


SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_SECRET_ID = os.getenv("SPOTIFY_SECRET_ID")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")

SPOTIFY_URL_REFRESH_TOKEN = "https://accounts.spotify.com/api/token"
SPOTIFY_URL_NOW_PLAYING = "https://api.spotify.com/v1/me/player/currently-playing"

LATEST_PLAY = None
app = Flask(__name__)


def get_authorization():

    return b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_SECRET_ID}".encode()).decode("ascii")


def refresh_token():

    data = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN,
    }

    headers = {"Authorization": "Basic {}".format(get_authorization())}

    response = requests.post(SPOTIFY_URL_REFRESH_TOKEN, data=data, headers=headers)
    repsonse_json = response.json()

    return repsonse_json["access_token"]


def get_now_playing():

    token = refresh_token()

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(SPOTIFY_URL_NOW_PLAYING, headers=headers)

    if response.status_code == 204:
        return {}

    repsonse_json = response.json()
    return repsonse_json


def get_svg_template():

    css_bar = ""
    left = 1
    for i in range(1, 76):

        anim = random.randint(350, 500)
        css_bar += ".bar:nth-child({})  {{{{ left: {}px; animation-duration: {}ms; }}}}".format(
            i, left, anim
        )
        left += 4

    svg = (
        """
        <svg width="320" height="445" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
            <foreignObject width="320" height="445">
                <div xmlns="http://www.w3.org/1999/xhtml" class="container">
                    <style>
                        div {{font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji;}}
                        .container {{background-color: #121212; border-radius: 10px; padding: 10px 10px}}
                        .playing {{ font-weight: bold; color: #53b14f; text-align: center; display: flex; justify-content: center; align-items: center;}}
                        .not-play {{color: #ff1616;}}
                        .artist {{ font-weight: bold; font-size: 20px; color: #fff; text-align: center; margin-top: 5px; }}
                        .song {{ font-size: 16px; color: #b3b3b3; text-align: center; margin-top: 5px; margin-bottom: 15px; }}
                        .logo {{ margin-left: 5px; margin-top: 5px; }}
                        .cover {{ border-radius: 5px; margin-top: 9px; }}
                        #bars {{
                            height: 30px;
                            margin: -20px 0 0 0px;
                            position: absolute;
                            width: 40px;
                        }}

                        .bar {{
                            background: #53b14f;
                            bottom: 1px;
                            height: 3px;
                            position: absolute;
                            width: 3px;      
                            animation: sound 0ms -800ms linear infinite alternate;
                        }}

                        @keyframes sound {{
                            0% {{
                            opacity: .35;
                                height: 3px; 
                            }}
                            100% {{
                                opacity: 1;       
                                height: 28px;        
                            }}
                        }}

                        """
        + css_bar
        + """

                    </style>
                    {}
                </div>
            </foreignObject>
        </svg>
    """
    )
    return svg


def load_image_b64(url):

    resposne = requests.get(url)
    return b64encode(resposne.content).decode("ascii")


def make_svg(data):
    global LATEST_PLAY

    template = get_svg_template()

    text = "Now playing"
    content_bar = "".join(["<div class='bar'></div>" for i in range(75)])
    if data == {} and LATEST_PLAY is not None:
        data = LATEST_PLAY
        text = "Latest play"
        content_bar = ""
    elif data == {}:
        content = """
            <div class="playing not-play">Nothing playing on Spotify</div>
        """
        return template.format(content)

    content = """
        <div class="playing">{} on <img class="logo" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACMAAAAjCAYAAAAe2bNZAAAE5ElEQVRYR81WS08bVxQ+dzweY48fQCCBllJDmqpRSx6gKizSiAUbILZjA21KVEhF20hNlLb/IKu2m3QRKaqQogIRkAXhYQxFSJGCQqVKrVSBQtpCFqEQkrQhxnb8Yjxzp7oTmdjjsWd4LHIlLzz3PL57zvedexG8Qgu9Qlhg22Bqumr0+/L2VdAMOpBvtdgCoedBnhPvsw/YpcFLg9x2DrklMA19DVajkf4B0dQnAMDkSJgQedwfWot9fevcraBWYJrA1HXX5RUWWG8jhGq1Bk7aiVj8PfGfWOc754uq+aqCOXXT8bFOTw2oBVLb5zmhw9s6fj2XXU4wniFnF6LRF2qJtO6LPPQMN3s/zWafFcxuA0kCwILYO+IZO6sESBHMbrUmWwVwQjw70jLWK9/PAEPIuqfQFtNa+u3acU8wKyd1BhjPqPNXJdVgHkP8WRwiqxGI/RsDLsSBiEXQGXRgKDCAqcQk/RgbA4hS1QXx/WPYPVaTepg0LzJHTBZmcy5wQQ5mL89CeCUMIGqvAQFjLjeD/aQdiqqLsoKLh/nCiTMT68nIaWA8Q45riKY6k5szF2YgEU5oR5HFkn2dhUNfHQLjXmOaBRZw34jHRwaotNLANHtdG6mTdaF3AVZvrwJCCNgyFoqOFIHtgA2MxUbQGXXSdyxg4MM8RJ9EYf2vdfDf80PsaUyxkqSNtd+nzU1+yOXVZ4Ahd429pCzjTiG80MIBeVH4GA/Lk8uw/PMyEL4lV9XFKiiuLt78H/2Hy5u8OEmK8LIyjb2Nbxvz9Qu5eiIKokTcuD8OfISXTk+zNOQV5r0grk6ZuIGFAMxdnpMIf+LHE0Dpqc00XCT+nq9t6l4aGOeNpia9iR6XgyHKuXv1rjYSI5BaWN5QDqUflAJFv0ya7ZBCHLeMfuQbSgPTPnG6LcLH+uVOM+dnIBFRIHGyCDlURgh7+JvDYCo1ZS04qzd3Xm/s/0lTZQJ/B2BxYBHK6sug+Ggx6M16Ge1BahdRHSHvytQKhB6E0pITMLXfKV/4QgK3jLbIKqOFM1vROFHW/NX5zdFw7NtjwL7GZoSIB/mqifaJ+bTKtF5qZfBRTmK14hIBuOccRB5GIPIoAhv+DeDjPDBWBsxvmMFaaQVDviGjaut/rkNgMQAVpyoUwyqqiVg2e11E2pu6l7xFgDtf3gEiVS2LgNv/4X4oPV6qxVx5zhBPz5CjG9FU2vUuiiJMd05LcrRWWKHg3QKwvGkBJv/FHUQkHl4Ow9rsGhAJp86USncl2F32rKCwgG+MeHxtSYO0wVDfVW+zlbABLUfKLlUBFvsW4fEvjyWTg50HJZkrrfDT+J6pz6b8imCk6ow4f0MUen8ngKTuCiIsjS+B3WFXnOAiFueG3WNHUvNkjExHl8PElFCRnYJR83/2MGiZPj8dzgmGbLoGT7bTjC7jJaaWQOs+zwmfe1vHr8ntc7yBXd2IBsW3qtakSnYixgPDbt8Zpb2cTzL3sLOH0qGOnSRP9c0FhNipvg/dN5s6KD3ds1NA2Vqjyhl5YkJq/V40gyhUvVVQRDX+R6HjcrJuuU1yh6b+pgLGSF2hdNRpAKBzAOOxgAejfu5C6hxRO4hqm7IFaLjSYKCL8Fs6HfOO1WK1haKhYCKKF3AA30++3NSSa1bTVgPthv22K7MbyeUx/gfIiuIzZiZJFQAAAABJRU5ErkJggg==" /></div>
        <div class="artist">{}</div>
        <div class="song">{}</div>
        <div id='bars'>
            {}
        </div>
        <a href="{}" target="_BLANK">
            <center>
            <img src="data:image/png;base64, {}" width="300" height="300" class="cover"/>
            </center>
        </a>
        """

    item = data["item"]

    """
    print(json.dumps(item))
    print(item["artists"][0]["name"])
    print(item["external_urls"]["spotify"])
    print(item["album"]["images"][0]["url"])
    """

    img = load_image_b64(item["album"]["images"][1]["url"])
    artist_name = item["artists"][0]["name"].replace("&", "&amp;")
    song_name = item["name"].replace("&", "&amp;")
    content_rendered = content.format(
        text,
        artist_name, 
        song_name, 
        content_bar, 
        item["external_urls"]["spotify"], 
        img,
    )

    return template.format(content_rendered)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    global LATEST_PLAY

    # TODO: caching

    data = get_now_playing()
    svg = make_svg(data)

    # cache lastest data
    if data != {}:
        LATEST_PLAY = data


    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"

    return resp


if __name__ == "__main__":
    app.run(debug=True)
