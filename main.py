# backend.py
from flask import Flask, request, jsonify, send_from_directory
import hashlib
import subprocess
import os
import sys
import webbrowser
import time
from pathlib import Path
from threading import Thread
import psutil
import shutil
import filetype
from PIL import Image
from PIL.ExifTags import TAGS

# -------------------------------------------------
# PyInstaller-safe resource helpers
# -------------------------------------------------
def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    return base / relative_path

def get_bin(name):
    """Return bundled binary path if frozen, else system binary"""
    if getattr(sys, 'frozen', False):
        return str(resource_path(f"bin/{name}"))
    return shutil.which(name) or name

# -------------------------------------------------
# Flask App Setup
# -------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path=""
)

# -------------------------------------------------
# Serve Frontend
# -------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

# -------------------------------------------------
# Status
# -------------------------------------------------
@app.route("/status", methods=["GET"])
def status():
    try:
        ip_result = subprocess.run(
            ["hostname", "-I"],
            capture_output=True,
            text=True,
            timeout=5
        )
        ip_address = ip_result.stdout.strip().split()[0]
    except Exception:
        ip_address = "Unavailable"

    version = "UHC OSINT v1.0"

    try:
        ping = subprocess.run(
            ["ping", "-c", "1", "8.8.8.8"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if ping.returncode == 0:
            internet_connection = "Connected"
        else:
            internet_connection = "Disconnected"
    except Exception:
        internet_connection = "Disconnected"
    print(internet_connection)
    return jsonify({
        "ip": ip_address,
        "version": version,
        "internet_connection": internet_connection
    })
    
# -------------------------------------------------
# NMAP
# -------------------------------------------------
@app.route("/nmap", methods=["POST"])
def network_map():
    args = request.json.get("args")
    target = request.json.get("range")
    try:
        result = subprocess.run(
            [get_bin("nmap"), args, target],
            capture_output=True,
            text=True,
            timeout=15
        )
        return jsonify({"output": result.stdout})
    except Exception as e:
        return jsonify({"error": str(e)})

# -------------------------------------------------
# Hash / Dehash
# -------------------------------------------------
@app.route("/hash", methods=["POST"])
def compute_hash():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    content = file.read()
    hashes = {
        "md5": hashlib.md5(content).hexdigest(),
        "sha1": hashlib.sha1(content).hexdigest(),
        "sha256": hashlib.sha256(content).hexdigest()
    }

    kind = filetype.guess(content)
    kind_name = kind.mime if kind else "unknown"

    return jsonify({"hashes": hashes, "file_type": kind_name})

# -------------------------------------------------
# WHOIS
# -------------------------------------------------
@app.route("/whois", methods=["POST"])
def whois_lookup():
    domain = request.json.get("domain")
    if not domain:
        return jsonify({"error": "No domain provided"}), 400
    try:
        result = subprocess.run(
            [get_bin("whois"), domain],
            capture_output=True,
            text=True,
            timeout=5
        )
        return jsonify({"output": result.stdout})
    except Exception as e:
        return jsonify({"error": str(e)})

# -------------------------------------------------
# DIG
# -------------------------------------------------
@app.route("/dig", methods=["POST"])
def dig_lookup():
    domain = request.json.get("domain")
    record = request.json.get("record", "A")
    try:
        result = subprocess.run(
            [get_bin("dig"), "+short", record, domain],
            capture_output=True,
            text=True,
            timeout=5
        )
        return jsonify({"output": result.stdout})
    except Exception as e:
        return jsonify({"error": str(e)})

# -------------------------------------------------
# Metadata
# -------------------------------------------------
@app.route("/metadata", methods=["POST"])
def metadata_extraction():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        img = Image.open(file)
        exif_data = {}
        if hasattr(img, "_getexif") and img._getexif():
            for tag, value in img._getexif().items():
                decoded = TAGS.get(tag, tag)
                exif_data[decoded] = value
        return jsonify({"metadata": exif_data})
    except Exception as e:
        return jsonify({"error": str(e)})

# -------------------------------------------------
# Chromium Launcher
# -------------------------------------------------
def launch_chromium():
    chromium = (
        shutil.which("chromium")
        or shutil.which("chromium-browser")
        or shutil.which("google-chrome")
        or shutil.which("chrome")
    )

    if not chromium:
        print("Chromium not found. Open http://127.0.0.1:5000 manually.")
        return None

    return subprocess.Popen([
        chromium,
        "--app=http://127.0.0.1:5000",
        "--window-size=1200,800",
        "--user-data-dir=/tmp/temp_chromium_profile"
    ])

# -------------------------------------------------
# Flask Runner
# -------------------------------------------------
def run_flask():
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

def is_process_alive(proc):
    if proc is None:
        return False
    if proc.poll() is None:
        return True
    try:
        p = psutil.Process(proc.pid)
        return any(c.is_running() for c in p.children(recursive=True))
    except psutil.NoSuchProcess:
        return False

# -------------------------------------------------
# Main
# -------------------------------------------------
if __name__ == "__main__":
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(1)

    chromium_proc = launch_chromium()

    try:
        ttyd_proc = subprocess.Popen([
            get_bin("ttyd"),
            "--interface", "127.0.0.1",
            "-p", "27681",
            "-t", 'theme={"background":"black","foreground":"white"}',
            "--writable", "bash"
        ])
    except Exception:
        ttyd_proc = None

    while True:
        time.sleep(5)
        if chromium_proc and not is_process_alive(chromium_proc):
            if ttyd_proc:
                ttyd_proc.terminate()
            os._exit(0)
