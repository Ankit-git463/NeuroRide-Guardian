"""
NeuroRide Guardian - Service Manager
Starts and manages all microservices
"""
import subprocess
import sys
import time
import os
import signal
import requests
from datetime import datetime

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MICROSERVICES_DIR = os.path.join(BASE_DIR, 'microservices')

# ANSI color codes for better output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Define services (in order of dependency)
services = [
    {
        'name': 'Core Engine',
        'description': 'Validation + ML Prediction',
        'path': 'app.py',
        'cwd': os.path.join(MICROSERVICES_DIR, 'core_engine'),
        'port': 5001,
        'required': True,
        'health_endpoint': '/health'
    },
    {
        'name': 'LLM Service',
        'description': 'AI Report Generation (Gemini)',
        'path': 'app.py',
        'cwd': os.path.join(MICROSERVICES_DIR, 'llm_service'),
        'port': 5002,
        'required': False,  # Optional if no API key
        'health_endpoint': '/health'
    },
    {
        'name': 'Scheduling Service',
        'description': 'Appointment Management',
        'path': 'app.py',
        'cwd': os.path.join(MICROSERVICES_DIR, 'scheduling'),
        'port': 5003,
        'required': True,
        'health_endpoint': '/health'
    },
    {
        'name': 'Forecasting Service',
        'description': 'Demand Prediction',
        'path': 'app.py',
        'cwd': os.path.join(MICROSERVICES_DIR, 'forecasting'),
        'port': 5004,
        'required': True,
        'health_endpoint': '/health'
    },
    {
        'name': 'Orchestrator Service',
        'description': 'Workflow Automation',
        'path': 'app.py',
        'cwd': os.path.join(MICROSERVICES_DIR, 'orchestrator'),
        'port': 5005,
        'required': True,
        'health_endpoint': '/health'
    },
    {
        'name': 'Telemetry Ingestion',
        'description': 'Data Collection + Simulator',
        'path': 'app.py',
        'cwd': os.path.join(MICROSERVICES_DIR, 'telemetry_ingestion'),
        'port': 5006,
        'required': True,
        'health_endpoint': '/health'
    },
    {
        'name': 'Gateway Service',
        'description': 'API Gateway',
        'path': 'app.py',
        'cwd': os.path.join(MICROSERVICES_DIR, 'gateway'),
        'port': 5000,
        'required': True,
        'health_endpoint': '/health'
    }
]

processes = []

def print_header():
    """Print startup header"""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("  NeuroRide Guardian - Vehicle Maintenance Scheduling System")
    print("  Service Manager v2.0")
    print("=" * 70)
    print(f"{Colors.ENDC}")

def print_colored(message, color=Colors.OKGREEN):
    """Print colored message"""
    print(f"{color}{message}{Colors.ENDC}")

def check_prerequisites():
    """Check if all prerequisites are met"""
    print(f"\n{Colors.BOLD}Checking Prerequisites...{Colors.ENDC}")
    
    all_ok = True
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print_colored(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}", Colors.OKGREEN)
    else:
        print_colored(f"✗ Python version too old: {python_version.major}.{python_version.minor}", Colors.FAIL)
        all_ok = False
    
    # Check for API Key
    if not os.environ.get('GEMINI_API_KEY'):
        print_colored("⚠ GEMINI_API_KEY not found (LLM Service will be limited)", Colors.WARNING)
        print_colored("  Set with: $env:GEMINI_API_KEY='your_key'", Colors.WARNING)
    else:
        print_colored("✓ GEMINI_API_KEY configured", Colors.OKGREEN)
    
    # Check if database exists
    db_path = os.path.join(BASE_DIR, 'database', 'neuroride_guardian.db')
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path) / 1024  # KB
        print_colored(f"✓ Database found ({db_size:.1f} KB)", Colors.OKGREEN)
    else:
        print_colored(f"✗ Database not found at: {db_path}", Colors.FAIL)
        print_colored("  Run: python database/seed_data.py", Colors.WARNING)
        all_ok = False
    
    # Check service directories
    missing_services = []
    for service in services:
        if not os.path.exists(service['cwd']):
            missing_services.append(service['name'])
    
    if missing_services:
        print_colored(f"✗ Missing service directories: {', '.join(missing_services)}", Colors.FAIL)
        all_ok = False
    else:
        print_colored(f"✓ All {len(services)} service directories found", Colors.OKGREEN)
    
    return all_ok

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print(f"\n\n{Colors.WARNING}Shutting down all services...{Colors.ENDC}")
    for p in processes:
        try:
            if sys.platform == 'win32':
                p.terminate()
            else:
                p.send_signal(signal.SIGINT)
        except:
            pass
    print_colored("✓ All services stopped", Colors.OKGREEN)
    sys.exit(0)

