from flask import Flask, jsonify, request, send_from_directory, Blueprint, redirect, session, url_for
import sqlite3
from sqlite3 import Error
import os
import requests
from flask_session import Session

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['STATIC_FOLDER'] = 'static'
app.config['SESSION_COOKIE_SECURE'] = False


Session(app)

main_blueprint = Blueprint('main', __name__)

def get_db_connection():
    conn = sqlite3.connect("./db/petitions.db")
    conn.row_factory = sqlite3.Row
    return conn

@main_blueprint.route("/api/petitions", methods=["GET"])
def get_petitions():
    status = request.args.get("status", "open")
    conn = get_db_connection()
    petitions = conn.execute("SELECT * FROM petitions WHERE status=?", (status,)).fetchall()
    return jsonify([dict(petition) for petition in petitions])

@main_blueprint.route("/", methods=["GET"])
def index():
    return send_from_directory("static", "index.html")

@main_blueprint.route("/login.html", methods=["GET"])
def login():
    return send_from_directory("static", "login.html")

@main_blueprint.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)

# OAuth2 Discord
CLIENT_ID = 1093521955698782278
CLIENT_SECRET = 'zqgK8Ibi94L8bDqx8mIoGVM1D9v_8gFc'
REDIRECT_URI = 'http://127.0.0.1:8080/login/callback'
TOKEN_URL = 'https://discord.com/api/oauth2/token'
USER_URL = 'https://discord.com/api/users/@me'


@main_blueprint.route("/login/callback", methods=["GET"])
def login_callback():
    code = request.args.get('code')
    
    if code:
        payload = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'scope': 'identify email'
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        # Échange du code d'autorisation contre un token d'accès
        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        response_data = response.json()

        if response.status_code == 200:
            access_token = response_data['access_token']
            headers = {
                'Authorization': f"Bearer {access_token}"
            }

            # Récupération des informations de l'utilisateur
            user_response = requests.get(USER_URL, headers=headers)
            user_data = user_response.json()

            if user_response.status_code == 200:
                # Stocke les informations de l'utilisateur et gére l'authentification de l'application
                session['user'] = user_data
                print("User data:", user_data)
                return f'''
                <script>
                    localStorage.setItem('discord_access_token', '{access_token}');
                    window.location.href = '/';
                </script>
                '''
            else:
                print("Erreur lors de la récupération des informations de l'utilisateur")
        else:
            print("Erreur lors de l'échange du code d'autorisation")

    return redirect(url_for('main.index'))

@main_blueprint.route("/api/authenticated", methods=["GET"])
def authenticated():
    print("Session user:", session.get('user'))  # Ajouter cette ligne
    return jsonify({'authenticated': 'user' in session})

app.register_blueprint(main_blueprint)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)