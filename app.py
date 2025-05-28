import os
import traceback
import asyncio
from openai import AsyncAzureOpenAI
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
from uuid import uuid4
from chainlit.logger import logger
from realtime import RealtimeClient
from azure_tts import Client as AzureTTSClient
from tools import search_knowledge_base_handler, report_grounding_handler, tools
from msal import ConfidentialClientApplication
from flask import Flask, request
import threading
import webbrowser
import time

REDIRECT_URI = "http://localhost:8500/auth/callback"
SCOPES = ["User.Read"]

AZURE_CLIENT_ID = os.environ.get("AZURE_CLIENT_ID")
AZURE_TENANT_ID = os.environ.get("AZURE_TENANT_ID")
AZURE_CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET")
AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"

msal_app = ConfidentialClientApplication(
    AZURE_CLIENT_ID,
    authority=AUTHORITY,
    client_credential=AZURE_CLIENT_SECRET
)

flask_app = Flask(__name__)
auth_event = threading.Event()
auth_result = {}

@flask_app.route("/auth/callback")
def flask_auth_callback():
    code = request.args.get("code")
    if not code:
        return "Código de autorización no recibido.", 400

    token_response = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    if "access_token" in token_response:
        auth_result["user"] = {
            "username": token_response.get("id_token_claims", {}).get("preferred_username"),
            "access_token": token_response["access_token"]
        }
        auth_event.set()  # Notificamos a Chainlit que ya tenemos el token
        # Devuelve HTML que cierra la pestaña automáticamente
        return """
        <html>
            <body>
                <script>
                    window.close();
                </script>
                <p>✅ Autenticación exitosa. Puedes cerrar esta pestaña.</p>
            </body>
        </html>
        """
    else:
        return f"❌ Error: {token_response}", 500

def run_flask_server():
    flask_app.run(port=8500)

threading.Thread(target=run_flask_server, daemon=True).start()
@flask_app.route("/auth/logout")
def flask_auth_logout():
    auth_result.clear()
    logout_url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/logout?post_logout_redirect_uri=http://localhost:8500/logout-success"
    return f"""
    <html>
        <body>
            <script>
                 window.close();
            </script>
            <p>🔒 Sesión cerrada. Redirigiendo...</p>
        </body>
    </html>
    """

@flask_app.route("/logout-success")
def logout_success():
    return "<p>✅ Has cerrado sesión correctamente.</p>"

voice = "es-AR-AlloyTurboMultilingualNeural"

VOICE_MAPPING = {
    "english": "en-IN-AnanyaNeural",
    "hindi": "hi-IN-AnanyaNeural",
    "tamil": "ta-IN-PallaviNeural",
    "odia": "or-IN-SubhasiniNeural",
    "bengali": "bn-IN-BashkarNeural",
    "gujarati": "gu-IN-DhwaniNeural",
    "kannada": "kn-IN-SapnaNeural",
    "malayalam": "ml-IN-MidhunNeural",
    "marathi": "mr-IN-AarohiNeural",
    "punjabi": "pa-IN-GurpreetNeural",
    "telugu": "te-IN-MohanNeural",
    "urdu": "ur-IN-AsadNeural"
}

tts_sentence_end = [ ".", "!", "?", ";", "。", "！", "？", "；", "\n", "।"]
async def setup_openai_realtime(system_prompt: str):
    """Instantiate and configure the OpenAI Realtime Client"""
    openai_realtime = RealtimeClient(system_prompt = system_prompt)
    cl.user_session.set("track_id", str(uuid4()))
    voice = VOICE_MAPPING.get(cl.user_session.get("Language"))
    collected_messages = []
    async def handle_conversation_updated(event):
        item = event.get("item")
        delta = event.get("delta")
        
        """Currently used to stream audio back to the client."""
        if delta:
            # Only one of the following will be populated for any given event
            if 'audio' in delta:
                audio = delta['audio']  # Int16Array, audio added
                if not cl.user_session.get("useAzureVoice"):
                    await cl.context.emitter.send_audio_chunk(cl.OutputAudioChunk(mimeType="pcm16", data=audio, track=cl.user_session.get("track_id")))
            if 'transcript' in delta:
                if cl.user_session.get("useAzureVoice"):
                    chunk_message = delta['transcript']
                    if item["status"] == "in_progress":
                        collected_messages.append(chunk_message)  # save the message
                        if chunk_message in tts_sentence_end: # sentence end found
                            sent_transcript = ''.join(collected_messages).strip()
                            collected_messages.clear()
                            chunk = await AzureTTSClient.text_to_speech_realtime(text=sent_transcript, voice= voice)
                            await cl.context.emitter.send_audio_chunk(cl.OutputAudioChunk(mimeType="audio/wav", data=chunk, track=cl.user_session.get("track_id")))
            if 'arguments' in delta:
                arguments = delta['arguments']  # string, function arguments added
                pass
    
    async def handle_item_completed(item):
        """Generate the transcript once an item is completed and populate the chat context."""
        try:
            transcript = item['item']['formatted']['transcript']
            if transcript.strip() != "":
                await cl.Message(content=transcript).send()      
                
        except Exception as e:
            logger.error(f"Failed to generate transcript: {e}")
            logger.error(traceback.format_exc())
    
    async def handle_conversation_interrupt(event):
        """Used to cancel the client previous audio playback."""
        cl.user_session.set("track_id", str(uuid4()))
        try:
            collected_messages.clear()
        except Exception as e:
            logger.error(f"Failed to clear collected messages: {e}")    
        await cl.context.emitter.send_audio_interrupt()
        
    async def handle_input_audio_transcription_completed(event):
        item = event.get("item")
        delta = event.get("delta")
        if 'transcript' in delta:
            transcript = delta['transcript']
            if transcript != "":
                await cl.Message(author="You", type="user_message", content=transcript).send()
        
    async def handle_error(event):
        logger.error(event)
        
    
    openai_realtime.on('conversation.updated', handle_conversation_updated)
    openai_realtime.on('conversation.item.completed', handle_item_completed)
    openai_realtime.on('conversation.interrupted', handle_conversation_interrupt)
    openai_realtime.on('conversation.item.input_audio_transcription.completed', handle_input_audio_transcription_completed)
    openai_realtime.on('error', handle_error)

    cl.user_session.set("openai_realtime", openai_realtime)
    #cl.user_session.set("tts_client", tts_client)
    coros = [openai_realtime.add_tool(tool_def, tool_handler) for tool_def, tool_handler in tools]
    await asyncio.gather(*coros)

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    auth_event.clear()
    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    print(f"🔗 Abriendo navegador para autenticación: {auth_url}")
    webbrowser.open(auth_url)

    if auth_event.wait(timeout=120):  # Esperamos a que Flask guarde el token
        token_data = auth_result["user"]
        return cl.User(
            identifier=token_data["username"],
            metadata={
                "role": "admin",
                "provider": "azure_entra_id",
                "token": token_data["access_token"]
            }
        )
    else:
        print("⛔ Timeout o fallo de autenticación.")
        return None
    
