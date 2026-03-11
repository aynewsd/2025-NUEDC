import socket
import json
import threading
import time
from Class import Data
class Client:
    def __init__(self, server_ip, server_port, shared_data, lock, callback=None):
        """
        shared_data: dict 包含 'position', 'animal', 'total_animal'
        lock: threading.Lock 用于保护共享数据
        callback: 可选，当收到消息时调用（用于调试）
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.shared_data = shared_data
        self.lock = lock
        self.callback = callback
        self.sock:socket.socket
        self.running = True
        self.connected = False
        self.reconnect_interval = 5  # 秒

    def connect(self):
        """尝试连接服务器，成功返回True"""
        while self.running:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.server_ip, self.server_port))
                self.connected = True
                print(f"Connected to server {self.server_ip}:{self.server_port}")
                return True
            except Exception as e:
                print(f"Connection failed: {e}, retry in {self.reconnect_interval}s")
                time.sleep(self.reconnect_interval)
        return False

    def send_path(self, path_points):
        """发送路径点列表（point对象列表）"""
        if not self.connected:
            print("Not connected, cannot send path")
            return
        path_list = [{"x": p.x, "y": p.y} for p in path_points]
        msg = json.dumps({"type": "path", "path": path_list}) + "\n"
        try:
            self.sock.sendall(msg.encode('utf-8'))
        except Exception as e:
            print(f"Send path failed: {e}")
            self.connected = False

    def _receive_loop(self):
        """接收线程主循环"""
        while self.running:
            if not self.connected:
                if not self.connect():
                    continue
            try:
                data = self.sock.recv(4096)
                if not data:
                    # 连接关闭
                    self.connected = False
                    self.sock.close()
                    continue
                # 按行分割（每条JSON以换行结尾）
                lines = data.decode('utf-8').split('\n')
                for line in lines:
                    if line.strip() == "":
                        continue
                    self._handle_message(line)
            except Exception as e:
                print(f"Receive error: {e}")
                self.connected = False
                self.sock.close()
                time.sleep(1)

    def _handle_message(self, line):
        """处理单条JSON消息"""
        try:
            msg = json.loads(line)
            msg_type = msg.get("type")
            with self.lock:
                if msg_type == "position":
                    self.shared_data["position"] = (msg["x"], msg["y"])
                elif msg_type == "cell":
                    x, y = msg["x"], msg["y"]
                    data = msg["data"]  # [xiang, hu, lang, hou, que]
                    # 确保animal数组存在
                    if 0 <= x < 9 and 0 <= y < 7:
                        # 更新对应格子的Data对象
                        self.shared_data["animal"][x][y] = Data(*data)
                        # 重新计算总数（可选，也可以在绘制时计算）
                        total = Data(0,0,0,0,0)
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
        """启动接收线程"""
        thread = threading.Thread(target=self._receive_loop, daemon=True)
        thread.start()

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()