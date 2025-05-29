from webserver import start_webserver
from sensor import SensorReader

print("[INIT] Initializing sensor reader...")
sensor = SensorReader()
print("[OK] SensorReader instance created:", sensor)

print("[INIT] Launching web server...")
start_webserver(sensor)
