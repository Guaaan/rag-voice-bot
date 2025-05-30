import os

# Configuración de Azure AD
AZURE_CLIENT_ID = os.environ.get("AZURE_CLIENT_ID")
AZURE_TENANT_ID = os.environ.get("AZURE_TENANT_ID")
AZURE_CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET")
AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"

# Configuración de la aplicación
REDIRECT_URI = "http://localhost:8500/auth/callback"
SCOPES = ["User.Read"]
BACKEND_URL = "http://localhost:8500"  # URL del backend Flask