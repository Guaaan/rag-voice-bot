import subprocess
import sys
import time
import webbrowser
import os
from pathlib import Path
import signal

def run_command(command, cwd=None):
    """Ejecuta un comando y maneja su salida"""
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process

def main():
    # Configurar PYTHONPATH
    project_root = Path(__file__).parent
    os.environ['PYTHONPATH'] = str(project_root)
    
    try:
        # 1. Iniciar backend
        print("🚀 Iniciando backend Flask...")
        flask_process = run_command([sys.executable, "app.py"], cwd=project_root/"backend")
        
        # Esperar que el backend esté listo
        time.sleep(3)
        
        # 2. Iniciar frontend
        print("💻 Iniciando frontend Chainlit...")
        chainlit_process = run_command(
            [sys.executable, "-m", "chainlit", "run", "app.py", "--port", "8000"],
            cwd=project_root/"frontend"
        )
        
        # 3. Abrir navegador
        time.sleep(5)
      #   webbrowser.open("http://localhost:8000")
        
        print("\n✅ Servicios iniciados correctamente")
        print("• Backend (Flask): http://localhost:8500")
        print("• Frontend (Chainlit): http://localhost:8000")
        print("\nPresiona Ctrl+C para detener los servicios\n")
        
        # Mantener el script activo
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servicios...")
    finally:
        # Terminar todos los procesos
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("✅ Todos los servicios han sido detenidos")

if __name__ == "__main__":
    main()