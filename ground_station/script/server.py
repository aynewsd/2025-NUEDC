import json
import socket
import threading

from Class import Data, point


class Server:
    def __init__(self, port, path_callback=None):
        self.port = port
        self.path_callback = path_callback
        self.server_sock = None
        self.client_sock = None
        self.client_addr = None
        self.running = False
        self.lock = threading.Lock()

    def start(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind(("0.0.0.0", self.port))
        self.server_sock.listen(1)
        self.running = True
        print(f"Server listening on port {self.port}")
        thread = threading.Thread(target=self._accept_loop, daemon=True)
        thread.start()

    def _accept_loop(self):
        while self.running:
            try:
                client, addr = self.server_sock.accept()
                with self.lock:
                    if self.client_sock:
                        self.client_sock.close()
                    self.client_sock = client
                    self.client_addr = addr
                print(f"Client connected from {addr}")
                threading.Thread(target=self._client_handler, args=(client,), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"Accept error: {e}")

    def _client_handler(self, sock):
        buffer = ""
        while self.running:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        self._handle_message(line)
            except Exception as e:
                print(f"Client handler error: {e}")
                break
        with self.lock:
            if self.client_sock == sock:
                self.client_sock = None
                self.client_addr = None
        sock.close()
        print("Client disconnected")

    def _handle_message(self, line):
        try:
            msg = json.loads(line)
            if msg.get("type") == "path":
                path_list = [point(item["x"], item["y"]) for item in msg["path"]]
                if self.path_callback:
                    self.path_callback(path_list)
        except Exception as e:
            print(f"Error handling message: {e}")

    def send_position(self, x, y):
        self._send({"type": "position", "x": x, "y": y})

    def send_cell(self, x, y, data):
        if isinstance(data, Data):
            data = [data.xiang, data.hu, data.lang, data.hou, data.que]
        self._send({"type": "cell", "x": x, "y": y, "data": data})

    def _send(self, msg_dict):
        with self.lock:
            if not self.client_sock:
                return
            try:
                msg = json.dumps(msg_dict) + "\n"
                self.client_sock.sendall(msg.encode("utf-8"))
            except Exception as e:
                print(f"Send error: {e}")
                self.client_sock.close()
                self.client_sock = None
                self.client_addr = None

    def stop(self):
        self.running = False
        if self.server_sock:
            self.server_sock.close()
            self.server_sock = None
        if self.client_sock:
            self.client_sock.close()
            self.client_sock = None
