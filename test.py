import subprocess
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
print(ping.returncode)