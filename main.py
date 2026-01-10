# backend.py
from flask import Flask, request, jsonify, send_from_directory
import hashlib
import subprocess
import os
import sys
import webbrowser
import time
from flask import Flask, request, jsonify, send_from_directory
import hashlib, subprocess, os
import filetype
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

app = Flask(__name__, static_folder="frontend", static_url_path="")

# -----------------------------
# Serve Frontend HTML
# -----------------------------
@app.route("/")
def index():
    app.static_folder="./"
    return send_from_directory(app.static_folder, "index.html")


# -------------------- HASH / DEHASH --------------------
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

    # Optional: detect file type
    kind = filetype.guess(content)
    kind_name = kind.mime if kind else "unknown"

    return jsonify({"hashes": hashes, "file_type": kind_name})

# -------------------- WHOIS --------------------
@app.route("/whois", methods=["POST"])
def whois_lookup():
    domain = request.json.get("domain")
    if not domain:
        return jsonify({"error": "No domain provided"}), 400
    try:
        result = subprocess.run(["whois", domain], capture_output=True, text=True, timeout=5)
        return jsonify({"output": result.stdout})
    except Exception as e:
        return jsonify({"error": str(e)})

# -------------------- DIG --------------------
@app.route("/dig", methods=["POST"])
def dig_lookup():
    domain = request.json.get("domain")
    record = request.json.get("record", "A")  # default to A record
    try:
        result = subprocess.run(["dig", "+short", record, domain], capture_output=True, text=True, timeout=5)
        return jsonify({"output": result.stdout})
    except Exception as e:
        return jsonify({"error": str(e)})

# -------------------- METADATA --------------------
@app.route("/metadata", methods=["POST"])
def metadata_extraction():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        img = Image.open(file)
        exif_data = {}
        if hasattr(img, "_getexif") and img._getexif() is not None:
            for tag, value in img._getexif().items():
                decoded = TAGS.get(tag, tag)
                exif_data[decoded] = value
        return jsonify({"metadata": exif_data})
    except Exception as e:
        return jsonify({"error": str(e)})

# -----------------------------
# Launch Chromium in App Mode
# -----------------------------
def open_chromium_app(url="http://127.0.0.1:5000"):
    """
    Opens Chromium in app mode (frameless, no tabs/address bar)
    """
    # Try to find chromium-browser or chromium
    browsers = ["chromium", "chromium-browser", "google-chrome", "chrome"]
    for b in browsers:
        try:
            webbrowser.get(f"{b} %s").open(url)
            return
        except webbrowser.Error:
            continue
    print(f"Could not automatically find Chromium. Open {url} manually.")

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    # Launch server in a separate thread to avoid blocking
    from threading import Thread
    def run_flask():
        app.run(debug=False, use_reloader=False)  # disable reloader

    t = Thread(target=run_flask)
    t.start()

    # Give Flask a moment to start
    time.sleep(1)

    # Open Chromium in app mode
    import subprocess
    try:
        subprocess.run([
            "chromium",  # or chromium-browser / google-chrome
            "--app=http://127.0.0.1:5000",
            "--window-size=1200,800"
        ])
    except FileNotFoundError:
        print("Chromium not found. Open http://127.0.0.1:5000 manually.")
