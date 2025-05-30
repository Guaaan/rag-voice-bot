import chainlit as cl 
from chainlit import User
import asyncio
import requests
import webbrowser
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

BACKEND_URL = "http://localhost:8500"

async def check_existing_session() -> Optional[User]:
    """Verifica si hay una sesión activa en el backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/auth/check-session", timeout=5)
        if response.status_code == 200 and response.json().get("authenticated"):
            user_data = response.json()["user"]
            return User(
                identifier=user_data["username"],
                metadata={
                    "token": user_data["access_token"],
                    "provider": "azure_ad"
                }
            )
    except requests.RequestException:
        pass
    return None

async def perform_login() -> Optional[User]:
    """Realiza el flujo completo de autenticación"""
    try:
        # 1. Obtener URL de autenticación
        auth_url = f"{BACKEND_URL}/auth/login"
        response = requests.get(auth_url, timeout=5)
        webbrowser.open(response.json()["auth_url"])
        
        # 2. Esperar autenticación
        for _ in range(30):  # 30 intentos (60 segundos máximo)
            status_response = requests.get(f"{BACKEND_URL}/auth/status", timeout=5)
            if status_response.status_code == 200:
                data = status_response.json()
                if data["authenticated"]:
                    user_data = data["user"]
                    return User(
                        identifier=user_data["username"],
                        metadata={
                            "token": user_data["access_token"],
                            "provider": "azure_ad"
                        }
                    )
            await asyncio.sleep(2)
    except requests.RequestException as e:
        print(f"Error durante autenticación: {e}")
    
    return None

@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    # 1. Primero verificar si ya hay sesión activa
    existing_user = await check_existing_session()
    if existing_user:
        return existing_user
    
    # 2. Si no hay sesión, realizar autenticación completa
    return await perform_login()

@cl.on_chat_start
async def start_chat():
    user = cl.user_session.get("user")
    await cl.Message(f"Bienvenido de nuevo {user.identifier}").send()

@cl.on_message
async def handle_message(message: cl.Message):
    # Tu lógica de mensajes aquí
    await cl.Message("Respuesta del asistente").send()

@cl.on_logout
async def logout():
    response = requests.get(f"{BACKEND_URL}/auth/logout")
    print("🔓 Cerrando sesión local y remota")
    webbrowser.open(response.json()["auth_url"])                
    # webbrowser.open("http://localhost:8500/auth/logout")
    # auth_result.clear()  # Limpiar token local
    # Opcional: cierre en Azure AD