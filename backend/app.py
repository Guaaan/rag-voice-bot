import os
from flask import Flask, request, jsonify
from msal import ConfidentialClientApplication
import threading
from dotenv import load_dotenv
load_dotenv.load_dotenv()

app = Flask(__name__)

# Configuración Azure AD
CLIENT_ID = os.environ['AZURE_CLIENT_ID']
TENANT_ID = os.environ['AZURE_TENANT_ID']
CLIENT_SECRET = os.environ['AZURE_CLIENT_SECRET']
REDIRECT_URI = "http://localhost:8500/auth/callback"
SCOPES = ["User.Read"]
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# MSAL Application
msal_app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

# Almacenamiento temporal de auth
auth_result = {}
auth_event = threading.Event()

@app.route('/auth/login')
def login():
    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return jsonify({"auth_url": auth_url})

@app.route('/auth/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Falta código de autorización", 400

    token = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    if "access_token" in token:
        auth_result['user'] = {
            "username": token.get("id_token_claims", {}).get("preferred_username"),
            "access_token": token["access_token"]
        }
        auth_event.set()
        return "Autenticación exitosa, puedes cerrar esta pestaña"
    else:
        return f"Error de autenticación: {token.get('error_description')}", 400

@app.route('/auth/status')
def auth_status():
    if 'user' in auth_result:
        user = auth_result.pop('user')  # Limpiamos después de usar
        return jsonify({
            "authenticated": True,
            "user": user
        })
    return jsonify({"authenticated": False})

@app.route('/auth/logout')
def logout():
      # Limpiamos la sesión local primero
      if 'user' in auth_result:
            auth_result.clear()

      # Construimos la URL de logout de Microsoft
      logout_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/logout"

      # Parámetros para redirigir de vuelta a tu aplicación después del logout
      post_logout_redirect_uri = "http://localhost:8500"  # Cambia esto según necesites

      # URL completa con parámetros
      full_logout_url = (
            f"{logout_url}?"
            f"post_logout_redirect_uri={post_logout_redirect_uri}"
      )

      # Redirigimos al usuario al logout de Microsoft
      return jsonify({
            "logout_url": full_logout_url,
            "status": "redirecting_to_microsoft_logout"
      })
@app.route('/auth/check-session')
def check_session():
    """Endpoint para verificar si hay sesión activa sin consumirla"""
    if 'user' in auth_result:
        user_data = auth_result['user'].copy()  # Copia sin remover
        return jsonify({
            "authenticated": True,
            "user": user_data
        })
    return jsonify({"authenticated": False})

@app.route('/auth/current-user')
def current_user():
    """Devuelve los datos del usuario actual"""
    if 'user' in auth_result:
        return jsonify(auth_result['user'])
    return jsonify({"error": "No autenticado"}), 401
def run():
    app.run(port=8500)

if __name__ == '__main__':
    run()