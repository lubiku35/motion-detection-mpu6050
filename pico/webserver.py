import network
import socket
import time
import ujson

def setup_access_point(ssid='PicoNetwork', password='12345678'):
    print("[WIFI] Disabling STA mode...")
    sta = network.WLAN(network.STA_IF)
    sta.active(False)

    print("[WIFI] Setting up Access Point...")
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid, password=password)
    ap.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '8.8.8.8'))

    print("[WIFI] Waiting for AP to become active...")
    for _ in range(10):
        if ap.active():
            print("[WIFI] Access Point is active.")
            print("[WIFI] IP Address:", ap.ifconfig()[0])
            return ap
        time.sleep(0.5)

    raise RuntimeError("[ERROR] Failed to activate Access Point.")

# --- Serve Static Files ---
def serve_file(conn, path, content_type):
    print(f"[HTTP] Serving file: {path}")
    try:
        with open(path, "r") as f:
            conn.send("HTTP/1.1 200 OK\r\nContent-Type: {}\r\n\r\n".format(content_type))
            while True:
                chunk = f.read(512)
                if not chunk:
                    break
                conn.sendall(chunk)
    except Exception as e:
        print(f"[ERROR] File serve failed: {e}")
        conn.send("HTTP/1.1 500 Internal Server Error\r\n\r\n")

# --- Handle JSON Response ---
def json_response(data):
    try:
        return ujson.dumps(data)
    except Exception as e:
        print(f"[ERROR] Failed to serialize JSON: {e}")
        return '{"error": "serialization error"}'

# --- Main Webserver Function ---
def start_webserver(sensor):
    ap = setup_access_point()
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind(addr)
        server.listen(1)
        print("[SERVER] Listening on port 80...")
    except Exception as e:
        print(f"[ERROR] Failed to bind socket: {e}")
        server.close()
        return

    while True:
        print("[WAIT] Awaiting client connection...")
        try:
            conn, addr = server.accept()
            print(f"[CONNECT] Client: {addr}")
            request = conn.recv(1024).decode()
            print("[REQUEST]", request.split('\n')[0])
            
            if "GET /data" in request:
                print("[ROUTE] Serving /data")
                data = sensor.read()  # includes accel, gyro, motion, summary
                response = json_response(data)
                conn.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n" + response)
            
            elif "GET /logs" in request:
                print("[ROUTE] Serving /logs")
                serve_file(conn, "logs.json", "application/json")
                
            elif "GET /chart.js" in request:
                serve_file(conn, "/static/chart.js", "application/javascript")

            elif "GET /client-behavior.js" in request:
                serve_file(conn, "/client-behavior.js", "application/javascript")
            
            elif "GET /" in request:
                serve_file(conn, "/html/index.html", "text/html")

            else:
                conn.send("HTTP/1.1 404 Not Found\r\n\r\n")
                print("[WARN] Unknown route")

        except Exception as e:
            print("[ERROR] During request:", e)

        finally:
            try:
                conn.close()
                print("[INFO] Connection closed\n")
            except:
                pass