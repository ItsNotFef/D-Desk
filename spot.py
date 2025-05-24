from flask import Flask, request, redirect, session, jsonify, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # segreto random

CLIENT_ID = "159b7003266f4609aabe6d8790b3a745"
CLIENT_SECRET = "ce1b344ff1d54a1eb1b96677ac156cd8"
REDIRECT_URI = "https://d-desk.onrender.com/callback"  # il tuo URL deployato

SCOPE = "user-read-currently-playing user-read-playback-state"

sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE,
                        cache_path=".cache")  # per salvare token localmente (su server)

@app.route("/")
def home():
    if "token_info" not in session:
        return redirect(url_for("login"))
    return """
    <h2>Benvenuto! Sei loggato con Spotify.</h2>
    <p>Per leggere la traccia attuale da ESP32, chiama <code>/esp-song</code></p>
    <p><a href="/logout">Logout</a></p>
    """

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get('code')
    if not code:
        return "Errore: nessun codice fornito"

    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    return "Logout effettuato!"

def get_token():
    token_info = session.get('token_info', None)
    if not token_info:
        return None

    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    return token_info['access_token']

@app.route("/esp-song")
def esp_song():
    token = get_token()
    if not token:
        return jsonify({"error": "non loggato"}), 401

    sp = spotipy.Spotify(auth=token)
    current = sp.current_user_playing_track()

    if current is None:
        return jsonify({"message": "Nessuna traccia in riproduzione"})
    
    item = current.get("item", {})
    artist_names = [artist["name"] for artist in item.get("artists", [])]
    song = {
        "title": item.get("name"),
        "artists": artist_names,
        "album": item.get("album", {}).get("name"),
        "progress_ms": current.get("progress_ms"),
        "duration_ms": item.get("duration_ms")
    }
    return jsonify(song)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
