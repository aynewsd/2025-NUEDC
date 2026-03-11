import socket
import json
import threading
from Class import point,Data
class Server:
    def __init__(self, port, path_callback=None):
        self.port = port
        self.path_callback = path_callback  # 当收到路径时调用 callback(path_list)
        self.server_sock = None
        self.client_sock = None
        self.client_addr = None
        self.running = False
        self.lock = threading.Lock()

    def start(self):
        """启动服务器，开始监听"""
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind(('0.0.0.0', self.port))
        self.server_sock.listen(1)
        self.running = True
        print(f"Server listening on port {self.port}")
        # 启动接受连接的线程
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
                # 启动接收该客户端消息的线程
                threading.Thread(target=self._client_handler, args=(client,), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"Accept error: {e}")

    def _client_handler(self, sock):
        """处理单个客户端消息"""
        buffer = ""
        while self.running:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    self._handle_message(line.strip())
            except Exception as e:
                print(f"Client handler error: {e}")
                break
        # 客户端断开
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
                path_list = msg["path"]
                # 转换为point对象列表（假设外部有point类）
                if self.path_callback:
                    # 注意：这里需要外部定义point类，或者传递字典
                    self.path_callback(path_list)
        except Exception as e:
            print(f"Error handling message: {e}")

    def send_position(self, x, y):
        """发送无人机位置"""
        self._send({"type": "position", "x": x, "y": y})

    def send_cell(self, x, y, data):
        """发送格子动物数据，data为[xiang, hu, lang, hou, que]"""
        self._send({"type": "cell", "x": x, "y": y, "data": data})

    def _send(self, msg_dict):
        with self.lock:
            if not self.client_sock:
                return
            try:
                msg = json.dumps(msg_dict) + "\n"
                self.client_sock.sendall(msg.encode('utf-8'))
            except Exception as e:
                print(f"Send error: {e}")
                self.client_sock.close()
                self.client_sock = None
                self.client_addr = None

    def stop(self):
        self.running = False
        if self.server_sock:
            self.server_sock.close()
        if self.client_sock:
            self.client_sock.close()