@cl.on_chat_start
async def start():
    app_user = cl.user_session.get("user")
    print("app_user", app_user)

    settings = await cl.ChatSettings([
        Select(
            id="Language",
            label="Choose Language",
            values=list(VOICE_MAPPING.keys()),
            initial_index=0,
        ),
        Switch(id="useAzureVoice", label="Use Azure Voice", initial=False),
        Slider(
            id="Temperature",
            label="Temperature",
            initial=1,
            min=0,
            max=2,
            step=0.1,
        )
    ]).send()
    await setup_agent(settings)


@cl.on_settings_update
async def setup_agent(settings):
    system_prompt = (
    "Eres un asistente de voz de la compañía ITAM. "
    "Antes de responder a cualquier pregunta, busca información relevante en la base de conocimientos interna. "
    "Si no encuentras información relevante, indica que no tienes una respuesta basada en la base de conocimientos. "
    "Responde siempre en el idioma español."
    )
    cl.user_session.set("useAzureVoice", settings["useAzureVoice"])
    cl.user_session.set("Temperature", settings["Temperature"])
    cl.user_session.set("Language", settings["Language"])
    app_user = cl.user_session.get("user")
    identifier = app_user.identifier if app_user else "admin"
    await cl.Message(
        content="Hola Bienvenido al bot conversacional de ITAM. Puedo brindarte información sobre los contactos de emergencia de algún empleado o información general de la compañía. Presiona `P` para hablar! Prueba preguntarme cual es el contacto de emergencias o la dirección de la compañía."
    ).send()
    system_prompt = system_prompt.replace("<customer_language>", settings["Language"])
    await setup_openai_realtime(system_prompt=system_prompt + "\n\n Customer ID: 12121")
    

@cl.on_message
async def on_message(message: cl.Message):
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime and openai_realtime.is_connected():
        # Usar la nueva función de búsqueda mejorada
        search_results = await search_knowledge_base_handler(message.content)
        
        # Formatear el contexto incluyendo las fuentes
        context = f"Información relevante:\n{search_results}\n\n"
        context += "Por favor, responde basándote en esta información y cita las fuentes usando report_grounding."
        
        await openai_realtime.send_user_message_content([
            {"type": "input_text", "text": context},
            {"type": "input_text", "text": f"Pregunta del usuario: {message.content}"}
        ])
    else:
        await cl.Message(content="Por favor, activa el modo de voz antes de enviar mensajes.").send()

@cl.on_audio_start
async def on_audio_start():
    try:
        openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
        # TODO: might want to recreate items to restore context
        # openai_realtime.create_conversation_item(item)
        await openai_realtime.connect()
        logger.info("Connected to OpenAI realtime")
        return True
    except Exception as e:
        await cl.ErrorMessage(content=f"Failed to connect to OpenAI realtime: {e}").send()
        return False

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime:            
        if openai_realtime.is_connected():
            await openai_realtime.append_input_audio(chunk.data)
        else:
            logger.info("RealtimeClient is not connected")

@cl.on_logout
def on_logout(request: str, response: str):
    print("🔓 Cerrando sesión local y remota")
    auth_result.clear()  # Limpiar token local
    webbrowser.open("http://localhost:8500/auth/logout")  # Opcional: cierre en Azure AD
    
@cl.on_audio_end
@cl.on_chat_end
@cl.on_stop
async def on_end():
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime and openai_realtime.is_connected():
        await openai_realtime.disconnect()