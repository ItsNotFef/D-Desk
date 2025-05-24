from flask import Flask, request, redirect, session, jsonify
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)
app.secret_key = "una_chiave_super_segreta"  # cambia con una roba tua

CLIENT_ID = "159b7003266f4609aabe6d8790b3a745"
CLIENT_SECRET = "ce1b344ff1d54a1eb1b96677ac156cd8"
REDIRECT_URI = "https://d-desk.onrender.com/callback"  # Cambia con il tuo URL deployato!

SCOPE = "user-read-currently-playing user-read-playback-state"

sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE)

@app.route("/")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)

    session['token_info'] = token_info
    return "Login effettuato! Ora puoi usare /currently-playing"

@app.route("/currently-playing")
def currently_playing():
    token_info = session.get('token_info', None)
    if not token_info:
        return jsonify({"error": "non loggato"}), 401

    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

    sp = spotipy.Spotify(auth=token_info['access_token'])
    current = sp.current_user_playing_track()
    if current is None:
        return jsonify({"message": "Nessuna traccia in riproduzione"})
    return jsonify(current)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
