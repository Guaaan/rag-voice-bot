from msal import PublicClientApplication
import os
from dotenv import load_dotenv
load_dotenv()

# Configuración
CLIENT_ID = os.environ.get("AZURE_CLIENT_ID")
TENANT_ID = os.environ.get("AZURE_TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["User.Read"]

def main():
    app = PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY
    )

    accounts = app.get_accounts()
    result = None

    if accounts:
        print("Se encontró una cuenta en caché:")
        for i, account in enumerate(accounts):
            print(f"{i + 1}: {account['username']}")
        chosen = accounts[0]
        result = app.acquire_token_silent(SCOPES, account=chosen)

    if not result:
        print("Iniciando autenticación interactiva...")
        result = app.acquire_token_interactive(scopes=SCOPES)  # Sin redirect_uri

    if "access_token" in result:
        print("\n✅ Token de acceso obtenido:")
        print(result["access_token"])
    else:
        print("\n❌ Error al obtener el token:")
        print(result.get("error"))
        print(result.get("error_description"))
        print("Correlation ID:", result.get("correlation_id"))

if __name__ == "__main__":
    main()

