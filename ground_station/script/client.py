import json
import socket
import threading
import time

from Class import Data


class Client:
    def __init__(
        self,
        server_ip,
        server_port,
        shared_data,
        lock,
        callback=None,
        on_connect=None,
        connect_timeout=120,
        on_connect_timeout=None,
    ):
        self.server_ip = server_ip
        self.server_port = server_port
        self.shared_data = shared_data
        self.lock = lock
        self.callback = callback
        self.sock = None
        self.running = True
        self.connected = False
        self.reconnect_interval = 5
        self.recv_buffer = ""
        self.on_connect = on_connect
        self.connect_timeout = connect_timeout
        self.on_connect_timeout = on_connect_timeout
        self._connect_started_at = None
        self._stop_requested = False

    def connect(self):
        while self.running:
            try:
                if self._connect_started_at is None:
                    self._connect_started_at = time.time()
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.server_ip, self.server_port))
                self.connected = True
                self.recv_buffer = ""
                self._connect_started_at = None
                print(f"Connected to server {self.server_ip}:{self.server_port}")
                if self.on_connect:
                    try:
                        self.on_connect()
                    except Exception as e:
                        print(f"on_connect callback error: {e}")
                return True
            except Exception as e:
                if self.sock:
                    self.sock.close()
                    self.sock = None
                print(f"Connection failed: {e}, retry in {self.reconnect_interval}s")
                if (
                    self.connect_timeout is not None
                    and self._connect_started_at is not None
                    and time.time() - self._connect_started_at >= self.connect_timeout
                ):
                    self.running = False
                    self.connected = False
                    if not self._stop_requested and self.on_connect_timeout:
                        try:
                            self.on_connect_timeout()
                        except Exception as callback_error:
                            print(f"on_connect_timeout callback error: {callback_error}")
                    return False
                time.sleep(self.reconnect_interval)
        return False

    def send_path(self, path_points):
        if not self.connected or not self.sock:
            print("Not connected, cannot send path")
            return
        path_list = [{"x": p.x, "y": p.y} for p in path_points]
        msg = json.dumps({"type": "path", "path": path_list}) + "\n"
        try:
            self.sock.sendall(msg.encode("utf-8"))
        except Exception as e:
            print(f"Send path failed: {e}")
            self.connected = False
            if self.sock:
                self.sock.close()
                self.sock = None

    def _receive_loop(self):
        while self.running:
            if not self.connected:
                if not self.connect():
                    continue
            try:
                data = self.sock.recv(4096)
                if not data:
                    self.connected = False
                    if self.sock:
                        self.sock.close()
                        self.sock = None
                    self.recv_buffer = ""
                    self._connect_started_at = time.time()
                    continue
                self.recv_buffer += data.decode("utf-8")
                while "\n" in self.recv_buffer:
                    line, self.recv_buffer = self.recv_buffer.split("\n", 1)
                    if line.strip():
                        self._handle_message(line)
            except Exception as e:
                print(f"Receive error: {e}")
                self.connected = False
                if self.sock:
                    self.sock.close()
                    self.sock = None
                self.recv_buffer = ""
                self._connect_started_at = time.time()
                time.sleep(1)

    def _handle_message(self, line):
        try:
            msg = json.loads(line)
            msg_type = msg.get("type")
            with self.lock:
                if msg_type == "position":
                    self.shared_data["position"] = (8-2*msg["x"],6-2*msg["y"])
                elif msg_type == "cell":
                    x, y = 8-int(round(msg["x"]*2)), 6-int(round(msg["y"]))
                    data = msg["data"]
                    if 0 <= x < 9 and 0 <= y < 7:
                        self.shared_data["animal"][x][y] = Data(*data)
                        total = Data(0, 0, 0, 0, 0)
                        for i in range(9):
                            for j in range(7):
                                d = self.shared_data["animal"][i][j]
                                total.xiang += d.xiang
                                total.hu += d.hu
                                total.lang += d.lang
                                total.hou += d.hou
                                total.que += d.que
                        self.shared_data["total_animal"] = total
            if self.callback:
                self.callback(msg)
        except Exception as e:
            print(f"Error handling message: {e}")

    def start(self):
        thread = threading.Thread(target=self._receive_loop, daemon=True)
        thread.start()

    def stop(self):
        self._stop_requested = True
        self.running = False
        self.connected = False
        self._connect_started_at = None
        if self.sock:
            self.sock.close()
            self.sock = None