def check_service_health(port, endpoint='/health', timeout=2):
    """Check if service is healthy"""
    try:
        response = requests.get(f"http://localhost:{port}{endpoint}", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def start_services():
    """Start all microservices"""
    print(f"\n{Colors.BOLD}Starting Microservices...{Colors.ENDC}")
    print("=" * 70)
    
    python_executable = sys.executable
    started_count = 0

    for i, service in enumerate(services, 1):
        print(f"\n[{i}/{len(services)}] {Colors.BOLD}{service['name']}{Colors.ENDC}")
        print(f"    {service['description']}")
        print(f"    Port: {service['port']}")
        
        # Check if service directory exists
        if not os.path.exists(service['cwd']):
            if service['required']:
                print_colored(f"    ✗ Directory not found: {service['cwd']}", Colors.FAIL)
                continue
            else:
                print_colored(f"    ⊘ Skipping (optional)", Colors.WARNING)
                continue
        
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
            print_colored(f"    ✓ Started (PID: {p.pid})", Colors.OKGREEN)
            started_count += 1
            time.sleep(2)  # Give service time to start
            
        except Exception as e:
            print_colored(f"    ✗ Failed to start: {e}", Colors.FAIL)

    return started_count

def verify_services():
    """Verify all services are healthy"""
    print(f"\n{Colors.BOLD}Verifying Services...{Colors.ENDC}")
    print("=" * 70)
    
    time.sleep(3)  # Wait for services to fully start
    
    healthy_count = 0
    for service in services:
        if not os.path.exists(service['cwd']):
            continue
        
        print(f"{service['name']:.<40}", end=" ")
        if check_service_health(service['port'], service.get('health_endpoint', '/health')):
            print_colored("✓ Healthy", Colors.OKGREEN)
            healthy_count += 1
        else:
            print_colored("✗ Not responding", Colors.FAIL)
    
    return healthy_count

def print_service_info():
    """Print service information"""
    print(f"\n{Colors.BOLD}Service Endpoints:{Colors.ENDC}")
    print("=" * 70)
    
    for service in services:
        if os.path.exists(service['cwd']):
            print(f"  {service['name']:.<35} http://localhost:{service['port']}")
    
    print(f"\n{Colors.BOLD}Frontend Pages:{Colors.ENDC}")
    print("=" * 70)
    print(f"  Main Dashboard:.<35 Open: frontend/index.html")
    print(f"  Admin Dashboard:.<35 Open: frontend/admin.html")
    print(f"  Bookings Management:.<35 Open: frontend/bookings.html")
    print(f"  AI Reports:.<35 Open: frontend/report.html")

def print_quick_start():
    """Print quick start guide"""
    print(f"\n{Colors.BOLD}Quick Start Guide:{Colors.ENDC}")
    print("=" * 70)
    print(f"{Colors.OKCYAN}")
    print("1. Open frontend/admin.html in your browser")
    print("2. Click 'Start Simulator' to generate telemetry data")
    print("3. Click 'Run Full Automation Cycle' to see the system in action")
    print("4. Open frontend/bookings.html to view scheduled appointments")
    print(f"{Colors.ENDC}")

def main():
    """Main function"""
    signal.signal(signal.SIGINT, signal_handler)
    
    print_header()
    
    # Check prerequisites
    if not check_prerequisites():
        print_colored("\n✗ Prerequisites check failed. Please fix the issues above.", Colors.FAIL)
        print_colored("  Continuing anyway, but some services may not work...\n", Colors.WARNING)
        time.sleep(3)
    
    # Start services
    started_count = start_services()
    
    if started_count == 0:
        print_colored("\n✗ No services were started. Exiting.", Colors.FAIL)
        sys.exit(1)
    
    # Verify services
    healthy_count = verify_services()
    
    # Print service info
    print_service_info()
    print_quick_start()
    
    # Final status
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}System Status:{Colors.ENDC}")
    print(f"  Started: {started_count}/{len(services)} services")
    print(f"  Healthy: {healthy_count}/{started_count} services")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    if healthy_count >= started_count - 1:  # Allow 1 service to fail
        print_colored("\n✓ System is ready!", Colors.OKGREEN)
    else:
        print_colored("\n⚠ Some services failed to start. Check console windows for errors.", Colors.WARNING)
    
    print(f"\n{Colors.WARNING}Press Ctrl+C to stop all services{Colors.ENDC}\n")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
