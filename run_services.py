import subprocess
import sys
import time
import os
import signal

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MICROSERVICES_DIR = os.path.join(BASE_DIR, 'microservices')

print(f"Microservices Directory: {MICROSERVICES_DIR}")

# Define services
services = [
    {
        'name': 'Core Engine (Validation + Prediction)',
        'path': 'app.py',
        'cwd': os.path.join(MICROSERVICES_DIR, 'core_engine'),
        'port': 5001
    },
    {
        'name': 'LLM Service (Gemini)',
        'path': 'app.py',
        'cwd': os.path.join(MICROSERVICES_DIR, 'llm_service'),
        'port': 5002
    },
    {
        'name': 'Gateway Service',
        'path': 'app.py',
        'cwd': os.path.join(MICROSERVICES_DIR, 'gateway'),
        'port': 5000
    }
]

processes = []

def signal_handler(sig, frame):
    print("\n🛑 Stopping all services...")
    for p in processes:
        if sys.platform == 'win32':
            p.terminate()
        else:
            p.send_signal(signal.SIGINT)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def start_services():
    print("🚀 Starting Vehicle Maintenance Microservices...")
    print("="*50)
    
    # Check for API Key
    if not os.environ.get('GEMINI_API_KEY'):
        print("WARNING: GEMINI_API_KEY environment variable not found.")
        print("   The LLM Service will not function correctly without it.")
        print("   Please set it before running this script: $env:GEMINI_API_KEY='your_key'")
        print("="*50)
        time.sleep(2)
    
    python_executable = sys.executable

    for service in services:
        print(f"Starting {service['name']} on port {service['port']}...")
        try:
            kwargs = {}
            if sys.platform == 'win32':
                kwargs['creationflags'] = subprocess.CREATE_NEW_CONSOLE
            
            p = subprocess.Popen(
                [python_executable, service['path']],
                cwd=service['cwd'],
                **kwargs
            )
            processes.append(p)
            time.sleep(1)
        except Exception as e:
            print(f"Failed to start {service['name']}: {e}")

    print("\n✅ All services are running in separate windows!")
    print("Press Ctrl+C in this window to stop all services.")
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    start_services()
