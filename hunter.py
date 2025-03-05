import subprocess
import os
import psutil
import time
import threading
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Initialize FastAPI web server
app = FastAPI()
stop_scan = False

# Auto-install required tools
def install_tools():
    tools = [
        "nmap", "sqlmap", "nikto", "nuclei", "subfinder",
        "httpx", "amass", "curl"
    ]
    for tool in tools:
        print(f"🔧 Installing {tool}...")
        subprocess.run(["apt", "install", "-y", tool], capture_output=True, text=True)

# Function to log bugs
def log_bug(tool, target, details, severity, impact):
    with open("bugs.txt", "a") as file:
        file.write(f"🔍 Bug Found on: {target}\n")
        file.write(f"🛠 Exploit Used: {tool}\n")
        file.write(f"🚨 Severity: {severity}\n")
        file.write(f"💥 Impact: {impact}\n")
        file.write(f"📜 Details:\n{details}\n")
        file.write("="*50 + "\n")

# Scanning function
def run_scans(target_url):
    global stop_scan

    print(f"🔍 Starting bug hunting on {target_url}...")

    tools = [
        ["nmap", "-sV", target_url],
        ["sqlmap", "-u", target_url, "--batch"],
        ["nikto", "-h", target_url],
        ["nuclei", "-u", target_url],
        ["subfinder", "-d", target_url],
        ["httpx", "-u", target_url],
        ["amass", "enum", "-d", target_url],
        ["curl", "-I", target_url]
    ]

    for tool in tools:
        if stop_scan:
            print("🛑 Scan stopped by user.")
            break
        print(f"🚀 Running: {' '.join(tool)}")
        
        result = subprocess.run(tool, capture_output=True, text=True)
        
        if "vulnerability" in result.stdout.lower() or "exploit" in result.stdout.lower():
            log_bug(tool[0], target_url, result.stdout, "High", "Possible Remote Exploit")

    print("✅ Bug hunting completed! Check results in bugs.txt.")

# Web server to track progress
@app.get("/")
def home():
    return JSONResponse({
        "message": "Bug Hunting Tracker",
        "status": "running",
        "cpu_usage": psutil.cpu_percent(),
        "ram_usage": psutil.virtual_memory().percent,
        "stop_scan": stop_scan
    })

@app.get("/stop")
def stop():
    global stop_scan
    stop_scan = True
    return JSONResponse({"message": "Bug hunting stopped!"})

@app.get("/start")
def start_scan(target_url: str):
    global stop_scan
    stop_scan = False
    thread = threading.Thread(target=run_scans, args=(target_url,))
    thread.start()
    return JSONResponse({"message": f"Bug hunting started on {target_url}!"})

# Function to check RAM/CPU usage and auto-stop if too high
def monitor_usage():
    while True:
        if psutil.virtual_memory().percent > 90 or psutil.disk_usage("/").percent > 95:
            global stop_scan
            stop_scan = True
            print("🚨 System resources too high! Stopping scans to prevent crash.")
        time.sleep(5)

# Start monitoring system usage in background
threading.Thread(target=monitor_usage, daemon=True).start()

if __name__ == "__main__":
    install_tools()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
